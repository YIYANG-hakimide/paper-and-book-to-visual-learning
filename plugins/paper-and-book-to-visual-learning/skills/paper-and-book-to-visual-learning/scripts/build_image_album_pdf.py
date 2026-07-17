#!/usr/bin/env python3
"""Package an ordered explainer-image series as a one-image-per-page PDF."""

from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

BITMAP_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a page-matched album PDF from numbered images.")
    parser.add_argument("image_dir")
    parser.add_argument("output_pdf")
    parser.add_argument("--title", default="Paper Learning Album")
    parser.add_argument("--jpeg-quality", type=int, default=90, help="JPEG quality used inside the PDF when Pillow is available")
    args = parser.parse_args()

    image_dir = Path(args.image_dir).expanduser().resolve()
    output_pdf = Path(args.output_pdf).expanduser().resolve()
    images = sorted(path for path in image_dir.iterdir() if path.is_file() and path.suffix.lower() in BITMAP_SUFFIXES)
    if not images:
        raise SystemExit(f"No numbered bitmap images found in {image_dir}")

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    try:
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas

        document = canvas.Canvas(str(output_pdf), pageCompression=1)
        document.setTitle(args.title)
        for path in images:
            reader_source: object = str(path)
            try:
                from PIL import Image

                buffer = io.BytesIO()
                with Image.open(path) as image:
                    flattened = image.convert("RGB")
                    flattened.save(buffer, "JPEG", quality=max(70, min(98, args.jpeg_quality)), optimize=True)
                buffer.seek(0)
                reader_source = buffer
            except ImportError:
                pass
            reader = ImageReader(reader_source)
            width_px, height_px = reader.getSize()
            if width_px <= 0 or height_px <= 0:
                raise SystemExit(f"Invalid image dimensions: {path}")
            page_width = 960.0 if width_px >= height_px else 600.0
            page_height = page_width * height_px / width_px
            document.setPageSize((page_width, page_height))
            document.drawImage(reader, 0, 0, width=page_width, height=page_height, preserveAspectRatio=True, mask="auto")
            document.showPage()
        document.save()
    except ImportError:
        try:
            from PIL import Image
        except ImportError as exc:
            raise SystemExit("Install reportlab or Pillow, or use the bundled Python reported by preflight.") from exc
        pages = []
        for path in images:
            with Image.open(path) as image:
                pages.append(image.convert("RGB"))
        first, *rest = pages
        first.save(output_pdf, "PDF", save_all=True, append_images=rest, resolution=144.0, title=args.title)

    print(json.dumps({"output_pdf": str(output_pdf), "page_count": len(images)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
