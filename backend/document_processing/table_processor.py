
def clean_cell(value):
    """Clean an individual table cell."""

    if value is None:
        return ""

    return " ".join(str(value).split())


def clean_table(rows):
    """Clean extracted table rows while preserving their structure."""

    if not rows:
        return []

    # Clean every cell
    cleaned_rows = [
        [clean_cell(cell) for cell in row]
        for row in rows
    ]

    # Remove completely empty rows
    cleaned_rows = [
        row for row in cleaned_rows
        if any(cell for cell in row)
    ]

    if not cleaned_rows:
        return []

    # Remove columns that are completely empty
    column_count = max(len(row) for row in cleaned_rows)

    cleaned_rows = [
        row + [""] * (column_count - len(row))
        for row in cleaned_rows
    ]

    non_empty_columns = [
        index
        for index in range(column_count)
        if any(row[index] for row in cleaned_rows)
    ]

    cleaned_rows = [
        [row[index] for index in non_empty_columns]
        for row in cleaned_rows
    ]

    return cleaned_rows


def table_to_text(rows):
    """Convert a cleaned table into retrieval-friendly text."""

    if not rows:
        return ""

    headers = rows[0]
    text_lines = []

    for row in rows[1:]:

        details = []

        for header, value in zip(headers, row):

            if header and value:
                details.append(f"{header}: {value}")

            elif value:
                details.append(value)

        if details:
            text_lines.append("; ".join(details))

    return "\n".join(text_lines)


if __name__ == "__main__":

    sample_table = [
        ["", "Hadoop", "", "RDBMS", ""],
        ["", "", "", "", ""],
        ["", "Highly scalable", "", "Less scalable", ""],
        ["", "Supports big data", "", "Supports structured data", ""]
    ]

    cleaned = clean_table(sample_table)

    print("CLEANED TABLE:")
    for row in cleaned:
        print(row)

    print("\nTABLE AS TEXT:")
    print(table_to_text(cleaned))
