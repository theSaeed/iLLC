import argparse
import csv
import re
import os
from collections import Counter
from pathlib import Path
from zipfile import ZipFile


YEAR_FILE_RE = re.compile(r"^yob(\d{4})\.txt$")
FIELDNAMES = ["rank", "name", "frequency"]
SCRIPT_DIR = Path(__file__).resolve().parent


def aggregate_names(zip_path, min_year, max_year):
    totals = {"M": Counter(), "F": Counter()}

    with ZipFile(zip_path) as archive:
        year_files = sorted(
            name
            for name in archive.namelist()
            if (match := YEAR_FILE_RE.match(name)) and min_year <= int(match.group(1)) <= max_year
        )
        if not year_files:
            raise ValueError(f"No yobYYYY.txt files from {min_year} through {max_year} found in {zip_path}")

        for year_file in year_files:
            with archive.open(year_file) as input_file:
                reader = csv.reader(
                    line.decode("utf-8") for line in input_file
                )
                for row_number, row in enumerate(reader, start=1):
                    if len(row) != 3:
                        raise ValueError(
                            f"Expected 3 columns in {year_file}:{row_number}, got {len(row)}"
                        )

                    name, sex, frequency = row
                    if sex not in totals:
                        raise ValueError(
                            f"Unexpected sex {sex!r} in {year_file}:{row_number}"
                        )

                    totals[sex][name] += int(frequency)

    return totals


def ranked_rows(counter, sex, limit=None):
    def descending_name_key(name):
        return tuple(-ord(char) for char in name)

    def sort_key(item):
        name, frequency = item
        first_letter = name[0].upper() if name else ""

        # Match reference tie ordering for male and female names
        if sex == "M":
            return (-frequency, first_letter, descending_name_key(name))
        else:
            return (-frequency, -ord(first_letter) if first_letter else 0, name)

    names = sorted(counter.items(), key=sort_key)
    if limit is not None:
        names = names[:limit]

    return [
        {"rank": rank, "name": name, "frequency": frequency}
        for rank, (name, frequency) in enumerate(names, start=1)
    ]


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as output_file:
        writer = csv.DictWriter(output_file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate Social Security baby names by sex and total frequency."
    )
    parser.add_argument(
        "input",
        nargs="?",
        default=SCRIPT_DIR / "unprocessed/names.zip",
        help="Path to the names.zip archive",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=1000,
        help="Number of names to write to the top-N CSV files",
    )
    parser.add_argument(
        "--min-year",
        type=int,
        default=1923,
        help="Earliest yobYYYY.txt year to include",
    )
    parser.add_argument(
        "--max-year",
        type=int,
        default=2022,
        help="Latest yobYYYY.txt year to include",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=SCRIPT_DIR / "processed",
        help="Directory to write the output CSV files",
    )
    parser.add_argument("--male-filename", default="male.csv")
    parser.add_argument("--female-filename", default="female.csv")
    parser.add_argument("--male-top-filename", default="male1000.csv")
    parser.add_argument("--female-top-filename", default="female1000.csv")
    args = parser.parse_args()

    male_output = os.path.join(args.output_dir, args.male_filename)
    female_output = os.path.join(args.output_dir, args.female_filename)
    male_top_output = os.path.join(args.output_dir, args.male_top_filename)
    female_top_output = os.path.join(args.output_dir, args.female_top_filename)

    totals = aggregate_names(args.input, args.min_year, args.max_year)

    male_rows = ranked_rows(totals["M"], "M")
    female_rows = ranked_rows(totals["F"], "F")
    male_top_rows = ranked_rows(totals["M"], "M", args.top_n)
    female_top_rows = ranked_rows(totals["F"], "F", args.top_n)

    write_csv(male_output, male_rows)
    write_csv(female_output, female_rows)
    write_csv(male_top_output, male_top_rows)
    write_csv(female_top_output, female_top_rows)

    print(f"Wrote {len(male_rows)} rows to {male_output}")
    print(f"Wrote {len(female_rows)} rows to {female_output}")
    print(f"Wrote {len(male_top_rows)} rows to {male_top_output}")
    print(f"Wrote {len(female_top_rows)} rows to {female_top_output}")


if __name__ == "__main__":
    main()
