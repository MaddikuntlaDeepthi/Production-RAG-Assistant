
import base64
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

from backend.document_processing.diagram_detector import (
    crop_visual_regions
)

from backend.document_processing.diagram_storage import (
    save_diagram_descriptions
)


# ==================================================
# 1. GROQ CONFIGURATION
# ==================================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

client = None

if api_key:
    client = Groq(
        api_key=api_key,
        timeout=30.0,
        max_retries=0
    )


def get_groq_client():
    """Initialize Groq client when required."""

    if client is None:
        raise RuntimeError(
            "GROQ_API_KEY not found in .env file"
        )

    return client


# ==================================================
# 2. IMAGE ENCODING
# ==================================================

def encode_image(image_path):

    with open(image_path, "rb") as image_file:

        encoded = base64.b64encode(
            image_file.read()
        ).decode("utf-8")

    return encoded


# ==================================================
# 3. DIAGRAM ANALYSIS USING GROQ
# ==================================================

def analyze_diagram(image_path):

    image_path = Path(image_path)

    base64_image = encode_image(image_path)

    groq_client = get_groq_client()

    response = groq_client.chat.completions.create(

        model="qwen/qwen3.8-27b",

        messages=[
            {
                "role": "user",

                "content": [

                    {
                        "type": "text",

                        "text": """
Analyze this diagram carefully.

Explain:

1. Diagram title or subject.
2. Main components.
3. Purpose of each component.
4. Connections between components.
5. Overall workflow.

Identify visible labels and relationships.

Do not invent missing information.
Mention anything unclear.

Keep the explanation clear and concise.
"""
                    },

                    {
                        "type": "image_url",

                        "image_url": {
                            "url": (
                                "data:image/png;base64,"
                                + base64_image
                            )
                        }
                    }
                ]
            }
        ],

        temperature=0,

        max_completion_tokens=400
    )

    description = response.choices[0].message.content

    if not description:
        raise ValueError(
            "Groq returned an empty diagram description."
        )

    return description


# ==================================================
# 4. SAFE DIAGRAM ANALYSIS WITH RETRIES
# ==================================================

def analyze_diagram_safely(image_path):

    max_attempts = 3

    for attempt in range(1, max_attempts + 1):

        try:

            description = analyze_diagram(image_path)

            return description, "success"

        except Exception as error:

            error_name = type(error).__name__

            status_code = getattr(
                error,
                "status_code",
                None
            )

            print(
                f"\nDiagram analysis failed: {error}"
            )

            # Do not retry rate-limit errors.

            if status_code == 429:

                print(
                    "Groq rate limit reached. "
                    "Skipping this diagram."
                )

                return (
                    "Diagram analysis unavailable: "
                    "Groq API rate limit reached.",
                    "skipped_rate_limit"
                )

            # Retry temporary connection errors.

            is_connection_error = (
                "Connection" in error_name
                or "Timeout" in error_name
            )

            if (
                is_connection_error
                and attempt < max_attempts
            ):

                delay = attempt * 3

                print(
                    f"Retrying in {delay} seconds "
                    f"(attempt {attempt + 1}/{max_attempts})..."
                )

                time.sleep(delay)

                continue

            print(
                "Skipping this diagram and continuing."
            )

            return (
                f"Diagram analysis unavailable: {error_name}.",
                "failed"
            )

    return (
        "Diagram analysis unavailable after retries.",
        "failed"
    )


# ==================================================
# 5. PROCESS ALL DIAGRAMS ON A PDF PAGE
# ==================================================

def process_pdf_diagrams(pdf_path, page_number):

    print(
        "\nDETECTING AND CROPPING DIAGRAMS...\n"
    )

    cropped_images = crop_visual_regions(
        pdf_path,
        page_number
    )

    if not cropped_images:

        print("No visual regions found.")

        return []

    results = []

    for image in cropped_images:

        print(
            f"\nAnalyzing: {image['image_path']}"
        )

        description, status = analyze_diagram_safely(
            image["image_path"]
        )

        result = {

            "document": image["document"],

            "page": image["page"],

            "region_number": image["region_number"],

            "image_path": image["image_path"],

            "description": description,

            "analysis_status": status
        }

        results.append(result)

        print("\nDIAGRAM DESCRIPTION:")

        print(description)

        print("\nANALYSIS STATUS:", status)

        print("\n" + "=" * 60)

    return results


# ==================================================
# 6. COMPLETE DIAGRAM PIPELINE
# ==================================================

def run_diagram_pipeline(pdf_path, page_number):

    print("\n" + "=" * 60)

    print("PRODUCTION RAG - DIAGRAM PROCESSING")

    print("=" * 60)

    results = process_pdf_diagrams(
        pdf_path,
        page_number
    )

    if results:

        save_diagram_descriptions(results)

        successful = sum(
            1
            for item in results
            if item["analysis_status"] == "success"
        )

        failed = len(results) - successful

        print("\nDIAGRAM PROCESSING COMPLETED")

        print("Total regions:", len(results))

        print("Successfully analyzed:", successful)

        print("Skipped or failed:", failed)

    else:

        print("\nNo diagrams were processed.")

    return results


# ==================================================
# 7. MAIN TEST
# ==================================================

if __name__ == "__main__":

    pdf_path = "data/raw/sample.pdf"

    page_number = 6

    run_diagram_pipeline(
        pdf_path,
        page_number
    )

    print(
        "\nCOMPLETE DIAGRAM PIPELINE FINISHED"
    )
