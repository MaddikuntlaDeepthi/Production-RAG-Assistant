
import pymupdf
from pathlib import Path

from backend.document_processing.diagram_detector import (
    detect_visual_regions
)


# --------------------------------------------------
# 1. SCAN ALL PDF PAGES
# --------------------------------------------------

def scan_pdf_visuals(pdf_path):

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(
            "Only PDF files are supported."
        )

    print("\n" + "=" * 60)
    print("PDF VISUAL SCANNER")
    print("=" * 60)

    with pymupdf.open(pdf_path) as document:
        total_pages = len(document)

    print(f"\nDocument: {pdf_path.name}")
    print(f"Total pages: {total_pages}")

    scan_results = []

    # --------------------------------------------------
    # 2. INSPECT EACH PAGE
    # --------------------------------------------------

    for page_number in range(1, total_pages + 1):

        regions = detect_visual_regions(
            pdf_path,
            page_number
        )

        image_count = sum(
            1 for region in regions
            if region["type"] == "image"
        )

        drawing_count = sum(
            1 for region in regions
            if region["type"] == "drawing"
        )

        page_result = {
            "document": pdf_path.name,
            "page": page_number,
            "total_regions": len(regions),
            "images": image_count,
            "drawings": drawing_count,
            "regions": regions
        }

        scan_results.append(page_result)

        print(f"\nPage {page_number}")
        print("-" * 40)

        print(f"Total visual regions: {len(regions)}")
        print(f"Embedded images: {image_count}")
        print(f"Vector drawings: {drawing_count}")

        # Display detected region details
        for index, region in enumerate(regions, start=1):

            print(
                f"Region {index}: "
                f"Type={region['type']}, "
                f"Area={region['area']:.2f}"
            )

    return scan_results


# --------------------------------------------------
# 3. SCAN SUMMARY
# --------------------------------------------------

def display_scan_summary(scan_results):

    pages_with_visuals = [
        page for page in scan_results
        if page["total_regions"] > 0
    ]

    total_images = sum(
        page["images"] for page in scan_results
    )

    total_drawings = sum(
        page["drawings"] for page in scan_results
    )

    print("\n" + "=" * 60)
    print("PDF SCAN SUMMARY")
    print("=" * 60)

    print(
        f"Total pages scanned: {len(scan_results)}"
    )

    print(
        f"Pages containing visual regions: "
        f"{len(pages_with_visuals)}"
    )

    print(f"Total embedded images: {total_images}")
    print(f"Total vector drawings: {total_drawings}")

    print("\nPages with visual regions:")

    for page in pages_with_visuals:

        print(
            f"Page {page['page']}: "
            f"{page['total_regions']} regions "
            f"({page['images']} images, "
            f"{page['drawings']} drawings)"
        )


# --------------------------------------------------
# 4. MAIN TEST
# --------------------------------------------------

if __name__ == "__main__":

    pdf_path = "data/raw/sample.pdf"

    results = scan_pdf_visuals(pdf_path)

    display_scan_summary(results)

    print("\nPDF VISUAL SCANNING COMPLETED")
