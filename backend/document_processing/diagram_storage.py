
import json
from pathlib import Path


# --------------------------------------------------
# 1. SAVE DIAGRAM DESCRIPTIONS
# --------------------------------------------------

def save_diagram_descriptions(
    diagram_results,
    output_path="data/processed/diagram_descriptions.json"
):
    """
    Save diagram descriptions and metadata
    into a JSON file.
    """

    output_path = Path(output_path)

    # Create the output folder if it doesn't exist
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Load existing records if the file exists
    if output_path.exists():

        with open(output_path, "r", encoding="utf-8") as file:
            existing_data = json.load(file)

    else:
        existing_data = []

    # Add new results without duplicating the same diagram
    for result in diagram_results:

        record = {
            "document": result["document"],
            "page": result["page"],
            "region_number": result["region_number"],
            "image_path": result["image_path"],
            "description": result["description"]
        }

        already_exists = any(
            item["document"] == record["document"]
            and item["page"] == record["page"]
            and item["region_number"] == record["region_number"]
            for item in existing_data
        )

        if already_exists:
            existing_data = [
                item for item in existing_data
                if not (
                    item["document"] == record["document"]
                    and item["page"] == record["page"]
                    and item["region_number"] == record["region_number"]
                )
            ]

        existing_data.append(record)

    # Save JSON data
    with open(output_path, "w", encoding="utf-8") as file:

        json.dump(
            existing_data,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("\nDIAGRAM DATA SAVED SUCCESSFULLY")
    print(f"Total stored diagrams: {len(existing_data)}")
    print(f"Saved location: {output_path}")


# --------------------------------------------------
# 2. LOAD DIAGRAM DESCRIPTIONS
# --------------------------------------------------

def load_diagram_descriptions(
    input_path="data/processed/diagram_descriptions.json"
):
    """
    Load previously saved diagram descriptions.
    """

    input_path = Path(input_path)

    if not input_path.exists():
        raise FileNotFoundError(
            f"Diagram storage file not found: {input_path}"
        )

    with open(input_path, "r", encoding="utf-8") as file:

        data = json.load(file)

    return data


# --------------------------------------------------
# 3. MAIN TEST
# --------------------------------------------------

if __name__ == "__main__":

    print("\nTESTING DIAGRAM STORAGE\n")

    sample_data = [
        {
            "document": "sample.pdf",
            "page": 6,
            "region_number": 1,
            "image_path": (
                "data/processed/diagrams/"
                "sample_page_6_region_1.png"
            ),
            "description": (
                "The diagram illustrates HDFS architecture "
                "with a NameNode and multiple DataNodes."
            )
        }
    ]

    # Save sample data
    save_diagram_descriptions(sample_data)

    # Load saved data
    loaded_data = load_diagram_descriptions()

    print("\nLOADED DIAGRAM DATA\n")

    for item in loaded_data:

        print(f"Document: {item['document']}")
        print(f"Page: {item['page']}")
        print(f"Description: {item['description']}")
