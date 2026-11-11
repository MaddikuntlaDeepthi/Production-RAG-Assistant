
import pymupdf
from pathlib import Path


# --------------------------------------------------
# 1. CALCULATE DISTANCE BETWEEN TWO RECTANGLES
# --------------------------------------------------

def calculate_rect_distance(rect1, rect2):
    """
    Calculate the minimum distance between two rectangles.

    Returns zero if the rectangles overlap or touch.
    """

    horizontal_gap = max(
        rect1.x0 - rect2.x1,
        rect2.x0 - rect1.x1,
        0
    )

    vertical_gap = max(
        rect1.y0 - rect2.y1,
        rect2.y0 - rect1.y1,
        0
    )

    return (
        horizontal_gap ** 2 + vertical_gap ** 2
    ) ** 0.5


# --------------------------------------------------
# 2. GROUP RELATED VECTOR DRAWINGS
# --------------------------------------------------

def group_vector_drawings(
    pdf_path,
    page_number,
    distance_threshold=15,
    min_group_area=500
):
    """
    Group nearby vector drawings using their
    bounding-box positions.

    Page numbering starts from 1.
    """

    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(
            "Only PDF files are supported."
        )

    with pymupdf.open(pdf_path) as document:

        if page_number < 1 or page_number > len(document):
            raise ValueError(
                f"Invalid page number. "
                f"PDF has {len(document)} pages."
            )

        page = document[page_number - 1]

        drawings = page.get_drawings()

        rectangles = []

        # Extract valid drawing rectangles
        for drawing in drawings:

            rect = pymupdf.Rect(drawing["rect"])

            if rect.is_empty or rect.is_infinite:
                continue

            rectangles.append(rect)

        print(
            f"\nPage {page_number}: "
            f"{len(rectangles)} valid vector drawings"
        )

        if not rectangles:
            return []

        # --------------------------------------------------
        # 3. INITIALIZE GROUPS
        # --------------------------------------------------

        parent = list(range(len(rectangles)))

        def find(index):

            if parent[index] != index:

                parent[index] = find(parent[index])

            return parent[index]

        def union(index1, index2):

            root1 = find(index1)
            root2 = find(index2)

            if root1 != root2:

                parent[root2] = root1

        # --------------------------------------------------
        # 4. MERGE NEARBY DRAWINGS
        # --------------------------------------------------

        for i in range(len(rectangles)):

            for j in range(i + 1, len(rectangles)):

                distance = calculate_rect_distance(
                    rectangles[i],
                    rectangles[j]
                )

                if distance <= distance_threshold:

                    union(i, j)

        # --------------------------------------------------
        # 5. CREATE GROUP BOUNDING BOXES
        # --------------------------------------------------

        grouped_rectangles = {}

        for index, rect in enumerate(rectangles):

            root = find(index)

            if root not in grouped_rectangles:

                grouped_rectangles[root] = {
                    "rect": pymupdf.Rect(rect),
                    "element_count": 1
                }

            else:

                group = grouped_rectangles[root]

                group["rect"] |= rect

                group["element_count"] += 1

        # --------------------------------------------------
        # 6. FILTER AND PREPARE RESULTS
        # --------------------------------------------------

        results = []

        for group in grouped_rectangles.values():

            rect = group["rect"]

            area = rect.get_area()

            if area < min_group_area:
                continue

            results.append({

                "page": page_number,

                "bbox": tuple(rect),

                "area": area,

                "element_count": group["element_count"]

            })

        # Sort largest groups first
        results.sort(
            key=lambda item: item["area"],
            reverse=True
        )

        return results


# --------------------------------------------------
# 7. DISPLAY GROUPING RESULTS
# --------------------------------------------------

def display_grouping_results(groups):

    print("\n" + "=" * 60)
    print("VECTOR GROUPING RESULTS")
    print("=" * 60)

    print(
        f"\nMeaningful groups detected: {len(groups)}"
    )

    for index, group in enumerate(groups, start=1):

        print(f"\nGroup {index}")

        print(f"Page: {group['page']}")

        print(
            f"Elements combined: "
            f"{group['element_count']}"
        )

        print(
            f"Bounding box: {group['bbox']}"
        )

        print(
            f"Area: {group['area']:.2f}"
        )


# --------------------------------------------------
# 8. CROP GROUPED VECTOR REGIONS
# --------------------------------------------------

def crop_vector_groups(
    pdf_path,
    page_number,
    output_dir="data/processed/diagrams/vector_groups",
    dpi=200,
    distance_threshold=15,
    min_group_area=500
):
    """
    Crop each detected vector group from its PDF page
    and save it as a PNG image.
    """

    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # Detect and group vector drawings
    groups = group_vector_drawings(
        pdf_path,
        page_number,
        distance_threshold=distance_threshold,
        min_group_area=min_group_area
    )

    if not groups:

        print(
            f"No suitable vector groups found on page {page_number}."
        )

        return []

    saved_images = []

    with pymupdf.open(pdf_path) as document:

        page = document[page_number - 1]

        for index, group in enumerate(groups, start=1):

            rect = pymupdf.Rect(group["bbox"])

            # Render the grouped region
            pixmap = page.get_pixmap(
                dpi=dpi,
                clip=rect,
                alpha=False
            )

            image_name = (
                f"{pdf_path.stem}_page_{page_number}"
                f"_group_{index}.png"
            )

            image_path = output_dir / image_name

            pixmap.save(str(image_path))

            saved_images.append({

                "page": page_number,

                "group_number": index,

                "element_count": group["element_count"],

                "bbox": group["bbox"],

                "image_path": str(image_path)

            })

            print(
                f"\nGroup {index} cropped successfully."
            )

            print(
                f"Elements: {group['element_count']}"
            )

            print(
                f"Saved image: {image_path}"
            )

    return saved_images


# --------------------------------------------------
# 9. MAIN TEST
# --------------------------------------------------

if __name__ == "__main__":

    pdf_path = "data/raw/sample.pdf"

    test_pages = [7, 8, 9]

    print("\n" + "=" * 60)
    print("PRODUCTION RAG - VECTOR GROUPING AND CROPPING")
    print("=" * 60)

    total_crops = 0

    for page_number in test_pages:

        print("\n" + "#" * 60)
        print(f"PROCESSING PAGE {page_number}")
        print("#" * 60)

        groups = group_vector_drawings(
            pdf_path,
            page_number,
            distance_threshold=15,
            min_group_area=500
        )

        display_grouping_results(groups)

        print("\nCROPPING GROUPED REGIONS...")

        saved_images = crop_vector_groups(
            pdf_path,
            page_number,
            distance_threshold=15,
            min_group_area=500,
            dpi=200
        )

        total_crops += len(saved_images)

    print("\n" + "=" * 60)
    print("VECTOR GROUPING AND CROPPING COMPLETED")
    print("=" * 60)

    print(f"Total images created: {total_crops}")

    print(
        "Output folder: "
        "data/processed/diagrams/vector_groups"
    )

