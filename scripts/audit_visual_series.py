#!/usr/bin/env python3
"""Strict static checks for ordered paper explainer image series."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image, ImageChops, ImageStat
except Exception:
    Image = None
    ImageChops = None
    ImageStat = None


BITMAP_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_hash(value: object) -> str:
    return str(value or "").replace("sha256:", "").strip().lower()


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def command_path(name: str) -> str | None:
    dependency_root = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies"
    for candidate in (dependency_root / "bin" / "override" / name, dependency_root / "bin" / name):
        if candidate.exists():
            return str(candidate)
    return shutil.which(name)


def validate_album_pdf(
    pdf_path: Path,
    expected_pages: int,
    target_ratio: str,
    image_paths: list[Path],
    qa_dir: Path,
) -> list[str]:
    issues: list[str] = []
    if not pdf_path.exists() or pdf_path.stat().st_size < 1024:
        return ["Album PDF is missing or suspiciously small."]
    if pdf_path.read_bytes()[:5] != b"%PDF-":
        return ["Album export is not a valid PDF file."]
    pdfinfo = command_path("pdfinfo")
    if not pdfinfo:
        return ["pdfinfo is unavailable; album PDF page count and ratio cannot be verified."]
    result = subprocess.run([pdfinfo, str(pdf_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
    if result.returncode != 0:
        return [f"pdfinfo could not read album PDF: {(result.stderr or result.stdout).strip()[:240]}"]
    pages_match = re.search(r"^Pages:\s+(\d+)", result.stdout, re.M)
    pages = int(pages_match.group(1)) if pages_match else None
    if pages != expected_pages:
        issues.append(f"Album PDF page count does not match image series: pdf={pages}, images={expected_pages}.")
    size_match = re.search(r"^Page size:\s+([0-9.]+)\s+x\s+([0-9.]+)", result.stdout, re.M)
    expected_ratios = {"3:4": 3 / 4, "4:3": 4 / 3, "16:9": 16 / 9}
    if size_match and target_ratio in expected_ratios:
        width, height = float(size_match.group(1)), float(size_match.group(2))
        if height <= 0 or abs((width / height) - expected_ratios[target_ratio]) > 0.06:
            issues.append(f"Album PDF ratio does not match image target {target_ratio}: {width}x{height}.")
    elif target_ratio in expected_ratios:
        issues.append("Could not verify album PDF page dimensions.")
    renderer = command_path("pdftoppm")
    if renderer and pages and Image is not None and ImageChops is not None and ImageStat is not None:
        qa_dir.mkdir(parents=True, exist_ok=True)
        for page_number, reference_path in enumerate(image_paths, 1):
            output_stem = qa_dir / f"album-page-{page_number:03d}"
            render = subprocess.run(
                [renderer, "-f", str(page_number), "-l", str(page_number), "-singlefile", "-png", "-r", "36", str(pdf_path), str(output_stem)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60,
            )
            rendered_path = output_stem.with_suffix(".png")
            if render.returncode != 0 or not rendered_path.exists():
                issues.append(f"Could not render album PDF page {page_number} for order verification.")
                continue
            try:
                with Image.open(reference_path) as reference, Image.open(rendered_path) as rendered:
                    reference_thumb = reference.convert("RGB").resize((240, 320))
                    rendered_thumb = rendered.convert("RGB").resize((240, 320))
                    delta = sum(ImageStat.Stat(ImageChops.difference(reference_thumb, rendered_thumb)).mean) / 3
                if delta > 18:
                    issues.append(f"Album PDF page {page_number} does not visually match the numbered source image (mean delta {delta:.1f}).")
            except Exception:
                issues.append(f"Could not compare album PDF page {page_number} with its numbered source image.")
    return issues


def has_review_lenses(passes: list[dict]) -> bool:
    lens_text = " ".join(str(item.get("lens", "")).lower() for item in passes if isinstance(item, dict))
    return (
        any(token in lens_text for token in ("visual", "design", "美观", "视觉"))
        and any(token in lens_text for token in ("information", "completeness", "信息", "完整"))
        and any(token in lens_text for token in ("narrative", "novice", "logic", "叙事", "新手", "逻辑"))
    )


def run_actual_ocr(paths: list[Path]) -> tuple[dict[str, dict] | None, str | None]:
    if not paths:
        return {}, None
    swift = command_path("swift")
    vision_script = Path(__file__).with_name("ocr_images_vision.swift")
    if swift and vision_script.exists() and sys.platform == "darwin":
        result = subprocess.run(
            [swift, str(vision_script), *[str(path.resolve()) for path in paths]],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=max(120, len(paths) * 20),
        )
        if result.returncode != 0:
            return None, f"Apple Vision OCR failed: {(result.stderr or result.stdout).strip()[:400]}"
        try:
            records = json.loads(result.stdout)
            return {str(Path(record["path"]).resolve()): record for record in records}, None
        except Exception as exc:
            return None, f"Apple Vision OCR returned invalid JSON: {exc}"
    tesseract = command_path("tesseract")
    if tesseract:
        records: dict[str, dict] = {}
        for path in paths:
            result = subprocess.run([tesseract, str(path), "stdout", "-l", "chi_sim+eng"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
            if result.returncode != 0:
                return None, f"Tesseract OCR failed for {path.name}: {(result.stderr or result.stdout).strip()[:300]}"
            records[str(path.resolve())] = {"path": str(path.resolve()), "text": result.stdout, "confidence": 1.0, "error": None}
        return records, None
    return None, "No executable OCR route found. Install Tesseract or use macOS with Swift/Vision."


def audit_teaching_coverage(root: Path, manifest: dict, size_mode: str, errors: list[str]) -> None:
    meta = manifest.get("teaching_fidelity", {})
    rel = meta.get("inventory_path")
    if not rel or not (root / str(rel)).exists():
        errors.append("Missing data/teaching-inventory.json or teaching_fidelity.inventory_path.")
        return
    path = root / str(rel)
    inventory = load_json(path)
    if not inventory:
        errors.append("Teaching inventory is invalid JSON.")
        return
    if clean_hash(meta.get("inventory_sha256")) != file_hash(path):
        errors.append("Teaching inventory hash is missing or incorrect.")
    if inventory.get("derivation_checked") is not True or inventory.get("reviewer_status") != "passed":
        errors.append("Teaching inventory derivation/review has not passed.")
    if clean_hash(inventory.get("source_inventory_sha256")) != clean_hash(manifest.get("source_fidelity", {}).get("main_text_inventory_sha256")):
        errors.append("Teaching inventory is not linked to the current source inventory hash.")
    if not inventory.get("hard_concepts"):
        errors.append("Teaching inventory must identify at least one hard concept.")
    if not inventory.get("central_claims"):
        errors.append("Teaching inventory must identify at least one central claim.")
    if "paper_has_experiments" not in inventory:
        errors.append("Teaching inventory must record paper_has_experiments.")
    elif inventory.get("paper_has_experiments") is True and not inventory.get("experiments"):
        errors.append("Teaching inventory says the paper has experiments but experiments[] is empty.")
    final_items = {str(item.get("id")): item for item in manifest.get("items", []) if item.get("id")}
    for concept in inventory.get("hard_concepts", []):
        for field in ("term", "plain_label", "field_definition", "plain_explanation", "paper_specific_meaning", "common_misunderstanding", "definition_item_ids"):
            if not concept.get(field):
                errors.append(f"Hard concept {concept.get('id', '[unknown]')} is missing {field}.")
        concept_id = str(concept.get("id", ""))
        for item_id in concept.get("definition_item_ids", []):
            item = final_items.get(str(item_id))
            if not item:
                errors.append(f"Hard concept {concept_id} references missing definition item {item_id}.")
            elif concept_id not in {str(value) for value in item.get("explained_concept_ids", [])}:
                errors.append(f"Definition item {item_id} does not declare explained_concept_ids coverage for {concept_id}.")
    for experiment in inventory.get("experiments", []):
        for field in (
            "comparison_objects",
            "sample_size",
            "metric",
            "metric_definition",
            "evaluator",
            "baseline_status",
            "uncertainty_or_missing",
        ):
            if experiment.get(field) in (None, "", []):
                errors.append(f"Experiment {experiment.get('id', '[unknown]')} is missing {field}; use not_reported_by_paper when necessary.")
        setup_ids = experiment.get("setup_item_ids", [])
        result_ids = experiment.get("result_item_ids", [])
        limitation_ids = experiment.get("limitation_item_ids", [])
        if not setup_ids or not result_ids or not limitation_ids:
            errors.append(f"Experiment {experiment.get('id', '[unknown]')} needs setup_item_ids, result_item_ids, and limitation_item_ids.")
        for item_id in [*setup_ids, *result_ids, *limitation_ids]:
            if str(item_id) not in final_items:
                errors.append(f"Experiment {experiment.get('id', '[unknown]')} references missing final item {item_id}.")
        experiment_id = str(experiment.get("id", ""))
        for item_id in limitation_ids:
            item = final_items.get(str(item_id), {})
            if experiment_id not in {str(value) for value in item.get("covered_experiment_limitations", [])}:
                errors.append(f"Experiment limitation item {item_id} does not visibly cover {experiment_id}.")
        ordered_ids = list(final_items)
        valid_setup = [ordered_ids.index(str(item_id)) for item_id in setup_ids if str(item_id) in final_items]
        valid_results = [ordered_ids.index(str(item_id)) for item_id in result_ids if str(item_id) in final_items]
        if valid_setup and valid_results and max(valid_setup) >= min(valid_results):
            errors.append(f"Experiment {experiment.get('id', '[unknown]')} setup pages must precede result pages.")
    for formula in inventory.get("formula_or_algorithm_items", []):
        for field in ("expression_or_name", "plain_explanation", "expected_tokens", "render_item_ids"):
            if not formula.get(field):
                errors.append(f"Formula/algorithm {formula.get('id', '[unknown]')} is missing {field}.")
        expected_tokens = {str(token) for token in formula.get("expected_tokens", [])}
        for item_id in formula.get("render_item_ids", []):
            item = final_items.get(str(item_id))
            if not item:
                errors.append(f"Formula/algorithm {formula.get('id', '[unknown]')} references missing item {item_id}.")
            elif not expected_tokens.issubset({str(token) for token in item.get("expected_labels", [])}):
                errors.append(f"Formula item {item_id} expected_labels do not cover the required formula tokens.")
    groups = {
        "hard_concepts": "hard_concept_coverage",
        "formula_or_algorithm_items": "formula_coverage",
        "experiments": "experiment_coverage",
        "major_figures": "major_figure_coverage",
        "central_claims": "central_claim_coverage",
    }
    for inventory_key, coverage_key in groups.items():
        entries = inventory.get(inventory_key)
        coverage = manifest.get(coverage_key)
        if not isinstance(entries, list):
            errors.append(f"Teaching inventory must contain {inventory_key}[].")
            continue
        if not isinstance(coverage, list):
            errors.append(f"Manifest must contain {coverage_key}[].")
            continue
        by_id = {str(item.get("inventory_id")): item for item in coverage if isinstance(item, dict) and item.get("inventory_id")}
        for entry in entries:
            item_id = str(entry.get("id", ""))
            item = by_id.get(item_id)
            if not item:
                errors.append(f"Teaching inventory item has no coverage entry: {inventory_key}:{item_id}")
                continue
            status = item.get("status")
            level = entry.get("required_level", "core")
            omission_allowed = level == "secondary" or (level == "major" and size_mode == "concise")
            if status == "omitted":
                if not omission_allowed or not item.get("reason"):
                    errors.append(f"Required teaching item was omitted without an allowed reason: {inventory_key}:{item_id}")
            elif status != "covered" or not item.get("final_item_ids"):
                errors.append(f"Teaching coverage must be covered with final_item_ids: {inventory_key}:{item_id}")
    central_claim_ids = {str(item.get("id")) for item in inventory.get("central_claims", []) if item.get("id")}
    bundles = manifest.get("evidence_bundles", [])
    bundle_claim_ids = {str(item.get("claim_id")) for item in bundles if isinstance(item, dict) and item.get("claim_id")}
    missing = central_claim_ids - bundle_claim_ids
    if missing:
        errors.append(f"Central claims are missing evidence bundles: {sorted(missing)}")
    for bundle in bundles:
        for field in ("bundle_id", "claim_id", "final_item_ids", "source_ids", "source_excerpt_or_asset", "visible_source_cue", "chinese_explanation", "evidence_meaning", "limitation"):
            if not bundle.get(field):
                errors.append(f"Evidence bundle is missing {field}.")
        if bundle.get("source_cue_ocr_pass") is not True:
            errors.append(f"Image-series evidence bundle source cue has not passed OCR: {bundle.get('bundle_id')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit a paper explainer image series.")
    parser.add_argument("path", help="Image-series output directory")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--require-pdf", action="store_true", help="Require and validate the page-matched album PDF")
    parser.add_argument("--source", help="Original source PDF/article; verifies the final package belongs to the requested source")
    args = parser.parse_args()

    root = Path(args.path).expanduser().resolve()
    errors: list[str] = []
    warnings: list[str] = []
    if args.strict and not args.source:
        errors.append("Strict image-series audit requires --source so source identity cannot be self-reported.")
    manifest_path = root / "data" / "learning-series-manifest.json"
    storyboard_path = root / "data" / "storyboard.json"

    if not manifest_path.exists():
        errors.append("Missing data/learning-series-manifest.json")
        manifest = {}
    else:
        manifest = load_json(manifest_path)
        if not manifest:
            errors.append("Invalid learning-series-manifest.json")

    if not storyboard_path.exists():
        errors.append("Missing data/storyboard.json")
        storyboard = {}
    else:
        storyboard = load_json(storyboard_path)
        if not storyboard:
            errors.append("Invalid storyboard.json")

    if manifest:
        if str(manifest.get("manifest_schema_version")) != "0.4":
            errors.append("Manifest schema version must be 0.4.")
        if manifest.get("output_mode") != "image-series":
            errors.append("Manifest output_mode must be image-series.")
        reader_language = str(manifest.get("reader_language", ""))
        if not reader_language:
            errors.append("Manifest must record reader_language.")
        size_mode = manifest.get("size_mode")
        if size_mode not in {"concise", "medium", "detailed"}:
            errors.append("Manifest must record resolved size_mode.")
        if manifest.get("size_mode_requested") == "automatic":
            sizing = manifest.get("automatic_sizing", {})
            for field in ("complexity_score", "score_breakdown", "target_min", "target_max", "maximum_count", "resolved_count", "rationale"):
                if sizing.get(field) in (None, "", []):
                    errors.append(f"Automatic sizing is missing {field}.")
        items = manifest.get("items", [])
        expected = manifest.get("items_expected")
        rendered = manifest.get("items_rendered")
        if expected != len(items) or rendered != len(items):
            errors.append("Expected/rendered counts must match the item inventory.")
        if manifest.get("size_mode_requested") == "automatic":
            sizing = manifest.get("automatic_sizing", {})
            if sizing.get("resolved_count") != len(items) or not sizing.get("target_min", 0) <= len(items) <= sizing.get("target_max", 0):
                errors.append("Automatic image count is outside its recorded target range or resolved_count.")
        count = len(items)
        if size_mode == "concise" and (count > 10 or (count < 6 and not manifest.get("shorter_user_approved"))):
            errors.append("Concise image series must contain 6-10 images unless a shorter set was explicitly approved.")
        if size_mode == "medium" and not 11 <= count <= 20:
            errors.append("Medium image series must contain 11-20 images.")
        if size_mode == "detailed" and count < 21:
            errors.append("Detailed image series must contain at least 21 images.")
        if count > 36 and not manifest.get("over_36_user_approved"):
            errors.append("Image series exceeds 36 items without explicit approval.")
        audit_teaching_coverage(root, manifest, size_mode, errors)

        storyboard_meta = manifest.get("storyboard", {})
        if storyboard_meta.get("locked_before_final_generation") is not True:
            errors.append("Storyboard was not locked before final generation.")
        if clean_hash(storyboard_meta.get("sha256")) != (file_hash(storyboard_path) if storyboard_path.exists() else ""):
            errors.append("Storyboard hash is missing or incorrect.")
        story_items = storyboard.get("items", storyboard.get("slides", [])) if storyboard else []
        story_ids = [str(item.get("id")) for item in story_items if item.get("id")]
        item_ids = [str(item.get("id")) for item in items if item.get("id")]
        if story_ids != item_ids:
            errors.append("Storyboard and manifest image order do not match exactly.")
        for index, story_item in enumerate(story_items):
            if index > 0:
                previous_id = str(story_items[index - 1].get("id", ""))
                if not story_item.get("previous_bridge") or str(story_item.get("previous_item_id")) != previous_id:
                    errors.append(f"Storyboard item {story_item.get('id')} lacks a valid previous bridge/link.")
            if index < len(story_items) - 1:
                next_id = str(story_items[index + 1].get("id", ""))
                if not story_item.get("next_bridge") or str(story_item.get("next_item_id")) != next_id:
                    errors.append(f"Storyboard item {story_item.get('id')} lacks a valid next bridge/link.")

        acts = storyboard.get("acts", []) if storyboard else []
        roles = {str(act.get("learning_role")) for act in acts if act.get("learning_role")}
        if not {"problem", "prerequisite", "method", "evidence", "limitation"}.issubset(roles):
            errors.append("Image series lacks the complete teaching arc.")

        argument_map = storyboard.get("paper_argument_map", {}) if storyboard else {}
        for field in ("main_question", "thesis", "argument_steps", "evidence_route", "conclusion", "limitation"):
            if not argument_map.get(field):
                errors.append(f"Storyboard paper_argument_map is missing {field}.")
        if len(argument_map.get("argument_steps", [])) < 3:
            errors.append("Storyboard paper_argument_map needs at least three ordered argument steps.")
        if len(argument_map.get("evidence_route", [])) < 2:
            errors.append("Storyboard paper_argument_map needs an explicit evidence route.")

        opening_roles = [str(item.get("sequence_role", "")) for item in items[:3]]
        if not any(role in {"paper-overview", "overview-and-argument-map"} for role in opening_roles[:2]):
            errors.append("A paper overview must appear by image 2.")
        if not any(role in {"argument-map", "overview-and-argument-map"} for role in opening_roles):
            errors.append("An argument map must appear by image 3.")
        all_sequence_roles = [str(item.get("sequence_role", "")) for item in items]
        valid_sequence_roles = {
            "cover-thesis",
            "paper-overview",
            "argument-map",
            "overview-and-argument-map",
            "prerequisite",
            "framework-overview",
            "method-detail",
            "argument-detail",
            "worked-example",
            "experiment-setup",
            "evidence",
            "conclusion",
            "limitation",
            "recap",
        }
        invalid_roles = sorted({role for role in all_sequence_roles if role not in valid_sequence_roles})
        if invalid_roles:
            errors.append(f"Image series contains invalid sequence_role values: {invalid_roles}")
        if "overview-and-argument-map" not in all_sequence_roles:
            if "paper-overview" in all_sequence_roles and "argument-map" in all_sequence_roles and all_sequence_roles.index("paper-overview") > all_sequence_roles.index("argument-map"):
                errors.append("Paper overview must precede the argument map.")
        for role in ("conclusion", "limitation", "recap"):
            if role not in all_sequence_roles:
                errors.append(f"Image series is missing required closing role: {role}")
        if "recap" in all_sequence_roles and all_sequence_roles[-1] != "recap":
            errors.append("The final image must be the learner recap/reconstruction page.")
        recap_expected = storyboard.get("recap_expected_concepts", [])
        if len(recap_expected) < 5:
            errors.append("Storyboard recap_expected_concepts must cover at least problem, method, evidence, conclusion, and limitation.")
        if "recap" in all_sequence_roles:
            recap_item = items[all_sequence_roles.index("recap")]
            if not set(map(str, recap_expected)).issubset({str(value) for value in recap_item.get("recap_concepts", [])}):
                errors.append("Final recap image does not cover all recap_expected_concepts.")
        if all(role in all_sequence_roles for role in ("evidence", "conclusion", "limitation", "recap")):
            positions = [all_sequence_roles.index(role) for role in ("evidence", "conclusion", "limitation", "recap")]
            if positions != sorted(positions):
                errors.append("Closing teaching order must be evidence -> conclusion -> limitation -> recap.")
        detail_positions = [index for index, role in enumerate(all_sequence_roles) if role in {"method-detail", "argument-detail", "worked-example", "experiment-setup", "evidence"}]
        if "prerequisites_required" not in storyboard:
            errors.append("Storyboard must record prerequisites_required and its rationale.")
        if not storyboard.get("prerequisites_rationale"):
            errors.append("Storyboard is missing prerequisites_rationale.")
        if detail_positions and storyboard.get("prerequisites_required") is True:
            first_detail = min(detail_positions)
            if "prerequisite" not in all_sequence_roles[:first_detail]:
                errors.append("Prerequisite teaching must appear before detailed method or evidence pages.")
        if "method-detail" in all_sequence_roles:
            first_method_detail = all_sequence_roles.index("method-detail")
            if "framework-overview" not in all_sequence_roles[:first_method_detail]:
                errors.append("A framework overview must precede component-level detail.")
        if "worked_example_required" not in storyboard:
            errors.append("Storyboard must record worked_example_required and its rationale.")
        elif storyboard.get("worked_example_required") is True and "worked-example" not in all_sequence_roles:
            errors.append("Storyboard requires a worked example, but no worked-example item exists.")
        if not storyboard.get("worked_example_rationale"):
            errors.append("Storyboard is missing worked_example_rationale.")
        method_stage_count = storyboard.get("method_stage_count")
        if not isinstance(method_stage_count, int) or method_stage_count < 0:
            errors.append("Storyboard must record a non-negative method_stage_count.")
        elif method_stage_count >= 3 and storyboard.get("worked_example_required") is not True:
            errors.append("A method with three or more stages must require a worked example.")
        if "paper_has_experiments" not in storyboard:
            errors.append("Storyboard must record paper_has_experiments.")
        elif storyboard.get("paper_has_experiments") is True:
            if "experiment-setup" not in all_sequence_roles or "evidence" not in all_sequence_roles:
                errors.append("Experimental papers need experiment-setup and evidence pages.")
            elif all_sequence_roles.index("experiment-setup") > all_sequence_roles.index("evidence"):
                errors.append("Experiment setup must appear before result evidence.")

        source_meta = manifest.get("source_fidelity", {})
        for field in ("source_pdf_sha256", "page_count"):
            if not source_meta.get(field):
                errors.append(f"Source fidelity is missing {field}.")
        if not manifest.get("source_title"):
            errors.append("Manifest is missing source_title.")
        if args.source:
            requested_source = Path(args.source).expanduser().resolve()
            if not requested_source.exists():
                errors.append(f"Requested source does not exist: {requested_source}")
            else:
                requested_hash = file_hash(requested_source)
                if clean_hash(source_meta.get("source_pdf_sha256")) != requested_hash:
                    errors.append("P0 source identity mismatch: output manifest does not belong to the requested source file.")
                if requested_source.suffix.lower() == ".pdf":
                    pdfinfo = command_path("pdfinfo")
                    if pdfinfo:
                        result = subprocess.run([pdfinfo, str(requested_source)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30)
                        match = re.search(r"^Pages:\s+(\d+)", result.stdout, re.M) if result.returncode == 0 else None
                        if match and source_meta.get("page_count") != int(match.group(1)):
                            errors.append("P0 source identity mismatch: manifest page_count differs from the requested PDF.")
        source_rel = source_meta.get("inventory_path")
        source_ids: set[str] = set()
        if not source_rel or not (root / str(source_rel)).exists():
            errors.append("Source inventory path is missing or invalid.")
        else:
            source_path = root / str(source_rel)
            source_inventory = load_json(source_path)
            if clean_hash(source_inventory.get("source_sha256")) != clean_hash(source_meta.get("source_pdf_sha256")):
                errors.append("Source inventory hash does not match manifest source_pdf_sha256.")
            if source_inventory.get("page_count") != source_meta.get("page_count"):
                errors.append("Source inventory page_count does not match manifest source fidelity.")
            if str(source_inventory.get("source_title", "")).strip() != str(manifest.get("source_title", "")).strip():
                errors.append("Source inventory title does not match manifest source_title.")
            blocks = source_inventory.get("all_main_text_blocks", [])
            source_ids = {str(block.get("source_id")) for block in blocks if block.get("source_id")}
            if clean_hash(source_meta.get("main_text_inventory_sha256")) != file_hash(source_path):
                errors.append("Source inventory hash is missing or incorrect.")

        argument_records = [*argument_map.get("argument_steps", []), *argument_map.get("evidence_route", [])]
        argument_record_ids: set[str] = set()
        for record in argument_records:
            if not isinstance(record, dict):
                errors.append("paper_argument_map records must be objects.")
                continue
            for field in ("id", "text", "source_ids", "final_item_ids"):
                if not record.get(field):
                    errors.append(f"paper_argument_map record is missing {field}.")
            record_id = str(record.get("id", ""))
            if record_id:
                argument_record_ids.add(record_id)
            for source_id in record.get("source_ids", []):
                if source_ids and str(source_id) not in source_ids:
                    errors.append(f"paper_argument_map references missing source id: {source_id}")
            for final_item_id in record.get("final_item_ids", []):
                if str(final_item_id) not in set(item_ids):
                    errors.append(f"paper_argument_map references missing final item id: {final_item_id}")
        opening_item_records = [item for item in items[:3] if item.get("sequence_role") in {"paper-overview", "argument-map", "overview-and-argument-map"}]
        covered_argument_ids = {str(value) for item in opening_item_records for value in item.get("covered_argument_step_ids", [])}
        if argument_record_ids - covered_argument_ids:
            errors.append(f"Opening overview/argument-map images do not visibly cover argument records: {sorted(argument_record_ids - covered_argument_ids)}")

        design = manifest.get("design_brief", {})
        for field in ("art_direction_thesis", "paper_motif", "motif_source_basis", "topic_specific_objects", "visual_direction", "typography_plan", "evidence_style", "forbidden_styles"):
            if not design.get(field):
                errors.append(f"Design brief is missing {field}.")
        target_ratio = str(manifest.get("target_aspect_ratio", ""))
        if target_ratio not in {"3:4", "4:3", "16:9", "custom"}:
            errors.append("Manifest must record target_aspect_ratio.")
        if target_ratio == "custom" and not manifest.get("custom_aspect_ratio_rationale"):
            errors.append("Custom aspect ratio requires a rationale.")

        declared_paths: set[str] = set()
        hashes: dict[str, str] = {}
        layout_counts: dict[str, int] = {}
        actual_ocr_records: dict[str, dict] = {}
        if args.strict:
            ocr_paths = [root / str(item.get("path", "")) for item in items if item.get("path")]
            actual_ocr, actual_ocr_error = run_actual_ocr([path for path in ocr_paths if path.exists()])
            if actual_ocr_error:
                errors.append(actual_ocr_error)
            elif actual_ocr is not None:
                actual_ocr_records = actual_ocr
        for index, item in enumerate(items, 1):
            for field in (
                "id",
                "learner_question",
                "one_sentence_answer",
                "source_ids",
                "layout_family",
                "path",
                "production_method",
                "sequence_role",
                "information_groups",
                "reader_takeaway",
                "teaching_units",
            ):
                if not item.get(field):
                    errors.append(f"Item {index} is missing {field}.")
            role = str(item.get("sequence_role", ""))
            groups = item.get("information_groups", [])
            required_groups = 1 if index == 1 else (3 if role in {"paper-overview", "argument-map", "overview-and-argument-map", "experiment-setup", "evidence", "recap"} else 2)
            if len(groups) < required_groups:
                errors.append(f"Item {index} has too few information groups for {role or 'its teaching role'}: {len(groups)}/{required_groups}.")
            if len(groups) > 4 or len({json.dumps(group, sort_keys=True, ensure_ascii=False) for group in groups}) != len(groups):
                errors.append(f"Item {index} information_groups must contain 1-4 distinct groups.")
            if index > 1 and len(item.get("scan_order", [])) < 3:
                errors.append(f"Item {index} needs a scan_order with at least three steps.")
            if len(set(map(str, item.get("scan_order", [])))) != len(item.get("scan_order", [])):
                errors.append(f"Item {index} scan_order contains repeated steps.")
            teaching_units = item.get("teaching_units", [])
            if len(teaching_units) < required_groups:
                errors.append(f"Item {index} has too few teaching_units: {len(teaching_units)}/{required_groups}.")
            for unit in teaching_units:
                for field in ("claim_or_concept", "explanation", "visual_anchor", "source_ids"):
                    if not unit.get(field):
                        errors.append(f"Item {index} teaching unit is missing {field}.")
            teaching_unit_names = [str(unit.get("claim_or_concept", "")) for unit in teaching_units]
            if len(set(teaching_unit_names)) != len(teaching_unit_names):
                errors.append(f"Item {index} repeats the same teaching unit.")
            if role == "evidence":
                evidence_objects = item.get("source_evidence_objects", [])
                if not evidence_objects:
                    errors.append(f"Evidence item {index} has no source_evidence_objects.")
                for evidence in evidence_objects:
                    for field in (
                        "evidence_id",
                        "source_id",
                        "source_page",
                        "object_type",
                        "reader_question",
                        "asset_path",
                        "asset_sha256",
                        "crop_bbox",
                        "display_width_px",
                        "display_height_px",
                        "annotated_regions",
                    ):
                        if evidence.get(field) in (None, "", []):
                            errors.append(f"Evidence item {index} source object is missing {field}.")
                    if evidence.get("readable_at_final_size") is not True:
                        errors.append(f"Evidence item {index} contains a source crop that is not readable at final size.")
                    evidence_asset = root / str(evidence.get("asset_path", ""))
                    if not evidence_asset.exists() or evidence_asset.suffix.lower() not in BITMAP_SUFFIXES:
                        errors.append(f"Evidence item {index} source crop is missing or not a bitmap: {evidence.get('asset_path')}")
                    elif clean_hash(evidence.get("asset_sha256")) != file_hash(evidence_asset):
                        errors.append(f"Evidence item {index} source crop hash is missing or incorrect.")
                    if evidence.get("display_width_px", 0) < 500 or evidence.get("display_height_px", 0) < 280:
                        errors.append(f"Evidence item {index} source crop is displayed too small for teaching.")
            if role == "worked-example":
                example = item.get("worked_example", {})
                for field in ("input", "stages", "output", "source_ids"):
                    if not example.get(field):
                        errors.append(f"Worked-example item {index} is missing {field}.")
                if isinstance(method_stage_count, int) and len(example.get("stages", [])) < method_stage_count:
                    errors.append(f"Worked-example item {index} does not cover the full method pipeline.")
            layout = str(item.get("layout_family", ""))
            layout_counts[layout] = layout_counts.get(layout, 0) + 1
            for source_id in item.get("source_ids", []):
                if source_ids and str(source_id) not in source_ids:
                    errors.append(f"Item {index} references missing source id: {source_id}")
            rel = str(item.get("path", ""))
            if rel and not Path(rel).name.startswith(f"{index:03d}-"):
                errors.append(f"Image filename does not preserve sequence number {index:03d}: {rel}")
            declared_paths.add(rel)
            asset = root / rel
            if asset.suffix.lower() not in BITMAP_SUFFIXES or not asset.exists():
                errors.append(f"Missing or invalid bitmap: {rel}")
                continue
            actual_hash = file_hash(asset)
            if clean_hash(item.get("asset_sha256")) != actual_hash:
                errors.append(f"Image hash is missing or incorrect: {rel}")
            if actual_hash in hashes and not item.get("reuse_reason"):
                errors.append(f"Duplicate bitmap without reuse reason: {hashes[actual_hash]} and {rel}")
            hashes[actual_hash] = rel
            if Image is not None:
                try:
                    with Image.open(asset) as image:
                        width, height = image.size
                    if max(width, height) < 1536 or min(width, height) < 864:
                        errors.append(f"Image resolution is too low: {rel} ({width}x{height})")
                    if item.get("width_px") != width or item.get("height_px") != height:
                        errors.append(f"Manifest dimensions are missing or incorrect: {rel}")
                    expected_ratios = {"3:4": 3 / 4, "4:3": 4 / 3, "16:9": 16 / 9}
                    if target_ratio in expected_ratios and abs((width / height) - expected_ratios[target_ratio]) > 0.06:
                        errors.append(f"Image aspect ratio does not match series target {target_ratio}: {rel} ({width}x{height})")
                except Exception:
                    errors.append(f"Unreadable image file: {rel}")
            if item.get("crop_checked") is not True or item.get("reviewer_status") != "passed":
                errors.append(f"Image has not passed visual review: {rel}")
            ocr_artifact_rel = str(item.get("ocr_artifact_path", ""))
            ocr_engine = str(item.get("ocr_engine", ""))
            if not ocr_artifact_rel or not ocr_engine:
                errors.append(f"Final image is missing OCR artifact provenance: {rel}")
                actual_ocr_text = ""
            else:
                ocr_artifact = root / ocr_artifact_rel
                if not ocr_artifact.exists():
                    errors.append(f"Final image OCR artifact does not exist: {ocr_artifact_rel}")
                    actual_ocr_text = ""
                else:
                    actual_ocr_text = ocr_artifact.read_text(encoding="utf-8", errors="replace")
                    if clean_hash(item.get("ocr_artifact_sha256")) != file_hash(ocr_artifact):
                        errors.append(f"Final image OCR artifact hash is missing or incorrect: {ocr_artifact_rel}")
            ocr_text = str(item.get("ocr_text", ""))
            if actual_ocr_text and ocr_text.strip() != actual_ocr_text.strip():
                errors.append(f"Manifest OCR text does not match the stored OCR artifact: {rel}")
            if not ocr_text:
                errors.append(f"Final image has no OCR text record: {rel}")
            if any(token in ocr_text for token in ("□", "�")):
                errors.append(f"Final image OCR contains missing/replacement glyphs: {rel}")
            actual_record = actual_ocr_records.get(str(asset.resolve()))
            actual_text = str(actual_record.get("text", "")) if actual_record else ""
            if args.strict and not actual_record:
                errors.append(f"Strict OCR did not return a record for final image: {rel}")
            if actual_record and actual_record.get("error"):
                errors.append(f"Strict OCR failed for final image {rel}: {actual_record.get('error')}")
            if actual_text and any(token in actual_text for token in ("□", "�")):
                errors.append(f"Strict OCR detected missing/replacement glyphs in final image: {rel}")
            actual_missing_labels = [str(label) for label in item.get("expected_labels", []) if str(label) and str(label) not in actual_text]
            if args.strict and actual_missing_labels:
                errors.append(f"Strict OCR could not find expected labels {actual_missing_labels[:5]} in final image: {rel}")
            if item.get("ocr_pass") is not True:
                errors.append(f"Final image has not passed full-page OCR review: {rel}")
            if not item.get("expected_labels"):
                errors.append(f"Final image has no expected_labels for OCR verification: {rel}")
            missing_anchors = [
                str(unit.get("visual_anchor"))
                for unit in teaching_units
                if unit.get("visual_anchor") and str(unit.get("visual_anchor")) not in ocr_text
            ]
            if missing_anchors:
                errors.append(f"Final image OCR does not contain teaching-unit visual anchors {missing_anchors[:5]}: {rel}")
            generated = item.get("production_method") in {"generated", "generated-composite"}
            if generated and index > 1:
                labels = item.get("diagram_labels", [])
                semantic_map = item.get("visual_semantic_map", [])
                integration = item.get("text_integration", {})
                relation_type = str(item.get("visual_relation_type", ""))
                if len(labels) < 3:
                    errors.append(f"Generated teaching image needs at least three explanatory diagram_labels: {rel}")
                missing_labels = [str(label) for label in labels if str(label) and str(label) not in ocr_text]
                if missing_labels:
                    errors.append(f"Generated teaching image OCR is missing diagram labels {missing_labels[:5]}: {rel}")
                if len(semantic_map) < 2:
                    errors.append(f"Generated teaching image lacks a visual_semantic_map: {rel}")
                if relation_type not in {"causal", "spatial", "comparative", "sequential", "quantitative", "hierarchical"}:
                    errors.append(f"Generated teaching image does not declare a real teaching relationship: {rel}")
                relation_labels = [str(label) for label in item.get("visual_relation_labels", [])]
                if len(relation_labels) < 2 or any(label not in ocr_text for label in relation_labels):
                    errors.append(f"Generated teaching image visual relationship is not anchored by OCR-visible labels: {rel}")
                if integration.get("mode") not in {"in-model", "reserved-zone-overlay", "source-annotation"}:
                    errors.append(f"Generated teaching image has no valid text-integration mode: {rel}")
                if integration.get("planned_before_generation") is not True:
                    errors.append(f"Generated teaching image labels were not planned before generation: {rel}")
                if integration.get("native_resolution_composite") is not True:
                    errors.append(f"Generated teaching image text was not composed at native output resolution: {rel}")
                if integration.get("mode") == "reserved-zone-overlay" and integration.get("label_zones_planned") is not True:
                    errors.append(f"Reserved-zone overlay lacks planned label zones: {rel}")
                visual_language = str(item.get("in_image_text_language", "")).lower()
                if reader_language.lower().startswith("zh") and not any(token in visual_language for token in ("zh", "chinese", "中文")):
                    errors.append(f"Chinese-reader teaching image is not recorded as Chinese-dominant: {rel}")
            if item.get("production_method") in {"generated", "generated-composite"} and not item.get("model_name"):
                errors.append(f"Generated image does not record the real model name: {rel}")
            if item.get("claim_role") in {"source_claim_to_verify", "supported_conclusion"}:
                source_cue = str(item.get("visible_source_cue", "")).strip()
                ocr_text = str(item.get("ocr_text", ""))
                if not source_cue or item.get("source_cue_ocr_pass") is not True or source_cue not in ocr_text:
                    errors.append(f"Factual image lacks a reader-visible, OCR-verified source cue: {rel}")

        if count and layout_counts:
            dominant_layout, dominant_count = max(layout_counts.items(), key=lambda entry: entry[1])
            if dominant_count / count > 0.60 and not manifest.get("layout_repetition_rationale"):
                errors.append(f"One image composition dominates the series without rationale: {dominant_layout} {dominant_count}/{count}")
            if count >= 11 and len(layout_counts) < 4:
                errors.append(f"Medium/detailed image series needs at least four composition families: {len(layout_counts)}.")
        layout_sequence = [str(item.get("layout_family", "")) for item in items]
        streak = 1
        for index in range(1, len(layout_sequence)):
            if layout_sequence[index] == layout_sequence[index - 1]:
                streak += 1
                if streak > 3:
                    errors.append(f"The same image composition repeats more than three times consecutively near item {index + 1}: {layout_sequence[index]}")
                    break
            else:
                streak = 1

        final_dir = root / "assets" / "images"
        packaged = {
            str(path.relative_to(root))
            for path in final_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in BITMAP_SUFFIXES
        } if final_dir.exists() else set()
        orphan = sorted(packaged - declared_paths)
        if orphan:
            errors.append(f"Orphan images found in final package: {orphan[:8]}")

        contact_sheet = root / str(manifest.get("contact_sheet_path", ""))
        if not manifest.get("contact_sheet_path") or not contact_sheet.exists():
            errors.append("Missing full-series contact sheet.")
        elif Image is not None:
            try:
                with Image.open(contact_sheet) as sheet:
                    sheet.verify()
            except Exception:
                errors.append("Full-series contact sheet is not a valid image.")
        exports = manifest.get("exports", {})
        album_rel = exports.get("album_pdf_path")
        if args.require_pdf or album_rel:
            if not album_rel:
                errors.append("Image series is missing exports.album_pdf_path.")
            else:
                album_path = root / str(album_rel)
                ordered_image_paths = [root / str(item.get("path", "")) for item in items]
                errors.extend(validate_album_pdf(album_path, count, target_ratio, ordered_image_paths, root / "qa" / "album-render-check"))
                if album_path.exists() and clean_hash(exports.get("album_pdf_sha256")) != file_hash(album_path):
                    errors.append("Album PDF hash is missing or incorrect.")
                if exports.get("album_pdf_page_count") != count:
                    errors.append("Manifest album_pdf_page_count does not match image count.")
        claims = manifest.get("claim_evidence_map", [])
        expected_claim_ids = {
            str(item.get("inventory_id"))
            for item in manifest.get("central_claim_coverage", [])
            if item.get("status") == "covered" and item.get("inventory_id")
        }
        mapped_claim_ids = {str(claim.get("claim_id")) for claim in claims if claim.get("claim_id")}
        if expected_claim_ids - mapped_claim_ids:
            errors.append(f"Covered central claims are missing from claim_evidence_map: {sorted(expected_claim_ids - mapped_claim_ids)}")
        visible_ocr = "\n".join(str(item.get("ocr_text", "")) for item in items)
        for claim in claims:
            for field in (
                "claim_id",
                "claim_role",
                "claim_wording",
                "source_ids",
                "comparison_baseline",
                "comparison_validity",
                "metric_or_dimension",
                "direction_or_value",
                "evidence_items",
                "evidence_strength",
                "limitation",
            ):
                if not claim.get(field):
                    errors.append(f"Claim evidence entry is missing {field}.")
            wording = str(claim.get("claim_wording", ""))
            if wording and wording not in visible_ocr:
                errors.append(f"Claim wording is not visible in final image OCR: {wording[:120]}")
            if claim.get("comparison_validity") not in {"controlled", "descriptive", "cross-benchmark", "not-applicable"}:
                errors.append(f"Claim has invalid comparison_validity: {claim.get('comparison_validity')}")
            if re.search(r"(?:证明|证实|验证了|击败|打败|优于|超越|导致|带来|使得|归因于|显著提高|提升了|proves?|demonstrates?|validates?|beats?|outperforms?|causes?|leads?\s+to|improves?\s+by)", wording, re.I) and claim.get("comparison_validity") != "controlled":
                errors.append(f"Overstated claim without a controlled comparison: {wording[:120]}")
            if claim.get("claim_role") == "supported_conclusion":
                supporting = [item for item in claim.get("evidence_items", []) if item.get("supports_vs_illustrates") == "supports" and item.get("evidence_kind") != "generated_visual"]
                if not supporting:
                    errors.append("A supported conclusion has no non-generated supporting evidence.")
        qa = manifest.get("qa", {})
        for field in (
            "all_images_reviewed",
            "contact_sheet_checked",
            "public_copy_clean",
            "evidence_links_checked",
            "aesthetic_review_passed",
            "visual_variety_checked",
            "narrative_continuity_checked",
            "overview_sequence_checked",
            "in_image_explanation_checked",
            "information_density_checked",
            "album_pdf_checked",
            "glyph_integrity_checked",
            "template_residue_checked",
            "source_crop_readability_checked",
        ):
            if qa.get(field) is not True:
                errors.append(f"Image-series QA has not passed {field}.")
        adversarial_passes = qa.get("adversarial_passes", [])
        if len(adversarial_passes) < 3 or not has_review_lenses(adversarial_passes):
            errors.append("Image-series QA must record visual, information-completeness, and narrative/novice reviews.")
        qa_report_path = root / "qa" / "qa-report.json"
        qa_report = load_json(qa_report_path) if qa_report_path.exists() else {}
        if not qa_report:
            errors.append("Missing or invalid qa/qa-report.json.")
        else:
            if qa_report.get("final_status") not in {"passed", "clean"}:
                errors.append("QA report final_status is not passed/clean.")
            if qa_report.get("unresolved_blockers") or qa_report.get("remaining_errors"):
                errors.append("QA report still contains unresolved blockers or errors.")
            item_reviews = qa_report.get("item_reviews", [])
            if len(item_reviews) != count:
                errors.append(f"QA report needs one item_reviews entry per image: {len(item_reviews)}/{count}.")
            reviewed_ids = {str(review.get("item_id")) for review in item_reviews if isinstance(review, dict)}
            if reviewed_ids != set(item_ids):
                errors.append("QA item review ids do not match the final image ids.")
            finding_counts: dict[str, int] = {}
            item_by_id = {str(item.get("id")): item for item in items if item.get("id")}
            for review in item_reviews:
                for field in (
                    "item_id",
                    "visual_status",
                    "information_status",
                    "narrative_status",
                    "findings",
                    "fixes",
                    "review_evidence_path",
                    "reviewed_asset_sha256",
                    "final_status",
                ):
                    if review.get(field) in (None, "", []):
                        errors.append(f"QA item review is missing {field}: {review.get('item_id', '[unknown]')}")
                for status_field in ("visual_status", "information_status", "narrative_status", "final_status"):
                    if review.get(status_field) not in {"passed", "fixed"}:
                        errors.append(f"QA item review has invalid {status_field}: {review.get('item_id', '[unknown]')}")
                findings = re.sub(r"\s+", " ", str(review.get("findings", "")).strip().lower())
                if len(findings) < 20:
                    errors.append(f"QA item review findings are too generic: {review.get('item_id', '[unknown]')}")
                if findings:
                    finding_counts[findings] = finding_counts.get(findings, 0) + 1
                evidence_path = root / str(review.get("review_evidence_path", ""))
                if not evidence_path.exists():
                    errors.append(f"QA item review evidence path does not exist: {review.get('review_evidence_path')}")
                item = item_by_id.get(str(review.get("item_id")), {})
                reviewed_hash = clean_hash(review.get("reviewed_asset_sha256"))
                if reviewed_hash:
                    if reviewed_hash != clean_hash(item.get("asset_sha256")):
                        errors.append(f"QA item review asset hash does not match final image: {review.get('item_id')}")
            repeated_findings = [text for text, repetitions in finding_counts.items() if repetitions > 2]
            if repeated_findings:
                errors.append("QA item reviews reuse generic findings across more than two images.")

    if args.strict:
        errors.extend(warnings)
        warnings = []
    else:
        warnings.extend(errors)
        errors = []

    print(json.dumps({"errors": errors, "warnings": warnings, "summary": {"errors": len(errors), "warnings": len(warnings)}}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
