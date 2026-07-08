#!/usr/bin/env python3
"""Static audit for paper-to-learning-site outputs."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


class SiteHTMLParser(HTMLParser):
    VOID_TAGS = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
    TEXT_FLOW_CLASSES = {
        "source-text",
        "translation-text",
        "plain-text",
        "source-paragraph",
    }
    DETACHED_TERM_CLASSES = {
        "term-strip",
        "terms-strip",
        "term-list",
        "related-terms",
        "glossary-strip",
        "glossary",
    }
    TEXT_COLLECT_CLASSES = {
        "source-text",
        "translation-text",
        "plain-text",
        "figure-note",
        "figure-explanation",
        "figure-reader",
        "source-figure-note",
        "marginalia",
        "side-note",
    }

    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.images: list[tuple[str, str, int]] = []
        self.iframes: list[tuple[str, int]] = []
        self.buttons: list[tuple[dict[str, str], int]] = []
        self.starttags: list[tuple[str, dict[str, str], int]] = []
        self.class_counts: dict[str, int] = {}
        self.visible_text_parts: list[str] = []
        self.attr_texts: list[tuple[str, str, int]] = []
        self.class_texts: dict[str, list[str]] = {}
        self.term_records: list[dict[str, object]] = []
        self.reading_blocks: list[dict[str, str | int]] = []
        self.aria_counts = {"expanded": 0, "controls": 0, "current": 0}
        self._current_button: dict[str, str] | None = None
        self._button_text: list[str] = []
        self._class_stack: list[set[str]] = []
        self._text_collectors: list[dict[str, object]] = []
        self._skip_depth = 0
        self._line = 1

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag_name = tag.lower()
        is_void = tag_name in self.VOID_TAGS
        if not is_void:
            for collector in self._text_collectors:
                collector["depth"] = int(collector["depth"]) + 1
        attr = {k: (v or "") for k, v in attrs}
        self._line = self.getpos()[0]
        self.starttags.append((tag, attr, self._line))
        classes = set(attr.get("class", "").split())
        ancestor_classes = set().union(*self._class_stack) if self._class_stack else set()
        all_context_classes = ancestor_classes | classes
        for class_name in attr.get("class", "").split():
            self.class_counts[class_name] = self.class_counts.get(class_name, 0) + 1
        for aria_name in ("aria-expanded", "aria-controls", "aria-current"):
            if aria_name in attr:
                self.aria_counts[aria_name.removeprefix("aria-")] += 1
        for attr_name in ("alt", "title", "aria-label"):
            if attr.get(attr_name, "").strip():
                self.attr_texts.append((attr_name, attr[attr_name].strip(), self._line))
        if "id" in attr:
            self.ids.append(attr["id"])
        if tag == "img":
            self.images.append((attr.get("src", ""), attr.get("alt", ""), self._line))
        if tag == "iframe":
            self.iframes.append((attr.get("src", ""), self._line))
        if "reading-block" in classes:
            self.reading_blocks.append(
                {
                    "line": self._line,
                    "id": attr.get("id", ""),
                    "data_source_id": attr.get("data-source-id", ""),
                    "data_block": attr.get("data-block", ""),
                }
            )
        is_term = (
            "term" in classes
            or "data-term" in attr
            or "data-term-id" in attr
            or attr.get("data-open-drawer", "").lower() == "term"
        )
        if is_term:
            self.term_records.append(
                {
                    "line": self._line,
                    "classes": sorted(classes),
                    "inline": bool(all_context_classes & self.TEXT_FLOW_CLASSES) and not bool(all_context_classes & self.DETACHED_TERM_CLASSES),
                    "detached": bool(all_context_classes & self.DETACHED_TERM_CLASSES),
                    "has_aria": any(name in attr for name in ("aria-expanded", "aria-controls", "aria-label")),
                }
            )
        for class_name in classes & self.TEXT_COLLECT_CLASSES:
            if is_void:
                continue
            self._text_collectors.append({"class": class_name, "depth": 1, "parts": []})
        if tag_name in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
        if tag == "button":
            self._current_button = attr
            self._button_text = []
        if not is_void:
            self._class_stack.append(classes)

    def handle_endtag(self, tag: str) -> None:
        if tag == "button" and self._current_button is not None:
            attrs = dict(self._current_button)
            attrs["_text"] = " ".join("".join(self._button_text).split())
            self.buttons.append((attrs, self.getpos()[0]))
            self._current_button = None
            self._button_text = []
        finished: list[dict[str, object]] = []
        for collector in self._text_collectors:
            collector["depth"] = int(collector["depth"]) - 1
            if int(collector["depth"]) <= 0:
                finished.append(collector)
        if finished:
            for collector in finished:
                class_name = str(collector["class"])
                value = " ".join("".join(collector["parts"]).split())
                if value:
                    self.class_texts.setdefault(class_name, []).append(value)
                self._text_collectors.remove(collector)
        if tag.lower() in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        if self._class_stack:
            self._class_stack.pop()

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            if data.strip():
                self.visible_text_parts.append(data)
            for collector in self._text_collectors:
                cast_parts = collector["parts"]
                if isinstance(cast_parts, list):
                    cast_parts.append(data)
        if self._current_button is not None:
            self._button_text.append(data)

    @property
    def visible_text(self) -> str:
        return " ".join(" ".join(self.visible_text_parts).split())


def is_external_or_embedded(src: str) -> bool:
    if not src:
        return False
    if src.startswith(("data:", "blob:", "#")):
        return True
    parsed = urlparse(src)
    return bool(parsed.scheme and parsed.scheme not in {"file"})


def find_html_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    return sorted(target.rglob("*.html"))


def load_manifest(root: Path) -> dict[str, object] | None:
    candidates = [
        root / "data" / "learning-site-manifest.json",
        root / "learning-site-manifest.json",
        root / "data" / "manifest.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
            except Exception as exc:
                return {"_manifest_error": f"{candidate}: {exc}"}
            data["_manifest_path"] = str(candidate)
            return data
    return None


def chrome_path() -> str | None:
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    return shutil.which("google-chrome") or shutil.which("google-chrome-stable") or shutil.which("chromium") or shutil.which("chromium-browser")


def run_mobile_render_check(path: Path, root: Path) -> tuple[list[str], list[str]]:
    chrome = chrome_path()
    if not chrome:
        return [], [f"{path}: Chrome/Chromium not found; mobile render overflow check skipped"]

    source = path.read_text(encoding="utf-8", errors="replace")
    base_href = root.resolve().as_uri().rstrip("/") + "/"
    probe = r"""
<script>
setTimeout(() => {
  const selectors = [
    'body',
    'header',
    '.shell',
    '.reader-card',
    '.chapter-map',
    '.marginalia',
    '.figure-row',
    '.figure-row img',
    '.figure-note',
    '.figure-note p',
    '.figure-note h3',
    '.reading-block',
    '.source-text',
    '.translation-text',
    '.plain-text',
    '.map-item',
    '.hero p',
    '.marginalia p',
    'p',
    'button'
  ];
  const offenders = [];
  for (const el of document.querySelectorAll(selectors.join(','))) {
    const rect = el.getBoundingClientRect();
    const isRootBox = el === document.body || el === document.documentElement;
    if (
      rect.width > 0 &&
      (
        rect.right > window.innerWidth + 2 ||
        rect.left < -2 ||
        (!isRootBox && el.scrollWidth > el.clientWidth + 2)
      )
    ) {
      offenders.push({
        tag: el.tagName.toLowerCase(),
        className: el.className || '',
        left: Math.round(rect.left),
        right: Math.round(rect.right),
        width: Math.round(rect.width),
        clientWidth: Math.round(el.clientWidth || 0),
        scrollWidth: Math.round(el.scrollWidth || 0),
        text: (el.innerText || el.alt || '').replace(/\s+/g, ' ').slice(0, 80)
      });
    }
  }
  const metrics = {
    innerWidth: window.innerWidth,
    documentScrollWidth: document.documentElement.scrollWidth,
    bodyScrollWidth: document.body.scrollWidth,
    offenders: offenders.slice(0, 12)
  };
  const pre = document.createElement('pre');
  pre.id = 'paper-site-audit-metrics';
  pre.textContent = JSON.stringify(metrics);
  document.body.appendChild(pre);
}, 150);
</script>
"""
    if "<head" in source.lower():
        source = re.sub(r"(<head[^>]*>)", lambda match: f'{match.group(1)}<base href="{base_href}">', source, count=1, flags=re.I)
    else:
        source = f'<base href="{base_href}">' + source
    if "</body>" in source.lower():
        source = re.sub(r"</body>", lambda _match: probe + "</body>", source, count=1, flags=re.I)
    else:
        source += probe

    with tempfile.TemporaryDirectory() as tmp:
        probe_path = Path(tmp) / path.name
        probe_path.write_text(source, encoding="utf-8")
        try:
            result = subprocess.run(
                [
                    chrome,
                    "--headless=new",
                    "--disable-gpu",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--window-size=390,1200",
                    "--virtual-time-budget=1000",
                    "--dump-dom",
                    probe_path.as_uri(),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=20,
            )
        except subprocess.TimeoutExpired:
            return [], [f"{path}: mobile render overflow check timed out"]
    if result.returncode != 0:
        return [], [f"{path}: mobile render overflow check failed to run: {result.stderr.strip()[:240]}"]

    match = re.search(r'<pre id="paper-site-audit-metrics">([\s\S]*?)</pre>', result.stdout)
    if not match:
        return [], [f"{path}: mobile render overflow metrics were not produced"]
    try:
        metrics = json.loads(html.unescape(match.group(1)))
    except Exception as exc:
        return [], [f"{path}: mobile render overflow metrics could not be parsed: {exc}"]

    errors: list[str] = []
    warnings: list[str] = []
    inner_width = int(metrics.get("innerWidth") or 390)
    scroll_width = max(int(metrics.get("documentScrollWidth") or 0), int(metrics.get("bodyScrollWidth") or 0))
    if scroll_width > inner_width + 2:
        errors.append(f"{path}: mobile layout has horizontal overflow ({scroll_width}px content in {inner_width}px viewport)")
    offenders = metrics.get("offenders") or []
    if offenders:
        preview = "; ".join(
            f"{item.get('tag')}.{str(item.get('className', '')).split()[0] if item.get('className') else ''} right={item.get('right')}"
            for item in offenders[:4]
        )
        errors.append(f"{path}: mobile elements extend outside viewport: {preview}")
    return errors, warnings


def run_desktop_first_viewport_check(path: Path, root: Path) -> tuple[list[str], list[str]]:
    chrome = chrome_path()
    if not chrome:
        return [], [f"{path}: Chrome/Chromium not found; desktop first-viewport reader check skipped"]

    source = path.read_text(encoding="utf-8", errors="replace")
    base_href = root.resolve().as_uri().rstrip("/") + "/"
    probe = r"""
<script>
setTimeout(() => {
  const groups = {
    title: 'h1,[data-paper-title],.paper-title',
    chapterNav: '.chapter-map,.chapter-tab,.map-item,.chapter-button,[role="tablist"]',
    languageMode: '.language-mode,.language-toggle,.lang-toggle,.mode-toggle,.segmented-language,[data-language-mode]',
    sourceText: '.source-text,.source-paragraph,[data-source-id]',
    chineseReading: '.translation-text,.plain-text,.chinese-reading,.cn-reading',
    learningAffordance: '.term,[data-term],[data-term-id],.figure-note,.figure-explanation,.source-figure-note,.marginalia,.side-note,[data-open-drawer],.term-popover'
  };
  const visible = {};
  for (const [key, selector] of Object.entries(groups)) {
    visible[key] = Array.from(document.querySelectorAll(selector)).some((el) => {
      const rect = el.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0 && rect.top < window.innerHeight && rect.bottom > 0 && rect.left < window.innerWidth && rect.right > 0;
    });
  }
  const offenders = [];
  for (const el of document.querySelectorAll('body,header,.shell,.reader-card,.chapter-map,.reading-block,.source-text,.translation-text,.plain-text,p,button')) {
    const rect = el.getBoundingClientRect();
    const isRootBox = el === document.body || el === document.documentElement;
    if (rect.width > 0 && (rect.right > window.innerWidth + 2 || rect.left < -2 || (!isRootBox && el.scrollWidth > el.clientWidth + 2))) {
      offenders.push({
        tag: el.tagName.toLowerCase(),
        className: el.className || '',
        right: Math.round(rect.right),
        clientWidth: Math.round(el.clientWidth || 0),
        scrollWidth: Math.round(el.scrollWidth || 0),
        text: (el.innerText || '').replace(/\s+/g, ' ').slice(0, 80)
      });
    }
  }
  const metrics = {
    innerWidth: window.innerWidth,
    documentScrollWidth: document.documentElement.scrollWidth,
    bodyScrollWidth: document.body.scrollWidth,
    visible,
    offenders: offenders.slice(0, 12)
  };
  const pre = document.createElement('pre');
  pre.id = 'paper-site-audit-desktop-metrics';
  pre.textContent = JSON.stringify(metrics);
  document.body.appendChild(pre);
}, 150);
</script>
"""
    if "<head" in source.lower():
        source = re.sub(r"(<head[^>]*>)", lambda match: f'{match.group(1)}<base href="{base_href}">', source, count=1, flags=re.I)
    else:
        source = f'<base href="{base_href}">' + source
    if "</body>" in source.lower():
        source = re.sub(r"</body>", lambda _match: probe + "</body>", source, count=1, flags=re.I)
    else:
        source += probe

    with tempfile.TemporaryDirectory() as tmp:
        probe_path = Path(tmp) / path.name
        probe_path.write_text(source, encoding="utf-8")
        try:
            result = subprocess.run(
                [
                    chrome,
                    "--headless=new",
                    "--disable-gpu",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--window-size=1440,950",
                    "--virtual-time-budget=1000",
                    "--dump-dom",
                    probe_path.as_uri(),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=20,
            )
        except subprocess.TimeoutExpired:
            return [], [f"{path}: desktop first-viewport check timed out"]
    if result.returncode != 0:
        return [], [f"{path}: desktop first-viewport check failed to run: {result.stderr.strip()[:240]}"]

    match = re.search(r'<pre id="paper-site-audit-desktop-metrics">([\s\S]*?)</pre>', result.stdout)
    if not match:
        return [], [f"{path}: desktop first-viewport metrics were not produced"]
    try:
        metrics = json.loads(html.unescape(match.group(1)))
    except Exception as exc:
        return [], [f"{path}: desktop first-viewport metrics could not be parsed: {exc}"]

    errors: list[str] = []
    warnings: list[str] = []
    inner_width = int(metrics.get("innerWidth") or 1440)
    scroll_width = max(int(metrics.get("documentScrollWidth") or 0), int(metrics.get("bodyScrollWidth") or 0))
    if scroll_width > inner_width + 2:
        errors.append(f"{path}: desktop layout has horizontal overflow ({scroll_width}px content in {inner_width}px viewport)")
    visible = metrics.get("visible") or {}
    required = {
        "title": "paper title",
        "chapterNav": "chapter navigation",
        "sourceText": "real source paragraph",
        "chineseReading": "Chinese translation/explanation",
        "learningAffordance": "inline term, evidence, side note, or learning affordance",
    }
    for key, label in required.items():
        if not visible.get(key):
            errors.append(f"{path}: desktop first viewport does not show {label}; avoid cover pages that hide the paper reader")
    if not visible.get("languageMode"):
        warnings.append(f"{path}: desktop first viewport does not show a language mode control")
    offenders = metrics.get("offenders") or []
    if offenders:
        preview = "; ".join(
            f"{item.get('tag')}.{str(item.get('className', '')).split()[0] if item.get('className') else ''} right={item.get('right')}"
            for item in offenders[:4]
        )
        errors.append(f"{path}: desktop elements extend outside viewport: {preview}")
    return errors, warnings


PRODUCTION_TEXT_PATTERNS = [
    (r"面向无专业背景大学生", "audience-targeting note"),
    (r"生成教学图资产", "generated asset label"),
    (r"生成教学图用于", "generated asset purpose note"),
    (r"这张生成", "generated-image production phrasing"),
    (r"Generated explainer", "generated explainer label"),
    (r"\bGenerated\b", "generated production label"),
    (r"generated assets?", "generated asset label"),
    (r"\bprompt\b", "prompt/internal generation label"),
    (r"\bmanifest\b", "manifest/internal file label"),
    (r"\bpreflight\b", "preflight/internal workflow label"),
    (r"\bregression(?: slice)?\b", "regression/internal test label"),
    (r"\breader level\b", "reader-level internal label"),
    (r"\bprompt_summary\b", "prompt summary label"),
]


def compact_text(value: str) -> str:
    return " ".join(value.split())


def explanation_length(value: str) -> int:
    return len(re.sub(r"\s+", "", value))


def source_word_count(value: str) -> int:
    return len(re.findall(r"[A-Za-z][A-Za-z0-9_-]*|[\u4e00-\u9fff]", value))


def cue_missing(text: str, cue_groups: dict[str, list[str]]) -> list[str]:
    missing: list[str] = []
    for cue_name, variants in cue_groups.items():
        if not any(variant.lower() in text.lower() for variant in variants):
            missing.append(cue_name)
    return missing


def audit_html(
    path: Path,
    root: Path,
    strict: bool,
    manifest: dict[str, object] | None,
    expected_source_blocks: int | None = None,
) -> tuple[list[str], list[str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    parser = SiteHTMLParser()
    parser.feed(text)

    errors: list[str] = []
    warnings: list[str] = []

    seen: set[str] = set()
    duplicates: set[str] = set()
    for item in parser.ids:
        if item in seen:
            duplicates.add(item)
        seen.add(item)
    for item in sorted(duplicates):
        errors.append(f"{path}: duplicate id '{item}'")

    source_count = parser.class_counts.get("source-label", 0)
    translation_count = parser.class_counts.get("translation-label", 0)
    plain_count = parser.class_counts.get("plain-label", 0)
    term_count = max(parser.class_counts.get("term", 0), len(parser.term_records))
    inline_term_count = sum(1 for item in parser.term_records if item.get("inline"))
    detached_term_count = sum(1 for item in parser.term_records if item.get("detached"))
    visible_text = parser.visible_text
    public_attr_text = " ".join(value for _name, value, _line in parser.attr_texts)
    public_text_for_scan = f"{visible_text} {public_attr_text}"
    source_texts = parser.class_texts.get("source-text", [])
    translation_texts = parser.class_texts.get("translation-text", [])
    plain_texts = parser.class_texts.get("plain-text", [])
    source_count = max(source_count, len(source_texts))
    translation_count = max(translation_count, len(translation_texts))
    plain_count = max(plain_count, len(plain_texts))
    figure_note_texts = []
    for class_name in ("figure-note", "figure-explanation", "figure-reader", "source-figure-note"):
        figure_note_texts.extend(parser.class_texts.get(class_name, []))
    marginalia_text = " ".join(parser.class_texts.get("marginalia", []) + parser.class_texts.get("side-note", []))
    script_count = len(re.findall(r"<script\b", text, re.I))
    language_mode = bool(
        re.search(r"中英|EN only|English only|仅英文|只英文|中文模式", text, re.I)
        or any(name in parser.class_counts for name in ("language-mode", "language-toggle", "lang-toggle", "mode-toggle", "segmented-language"))
    )
    has_interaction_logic = bool(
        script_count
        and re.search(r"addEventListener|onclick|classList|aria-expanded|aria-pressed|data-mode|data-term|showModal|popover|dialog|drawer", text, re.I)
    )
    has_close_affordance = bool(
        re.search(r"aria-label=[\"'][^\"']*(关闭|close)|data-close|drawer-close|modal-close|popover-close|class=[\"'][^\"']*close|>×<|>关闭<|>Close<", text, re.I)
    )
    has_popover_or_drawer = bool(
        re.search(r"popover|drawer|dialog|modal|bottom-sheet|side-panel|术语弹窗|图表抽屉", text, re.I)
        or any(name in parser.class_counts for name in ("popover", "drawer", "dialog", "modal", "bottom-sheet", "side-panel", "term-popover", "figure-drawer"))
    )
    full_source_pre = bool(re.search(r"""<details[^>]+class=["'][^"']*full-source[^"']*["'][\s\S]*?<pre""", text, re.I))
    any_large_pre = bool(re.search(r"<pre[\s\S]{2000,}</pre>", text, re.I))
    diagram_svgs = [src for src, _alt, _line in parser.images if re.search(r"assets/diagrams/.*\.svg(\?|#|$)", src, re.I)]
    source_figures = [src for src, _alt, _line in parser.images if re.search(r"assets/(figures|tables)/", src, re.I)]
    source_screenshot_refs = [
        src
        for src, _alt, _line in parser.images
        if re.search(r"assets/screenshots/|source-facsimile|paper-facsimile|facsimile-plus-html", src, re.I)
    ]
    has_facsimile_markup = bool(re.search(r"source-facsimile|paper-facsimile|facsimile-plus-html|排版截图", text, re.I))

    if full_source_pre:
        errors.append(f"{path}: full source is buried in a collapsed pre block; render paragraph-level bilingual source in the main flow")
    elif any_large_pre:
        warnings.append(f"{path}: large <pre> block found; avoid using raw pre dumps as the source reading experience")

    if source_count and translation_count and source_count != translation_count:
        errors.append(f"{path}: source/translation block count mismatch ({source_count} source vs {translation_count} translation)")
    if expected_source_blocks is not None and source_count < expected_source_blocks:
        errors.append(f"{path}: expected at least {expected_source_blocks} source reading blocks, found {source_count}")
    if strict and source_count < 10:
        errors.append(f"{path}: too few source reading blocks for a paper learning site ({source_count}); use --expected-source-blocks for exact checks")
    if strict and not language_mode:
        errors.append(f"{path}: no visible bilingual language mode such as 中英 / 中文 / EN only")
    if strict and language_mode and len(parser.buttons) >= 2 and not has_interaction_logic:
        errors.append(f"{path}: language controls look static; wire 中英/中文/EN buttons to actual reading-mode changes")
    if strict and plain_count < max(3, source_count // 3):
        errors.append(f"{path}: plain-language explanations look sparse ({plain_count} plain blocks for {source_count} source blocks)")
    if strict and term_count and not has_interaction_logic:
        errors.append(f"{path}: inline terms are marked but have no detected popover/drawer interaction logic")
    if strict and term_count and not has_popover_or_drawer:
        errors.append(f"{path}: inline terms need an attached popover, drawer, dialog, or side panel")
    if strict and term_count and inline_term_count == 0:
        errors.append(f"{path}: terms are not anchored inline in source/translation/explanation text ({detached_term_count} detached term chips found)")
    if strict and detached_term_count and inline_term_count < detached_term_count:
        warnings.append(f"{path}: detached term chips outnumber inline term anchors ({detached_term_count} detached vs {inline_term_count} inline)")
    if strict and (term_count or has_popover_or_drawer) and not has_close_affordance:
        errors.append(f"{path}: popovers/drawers/term panels need an obvious close state")
    if strict and (term_count or has_popover_or_drawer) and parser.aria_counts["expanded"] == 0:
        errors.append(f"{path}: interactive term/drawer controls should expose state with aria-expanded")
    if strict and (term_count or has_popover_or_drawer) and parser.aria_counts["controls"] == 0:
        errors.append(f"{path}: interactive term/drawer controls should connect triggers to panels with aria-controls")
    if strict and any(name in parser.class_counts for name in ("chapter-map", "chapter-tab", "map-item", "chapter-button")) and parser.aria_counts["current"] == 0:
        warnings.append(f"{path}: chapter navigation should mark the active chapter with aria-current")
    if strict and source_figures:
        figure_cues = {
            "what": ["它是什么", "是什么", "图里", "表里"],
            "how-to-read": ["怎么看", "读法", "先看", "如何读"],
            "comparison": ["相比", "对比", "baseline", "基线"],
            "conclusion": ["结论", "说明", "支持"],
            "limitation": ["不能推出", "不能证明", "不代表", "限制"],
        }
        if not figure_note_texts:
            errors.append(f"{path}: source figures/tables need per-figure explanation blocks")
        elif len(figure_note_texts) < len(source_figures):
            errors.append(f"{path}: fewer figure/table explanations than source figure/table assets ({len(figure_note_texts)} notes for {len(source_figures)} assets)")
        for index, note_text in enumerate(figure_note_texts[: len(source_figures)], start=1):
            missing_cues = cue_missing(note_text, figure_cues)
            if missing_cues:
                preview = compact_text(note_text)[:80]
                errors.append(f"{path}: figure/table explanation #{index} misses cues {', '.join(missing_cues)}: {preview}")
    if diagram_svgs:
        message = f"{path}: generated diagram assets include SVG files under assets/diagrams; use Image 2/bitmap visuals when available: {len(diagram_svgs)} found"
        if strict and not (manifest and manifest.get("allow_svg_fallback") is True):
            errors.append(message)
        else:
            warnings.append(message)

    base = path.parent
    for src, alt, line in parser.images:
        if not src:
            errors.append(f"{path}:{line}: img missing src")
            continue
        if not alt.strip():
            warnings.append(f"{path}:{line}: img missing useful alt text")
        if is_external_or_embedded(src):
            continue
        asset = (base / src.split("#", 1)[0].split("?", 1)[0]).resolve()
        try:
            asset.relative_to(root.resolve())
        except ValueError:
            warnings.append(f"{path}:{line}: img points outside site root: {src}")
        if not asset.exists():
            errors.append(f"{path}:{line}: missing image asset: {src}")

    for src, line in parser.iframes:
        if re.search(r"\.pdf(\?|#|$)", src, re.I):
            errors.append(f"{path}:{line}: PDF iframe found; source text must be in-page")

    for attrs, line in parser.buttons:
        label = attrs.get("aria-label", "").strip() or attrs.get("title", "").strip() or attrs.get("_text", "").strip()
        if not label:
            warnings.append(f"{path}:{line}: button has no visible text, aria-label, or title")

    if strict:
        for pattern, label in PRODUCTION_TEXT_PATTERNS:
            if re.search(pattern, public_text_for_scan, re.I):
                errors.append(f"{path}: public UI exposes internal production text ({label}); rewrite as reader-facing learning copy")
        for attr_name, value, line in parser.attr_texts:
            for pattern, label in PRODUCTION_TEXT_PATTERNS:
                if re.search(pattern, value, re.I):
                    errors.append(f"{path}:{line}: public {attr_name} exposes internal production text ({label})")
        if marginalia_text and re.search(r"资产|生成教学图|manifest|preflight|regression|generated assets?", marginalia_text, re.I):
            errors.append(f"{path}: marginalia/side notes expose production or asset-management language")
        missing_source_ids = [
            str(item.get("data_block") or item.get("id") or item.get("line"))
            for item in parser.reading_blocks
            if not item.get("data_source_id")
        ]
        if parser.reading_blocks and missing_source_ids:
            errors.append(
                f"{path}: reading blocks need stable data-source-id values; missing on {len(missing_source_ids)}/{len(parser.reading_blocks)} blocks"
            )
        if parser.reading_blocks and (source_count < len(parser.reading_blocks) or plain_count < len(parser.reading_blocks)):
            errors.append(
                f"{path}: every reading-block should include source and plain-language layers ({len(parser.reading_blocks)} blocks, {source_count} source labels, {plain_count} plain labels)"
            )
        if source_count and translation_count and plain_count and not (source_count == translation_count == plain_count):
            errors.append(
                f"{path}: source/translation/plain block counts should match ({source_count}/{translation_count}/{plain_count})"
            )
        if term_count:
            required_ladder = ["术语本义", "说人话", "本文指代", "作者怎么用", "常见误解"]
            missing_ladder = [label for label in required_ladder if label not in text]
            if missing_ladder:
                errors.append(f"{path}: term explanations should include full explanation ladder; missing labels: {', '.join(missing_ladder)}")
        generic_action_counts: dict[str, int] = {}
        generic_exact_labels = {"打开图表抽屉", "继续阅读这一章", "查看详情", "展开详情", "了解更多", "阅读更多"}
        for attrs, _line in parser.buttons:
            label = attrs.get("aria-label", "").strip() or attrs.get("title", "").strip() or attrs.get("_text", "").strip()
            if label:
                generic_action_counts[label] = generic_action_counts.get(label, 0) + 1
                if re.fullmatch(r"(查看|查看详情|了解更多|展开|展开详情|继续|探索|打开|阅读|更多|详情)", label, re.I):
                    errors.append(f"{path}: vague button label '{label}' needs a concrete learning object or action")
        for label, count in sorted(generic_action_counts.items()):
            if label in generic_exact_labels:
                errors.append(f"{path}: generic button label '{label}' appears {count} times; name the figure, table, term, chapter, or learning action")
            if count > 3 and label in {"打开图表抽屉", "继续下一章", "查看详情", "展开详情", "了解更多", "展开", "打开"}:
                errors.append(f"{path}: repeated generic button label '{label}' appears {count} times; use figure/table/chapter-specific learning actions")
        long_source_failures = 0
        for index, source_value in enumerate(source_texts):
            words = source_word_count(source_value)
            explanation = plain_texts[index] if index < len(plain_texts) else ""
            if words >= 50 and explanation_length(explanation) < 100:
                long_source_failures += 1
                if long_source_failures <= 5:
                    preview = compact_text(source_value)[:90]
                    errors.append(f"{path}: dense source block #{index + 1} has too little Chinese/plain explanation ({words} source tokens): {preview}")
        if source_texts and translation_texts and len(translation_texts) < len(source_texts):
            errors.append(f"{path}: fewer translation blocks than source text blocks ({len(translation_texts)} translations for {len(source_texts)} source blocks)")

    if re.search(r"<iframe[^>]+pdf", text, re.I):
        errors.append(f"{path}: possible PDF iframe pattern found")
    if "原文" not in text and "Original" not in text:
        warnings.append(f"{path}: no obvious source-text label such as '原文' or 'Original'")
    if "说人话" not in text and "Plain language" not in text:
        warnings.append(f"{path}: no obvious plain-language explanation label")

    if manifest:
        if "_manifest_error" in manifest:
            errors.append(str(manifest["_manifest_error"]))
        expected_source = manifest.get("source_paragraphs_expected")
        rendered_source = manifest.get("source_paragraphs_rendered", source_count)
        expected_figures = manifest.get("paper_figures_expected")
        rendered_figures = manifest.get("paper_figures_rendered")
        expected_visuals = manifest.get("generated_visuals_expected")
        rendered_visuals = manifest.get("generated_visuals_rendered")
        image_model = str(manifest.get("image_generation_model", "")).lower()
        source_language = str(manifest.get("source_language", "")).lower()
        source_blocks = manifest.get("source_blocks")
        chapter_coverage = manifest.get("chapter_coverage")
        term_anchors = manifest.get("term_anchors")
        generated_visuals = manifest.get("generated_visuals")
        paper_figures_manifest = manifest.get("paper_figures")
        generated_visual_language = str(manifest.get("generated_visual_language", "")).lower()
        design_brief = manifest.get("design_brief")
        layout_strategy = manifest.get("layout_strategy")
        source_rendering_modes = manifest.get("source_rendering_modes")
        source_screenshot_blocks = manifest.get("source_screenshot_blocks")
        interaction_inventory = manifest.get("interaction_inventory")
        if expected_source_blocks is not None and not isinstance(expected_source, int):
            expected_source = expected_source_blocks
        if isinstance(expected_source, int) and rendered_source < expected_source:
            errors.append(f"{path}: manifest says only {rendered_source}/{expected_source} source paragraphs rendered")
        if isinstance(expected_figures, int) and isinstance(rendered_figures, int) and rendered_figures < expected_figures:
            errors.append(f"{path}: manifest says only {rendered_figures}/{expected_figures} paper figures/tables rendered")
        if isinstance(expected_visuals, int) and isinstance(rendered_visuals, int) and rendered_visuals < expected_visuals:
            errors.append(f"{path}: manifest says only {rendered_visuals}/{expected_visuals} generated visuals rendered")
        if strict and expected_visuals and "image" not in image_model and "gpt-image" not in image_model:
            errors.append(f"{path}: manifest does not record an Image 2/image-generation model for generated visuals")
        if strict:
            if manifest.get("public_ui_clean") is False:
                errors.append(f"{path}: manifest says public_ui_clean=false")
            if not isinstance(design_brief, dict) or not design_brief:
                errors.append(f"{path}: manifest needs design_brief with paper-specific visual direction and typography/layout choices")
            else:
                required_design_keys = {"visual_direction", "topic_motif", "typography_plan", "why_not_generic"}
                missing_design_keys = sorted(required_design_keys - set(str(key) for key in design_brief.keys()))
                if missing_design_keys:
                    errors.append(f"{path}: design_brief missing keys: {', '.join(missing_design_keys)}")
                design_text = " ".join(str(value) for value in design_brief.values()).lower()
                if re.search(r"\bdashboard\b|generic|ai gradient|模板|通用", design_text):
                    warnings.append(f"{path}: design_brief sounds generic; explain the paper-specific visual system")
            if not isinstance(layout_strategy, dict) or not layout_strategy.get("summary"):
                errors.append(f"{path}: manifest needs layout_strategy.summary explaining why this reading layout fits the paper")
            else:
                if layout_strategy.get("desktop_first_viewport_checked") is not True:
                    errors.append(f"{path}: layout_strategy.desktop_first_viewport_checked must be true after browser review")
                if layout_strategy.get("mobile_layout_checked") is not True:
                    errors.append(f"{path}: layout_strategy.mobile_layout_checked must be true after responsive review")
            if not isinstance(source_rendering_modes, list) or not source_rendering_modes:
                errors.append(f"{path}: manifest needs source_rendering_modes[] such as parallel-bilingual, stacked-bilingual, interleaved-close-reading, figure-led")
            elif isinstance(expected_source, int) and expected_source >= 20 and len(set(map(str, source_rendering_modes))) == 1:
                warnings.append(f"{path}: only one source rendering mode recorded for a long paper; confirm the layout is not a one-template reader")
            if source_screenshot_blocks is None:
                errors.append(f"{path}: manifest needs source_screenshot_blocks[]; use [] when no original-text facsimile screenshots are rendered")
            elif not isinstance(source_screenshot_blocks, list):
                errors.append(f"{path}: source_screenshot_blocks must be a list")
            if (source_screenshot_refs or has_facsimile_markup) and not source_screenshot_blocks:
                errors.append(f"{path}: source facsimile/screenshot markup is present but manifest has no source_screenshot_blocks[] entries")
            if isinstance(source_screenshot_blocks, list):
                for index, item in enumerate(source_screenshot_blocks, start=1):
                    if not isinstance(item, dict):
                        errors.append(f"{path}: source_screenshot_blocks[{index}] must be an object")
                        continue
                    required = {"source_id", "path", "reason", "selectable_text_fallback_id"}
                    missing = sorted(required - set(str(key) for key in item.keys()))
                    if missing:
                        errors.append(f"{path}: source_screenshot_blocks[{index}] missing keys: {', '.join(missing)}")
                    block_path = str(item.get("path", ""))
                    if block_path:
                        asset = (root / block_path.split("#", 1)[0].split("?", 1)[0]).resolve()
                        try:
                            asset.relative_to(root.resolve())
                        except ValueError:
                            errors.append(f"{path}: source_screenshot_blocks[{index}] path points outside site root: {block_path}")
                        if not asset.exists():
                            errors.append(f"{path}: source_screenshot_blocks[{index}] missing image asset: {block_path}")
                        if block_path not in text:
                            warnings.append(f"{path}: source_screenshot_blocks[{index}] path is not referenced in HTML: {block_path}")
                    fallback_id = str(item.get("selectable_text_fallback_id", ""))
                    if fallback_id and fallback_id not in text:
                        errors.append(f"{path}: source_screenshot_blocks[{index}] fallback id not found in HTML: {fallback_id}")
            if not isinstance(interaction_inventory, dict) or not interaction_inventory:
                errors.append(f"{path}: manifest needs interaction_inventory with real learning interactions and tested controls")
            else:
                learning_keys = {
                    "figure_hotspots",
                    "formula_breakdowns",
                    "comparison_tables",
                    "chapter_quizzes",
                    "knowledge_map",
                    "method_chats",
                    "visualizers",
                    "concept_maps",
                }
                has_learning_action = False
                for key in learning_keys:
                    value = interaction_inventory.get(key)
                    if value is True or (isinstance(value, (int, float)) and value > 0) or (isinstance(value, list) and value):
                        has_learning_action = True
                if not has_learning_action:
                    errors.append(f"{path}: interaction_inventory needs at least one non-decorative learning action beyond passive text/terms")
                tested_controls = interaction_inventory.get("tested_controls")
                if not isinstance(tested_controls, list) or not tested_controls:
                    errors.append(f"{path}: interaction_inventory needs tested_controls[] with trigger, state_change, close_method, and linked_source_ids")
                else:
                    for index, item in enumerate(tested_controls[:12], start=1):
                        if not isinstance(item, dict):
                            errors.append(f"{path}: tested_controls[{index}] must be an object")
                            continue
                        missing = [key for key in ("trigger", "state_change", "close_method", "linked_source_ids") if not item.get(key)]
                        if missing:
                            errors.append(f"{path}: tested_controls[{index}] missing: {', '.join(missing)}")
            if isinstance(expected_source, int) and expected_source >= 10:
                if not isinstance(source_blocks, list) or not source_blocks:
                    errors.append(f"{path}: manifest needs source_blocks[] with per-paragraph ids/hashes, not only total source paragraph counts")
                if not isinstance(chapter_coverage, list) or not chapter_coverage:
                    errors.append(f"{path}: manifest needs chapter_coverage[] with expected/rendered/missing source ids per chapter")
            if isinstance(source_blocks, list) and isinstance(rendered_source, int) and len(source_blocks) < rendered_source:
                errors.append(f"{path}: manifest source_blocks length ({len(source_blocks)}) is smaller than rendered source count ({rendered_source})")
            if isinstance(chapter_coverage, list):
                for index, chapter in enumerate(chapter_coverage, start=1):
                    if not isinstance(chapter, dict):
                        continue
                    missing_ids = chapter.get("missing_source_ids")
                    if isinstance(missing_ids, list) and missing_ids:
                        errors.append(f"{path}: chapter_coverage[{index}] has missing_source_ids: {', '.join(map(str, missing_ids[:5]))}")
                    expected_ids = chapter.get("expected_source_ids")
                    rendered_ids = chapter.get("rendered_source_ids")
                    if isinstance(expected_ids, list) and isinstance(rendered_ids, list):
                        missing_rendered = sorted(set(map(str, expected_ids)) - set(map(str, rendered_ids)))
                        if missing_rendered:
                            errors.append(f"{path}: chapter_coverage[{index}] did not render expected source ids: {', '.join(missing_rendered[:5])}")
            if isinstance(source_blocks, list):
                missing_render_refs = []
                for block in source_blocks[:20]:
                    if not isinstance(block, dict):
                        continue
                    source_id = str(block.get("source_id", ""))
                    rendered_block_id = str(block.get("rendered_block_id", ""))
                    if rendered_block_id and rendered_block_id not in text and source_id and source_id not in text:
                        missing_render_refs.append(rendered_block_id or source_id)
                if missing_render_refs:
                    errors.append(f"{path}: manifest source_blocks do not map back to visible DOM ids/snippets: {', '.join(missing_render_refs[:5])}")
            if term_count:
                inline_manifest_terms = 0
                if isinstance(term_anchors, list):
                    inline_manifest_terms = sum(1 for item in term_anchors if isinstance(item, dict) and item.get("is_inline") is True)
                if not inline_manifest_terms:
                    errors.append(f"{path}: manifest needs term_anchors[] with inline source/translation/plain-text locations")
            term_strip_only_count = manifest.get("term_strip_only_count")
            if isinstance(term_strip_only_count, int) and term_strip_only_count > 0:
                errors.append(f"{path}: manifest reports {term_strip_only_count} terms that only exist in detached strips")
            is_chinese_bilingual = source_language not in {"", "zh", "zh-cn", "zh-hans"} and language_mode
            if is_chinese_bilingual and isinstance(rendered_visuals, int) and rendered_visuals > 0:
                if generated_visual_language and generated_visual_language not in {"zh-dominant", "chinese-dominant"}:
                    errors.append(f"{path}: generated diagrams should be Chinese-dominant for Chinese-bilingual sites, got '{generated_visual_language}'")
                if not generated_visual_language:
                    errors.append(f"{path}: manifest must record generated_visual_language for Chinese-bilingual generated diagrams")
            if isinstance(chapter_coverage, list):
                non_appendix_chapters = [
                    chapter
                    for chapter in chapter_coverage
                    if isinstance(chapter, dict)
                    and not re.search(
                        r"appendix|references|bibliography|supplement|附录|参考文献",
                        f"{chapter.get('chapter_id', '')} {chapter.get('title', '')}",
                        re.I,
                    )
                ]
                if isinstance(rendered_visuals, int) and non_appendix_chapters and rendered_visuals < len(non_appendix_chapters):
                    errors.append(
                        f"{path}: generated visuals are below the per-chapter teaching expectation ({rendered_visuals} visuals for {len(non_appendix_chapters)} non-appendix chapters)"
                    )
                for index, chapter in enumerate(non_appendix_chapters, start=1):
                    visual_ids = chapter.get("generated_visual_ids")
                    if visual_ids is not None and not visual_ids:
                        errors.append(f"{path}: chapter_coverage[{index}] has no generated_visual_ids; each major chapter needs a teaching visual or a justified omission")
            if isinstance(generated_visuals, list):
                for index, item in enumerate(generated_visuals, start=1):
                    if not isinstance(item, dict):
                        continue
                    if not (item.get("model_name") or item.get("tool") or image_model):
                        errors.append(f"{path}: generated visual #{index} must record model_name/tool")
                    for key in ("teaches_concept", "reader_question", "why_image_needed"):
                        if not item.get(key):
                            errors.append(f"{path}: generated visual #{index} must record {key}")
                    if not item.get("linked_source_ids") and not item.get("linked_claim_ids"):
                        errors.append(f"{path}: generated visual #{index} should link to source paragraphs or claims")
                    language = str(item.get("in_image_text_language", item.get("prompt_language", ""))).lower()
                    ratio = item.get("chinese_label_ratio")
                    if is_chinese_bilingual and not language:
                        errors.append(f"{path}: generated visual #{index} must record in_image_text_language or prompt_language")
                    if is_chinese_bilingual and language and language not in {"zh", "zh-dominant", "chinese", "chinese-dominant", "mixed"}:
                        errors.append(f"{path}: generated visual #{index} records non-Chinese-dominant in-image language: {language}")
                    if is_chinese_bilingual and isinstance(ratio, (int, float)) and ratio < 0.6:
                        errors.append(f"{path}: generated visual #{index} has low Chinese label ratio ({ratio}); use Chinese-dominant labels/callouts")
                    factual_values = item.get("factual_values_used")
                    source_refs = item.get("source_refs_for_values")
                    if factual_values and not source_refs:
                        errors.append(f"{path}: generated visual #{index} uses factual values without source_refs_for_values")
            elif strict and isinstance(rendered_visuals, int) and rendered_visuals > 0:
                warnings.append(f"{path}: manifest should include generated_visuals[] entries with language and source-link metadata")
            if isinstance(paper_figures_manifest, list):
                for index, item in enumerate(paper_figures_manifest, start=1):
                    if not isinstance(item, dict):
                        continue
                    if not (item.get("primary_rendered_block_id") or item.get("primary_source_id") or item.get("linked_source_ids")):
                        errors.append(f"{path}: paper figure/table #{index} needs a primary in-flow reading position linked to source ids")
                    primary_block = str(item.get("primary_rendered_block_id", "") or "")
                    primary_source = str(item.get("primary_source_id", "") or "")
                    figure_path = str(item.get("path", "") or "")
                    if primary_block and primary_block not in text:
                        errors.append(f"{path}: paper figure/table #{index} primary_rendered_block_id not found in HTML: {primary_block}")
                    if primary_source and primary_source not in text:
                        errors.append(f"{path}: paper figure/table #{index} primary_source_id not found in HTML: {primary_source}")
                    if figure_path and figure_path not in text:
                        warnings.append(f"{path}: paper figure/table #{index} path is not referenced in HTML: {figure_path}")
                    cues = item.get("explanation_cues_present")
                    if isinstance(cues, list):
                        required = {"它是什么", "怎么看", "结论是什么", "不能推出什么"}
                        missing = sorted(required - {str(cue) for cue in cues})
                        if missing:
                            errors.append(f"{path}: paper figure/table #{index} manifest explanation cues missing: {', '.join(missing)}")
            elif isinstance(expected_figures, int) and expected_figures > 0:
                errors.append(f"{path}: manifest needs paper_figures[] with primary placement and per-figure explanation metadata")
    elif strict:
        errors.append(f"{path}: no learning-site manifest found; add data/learning-site-manifest.json for exact coverage checks")

    if strict:
        render_errors, render_warnings = run_desktop_first_viewport_check(path, root)
        errors.extend(render_errors)
        warnings.extend(render_warnings)
        render_errors, render_warnings = run_mobile_render_check(path, root)
        errors.extend(render_errors)
        warnings.extend(render_warnings)

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a static paper learning site.")
    parser.add_argument("target", help="Path to site directory or HTML file")
    parser.add_argument("--strict", action="store_true", help="Treat core product-quality gaps as errors")
    parser.add_argument("--expected-source-blocks", type=int, help="Expected minimum number of source reading blocks in the main reader")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target.exists():
        print(f"ERROR: target does not exist: {target}", file=sys.stderr)
        return 2

    root = target.parent if target.is_file() else target
    manifest = load_manifest(root)
    html_files = find_html_files(target)
    if not html_files:
        print(f"ERROR: no HTML files found under {target}", file=sys.stderr)
        return 2

    all_errors: list[str] = []
    all_warnings: list[str] = []
    for html_file in html_files:
        errors, warnings = audit_html(html_file, root, args.strict, manifest, args.expected_source_blocks)
        all_errors.extend(errors)
        all_warnings.extend(warnings)

    for warning in all_warnings:
        print(f"WARN: {warning}")
    for error in all_errors:
        print(f"ERROR: {error}")

    print(f"Audited {len(html_files)} HTML file(s). Errors: {len(all_errors)}. Warnings: {len(all_warnings)}.")
    return 1 if all_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
