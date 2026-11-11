
import pymupdf
from pathlib import Path


# --------------------------------------------------
# 1. DETECT VISUAL REGIONS
# --------------------------------------------------

def detect_visual_regions(pdf_path, page_number):
    """
    Detect embedded images and vector drawings
    on a specific PDF page.

    page_number starts from 1.
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported.")

    with pymupdf.open(pdf_path) as document:

        if page_number < 1 or page_number > len(document):
            raise ValueError(
                f"Invalid page number. PDF has {len(document)} pages."
            )

        page = document[page_number - 1]

        regions = []

        # ------------------------------------------
        # Detect embedded images
        # ------------------------------------------

        images = page.get_image_info(xrefs=True)

        for image in images:

            rect = pymupdf.Rect(image["bbox"])

            if rect.is_empty or rect.is_infinite:
                continue

            regions.append({
                "type": "image",
                "bbox": tuple(rect),
                "area": rect.get_area()
            })

        # ------------------------------------------
        # Detect vector drawings
        # ------------------------------------------

        drawings = page.get_drawings()

        for drawing in drawings:

            rect = pymupdf.Rect(drawing["rect"])

            if rect.is_empty or rect.is_infinite:
                continue

            regions.append({
                "type": "drawing",
                "bbox": tuple(rect),
                "area": rect.get_area()
            })

        return regions


# --------------------------------------------------
# 2. CROP DETECTED VISUAL REGIONS
# --------------------------------------------------

def crop_visual_regions(
    pdf_path,
    page_number,
    output_dir="data/processed/diagrams",
    dpi=200
):
    """
    Crop detected visual regions from a PDF page
    and save them as separate PNG images.
    """

    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    regions = detect_visual_regions(
        pdf_path,
        page_number
    )

    cropped_images = []

    with pymupdf.open(pdf_path) as document:

        page = document[page_number - 1]

        for index, region in enumerate(regions, start=1):

            rect = pymupdf.Rect(region["bbox"])

            # Render only the detected region
            pixmap = page.get_pixmap(
                dpi=dpi,
                clip=rect,
                alpha=False
            )

            image_name = (
                f"{pdf_path.stem}_page_{page_number}"
                f"_region_{index}.png"
            )

            image_path = output_dir / image_name

            pixmap.save(str(image_path))

            cropped_images.append({
                "document": pdf_path.name,
                "page": page_number,
                "region_number": index,
                "region_type": region["type"],
                "image_path": str(image_path)
            })

    return cropped_images


# --------------------------------------------------
# 3. MAIN TEST
# --------------------------------------------------

if __name__ == "__main__":

    pdf_path = "data/raw/sample.pdf"

    page_number = 6

    print("\nDETECTING VISUAL REGIONS...\n")

    regions = detect_visual_regions(
        pdf_path,
        page_number
    )

    print(f"Page number: {page_number}")
    print(f"Total regions detected: {len(regions)}")

    for index, region in enumerate(regions, start=1):

        print(f"\nRegion {index}")
        print(f"Type: {region['type']}")
        print(f"Bounding box: {region['bbox']}")
        print(f"Area: {region['area']:.2f}")

    print("\nCROPPING VISUAL REGIONS...\n")

    cropped_images = crop_visual_regions(
        pdf_path,
        page_number
    )

    if cropped_images:

        for image in cropped_images:

            print(f"Document: {image['document']}")
            print(f"Page: {image['page']}")
            print(f"Type: {image['region_type']}")
            print(f"Saved: {image['image_path']}")
            print("-" * 50)

        print("\nDIAGRAM CROPPING COMPLETED")

    else:

        print("No visual regions found on this page.")

