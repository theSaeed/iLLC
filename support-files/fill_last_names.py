import argparse
import csv
import os
import re
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET


SCRIPT_DIR = Path(__file__).resolve().parent
NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkgrel": "http://schemas.openxmlformats.org/package/2006/relationships",
}


def column_index(cell_ref):
    match = re.match(r"([A-Z]+)", cell_ref)
    if not match:
        raise ValueError(f"Invalid cell reference: {cell_ref}")

    index = 0
    for char in match.group(1):
        index = index * 26 + ord(char) - ord("A") + 1
    return index - 1


def normalize_header(value):
    return re.sub(r"[^A-Z0-9]+", " ", value.upper()).strip()


def load_shared_strings(workbook):
    if "xl/sharedStrings.xml" not in workbook.namelist():
        return []

    root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
    shared_strings = []
    for item in root.findall("main:si", NS):
        text = "".join(node.text or "" for node in item.findall(".//main:t", NS))
        shared_strings.append(text)
    return shared_strings


def first_sheet_path(workbook):
    workbook_root = ET.fromstring(workbook.read("xl/workbook.xml"))
    first_sheet = workbook_root.find("main:sheets/main:sheet", NS)
    if first_sheet is None:
        raise ValueError("Workbook does not contain any sheets")

    relationship_id = first_sheet.attrib[f"{{{NS['rel']}}}id"]
    rels_root = ET.fromstring(workbook.read("xl/_rels/workbook.xml.rels"))
    for relationship in rels_root.findall("pkgrel:Relationship", NS):
        if relationship.attrib["Id"] == relationship_id:
            target = relationship.attrib["Target"]
            return os.path.normpath(os.path.join("xl", target))

    raise ValueError(f"Could not find sheet relationship {relationship_id}")


def cell_value(cell, shared_strings):
    cell_type = cell.attrib.get("t")

    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(".//main:t", NS))

    value_node = cell.find("main:v", NS)
    if value_node is None:
        return ""

    value = value_node.text or ""
    if cell_type == "s":
        return shared_strings[int(value)]
    if cell_type == "b":
        return "TRUE" if value == "1" else "FALSE"
    return value


def iter_rows(workbook, sheet_path, shared_strings):
    root = ET.fromstring(workbook.read(sheet_path))
    for row in root.findall(".//main:sheetData/main:row", NS):
        values = []
        for cell in row.findall("main:c", NS):
            index = column_index(cell.attrib["r"])
            while len(values) <= index:
                values.append("")
            values[index] = cell_value(cell, shared_strings)
        yield values


def parse_int(value):
    return str(int(float(str(value).replace(",", "").strip())))


def surname_to_name(value):
    # Convert surname to name by stripping whitespace and title-casing. Handle special cases for Mc, LeBlanc, etc.
    value = str(value).strip().title()
    if value.startswith("Mc") and len(value) > 2:
        value = "Mc" + value[2].upper() + value[3:]
    if value == 'Macdonald':
        value = 'MacDonald'
    if value == 'Leblanc':
        value = 'LeBlanc'
    if value == 'Deleon':
        value = 'DeLeon'
    if value == 'Dejesus':
        value = 'DeJesus'
    if value == 'Odonnell':
        value = "O'Donnell"
    if value == 'Oneill':
        value = "O'Neill"
    if value == 'Oneal':
        value = "O'Neal"
    if value == 'Oconnell':
        value = "O'Connell"
    if value == 'Oconnor':
        value = "O'Connor"
    if value == "Obrien":
        value = "O'Brien"
    return value


def read_census_last_names(input_path):
    with ZipFile(input_path) as workbook:
        shared_strings = load_shared_strings(workbook)
        sheet_path = first_sheet_path(workbook)

        header_indexes = None
        for row in iter_rows(workbook, sheet_path, shared_strings):
            headers = {normalize_header(value): index for index, value in enumerate(row)}
            if {"SURNAME", "RANK", "FREQUENCY COUNT"}.issubset(headers):
                header_indexes = headers
                continue

            if header_indexes is None:
                continue

            required_indexes = [
                header_indexes["SURNAME"],
                header_indexes["RANK"],
                header_indexes["FREQUENCY COUNT"],
            ]
            if len(row) <= max(required_indexes):
                continue

            surname = row[header_indexes["SURNAME"]].strip()
            if not surname:
                continue

            yield {
                "rank": parse_int(row[header_indexes["RANK"]]),
                "name": surname_to_name(surname),
                "frequency": parse_int(row[header_indexes["FREQUENCY COUNT"]]),
            }


def main():
    parser = argparse.ArgumentParser(
        description="Fill last.csv from the Census top 1,000 surnames XLSX file."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=SCRIPT_DIR / "unprocessed/Names_2010Census_Top1000.xlsx",
        help="Path to the Census XLSX file",
    )
    parser.add_argument(
        "output",
        nargs="?",
        default=SCRIPT_DIR / "processed/last.csv",
        help="Path to the CSV file to write",
    )
    args = parser.parse_args()

    rows = list(read_census_last_names(args.input))
    if not rows:
        raise ValueError(f"No Census surname rows found in {args.input}")

    with open(args.output, "w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=["rank", "name", "frequency"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
