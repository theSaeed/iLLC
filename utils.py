import csv


def extract_names(csv_file_path):
    """
    Reads a CSV file and returns the non-empty values from its name column.
    """
    with open(csv_file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or 'name' not in reader.fieldnames:
            raise ValueError(f"{csv_file_path} must contain a 'name' column")

        return [
            name
            for row in reader
            if (name := row.get('name', '').strip())
        ]
