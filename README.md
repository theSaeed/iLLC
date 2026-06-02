# iLLC Dataset Generator

This repository generates the iLLC dataset introduced in the ReHoPER (Receding Horizon Planning for Enhanced Reasoning) paper.
iLLC stands for `i`-th to Last Letter Concatenation: it generalizes LLC by concatenating the `i`-th to last letters of the words in a name-like string:

```text
Take the second-to-last letters of the words in "Anne Davis" and concatenate them.
```

The answer is `ni`.

For background, see the ReHoPER paper and the paper that introduced LLC:

- ReHoPER paper: [TBA]
- LLC: Jason Wei, Xuezhi Wang, Dale Schuurmans, Maarten Bosma, Brian Ichter,
  Fei Xia, Ed Chi, Quoc V. Le, and Denny Zhou. "Chain-of-Thought Prompting
  Elicits Reasoning in Large Language Models." NeurIPS 2022.
  https://arxiv.org/abs/2201.11903

## Setup

The generator reads local CSV files with a `name` column. By default, it uses
the prepared files in `support-files/processed`:

- `male1000.csv`
- `female1000.csv`
- `last.csv`

The first-name files are prepared from the Social Security Administration baby
names archive. The last-name file is prepared from the U.S. Census surname
data.

The source files included under `support-files/unprocessed/` are:

- `names.zip`: SSA baby names archive
- `Names_2010Census_Top1000.xlsx`: U.S. Census top 1,000 surnames workbook

Helper scripts are included if you need to rebuild the CSV files:

```bash
python support-files/fill_first_names.py
python support-files/fill_last_names.py
```

Data sources:

- SSA baby names: https://www.ssa.gov/oact/babynames/names.zip (The archived snapshot can be found [here](https://web.archive.org/web/20240329104153if_/https://www.ssa.gov/oact/babynames/names.zip).)
- U.S. Census surname data: https://www.census.gov/topics/population/genealogy/data.html (The archived snapshot can be found [here](https://web.archive.org/web/20260227055245if_/https://www2.census.gov/topics/genealogy/2010surnames/Names_2010Census_Top1000.xlsx).)

## Requirements

The script only uses the Python standard library. No package installation is
required.

Use Python 3:

```bash
python illc.py --help
```

## Usage

Generate the default validation/test splits for `L1` with 4-word names:

```bash
python illc.py L1 4
```

This reads from the default files:

- `support-files/processed/male1000.csv`
- `support-files/processed/female1000.csv`
- `support-files/processed/last.csv`

and writes:

```text
datasets/L1-4/val.csv
datasets/L1-4/test.csv
```

Generate train, validation, and test splits:

```bash
python illc.py L2 4 --splits 1000,200,500
```

Use a fixed random seed:

```bash
python illc.py L3 5 --splits 1000,200,500 --seed 123
```

Use custom CSV input files:

```bash
python illc.py L2 4 --male-file path/to/male.csv --female-file path/to/female.csv --last-file path/to/last.csv
```

Write outputs to a custom directory:

```bash
python illc.py L2 4 --output-dir /tmp/illc-datasets
```

## Arguments

```text
python illc.py type name-length [--splits TRAIN,VAL,TEST] [--seed SEED] [--male-file MALE_FILE] [--female-file FEMALE_FILE] [--last-file LAST_FILE] [--output-dir OUTPUT_DIR]
```

Arguments:

- `type`: iLLC task type, written as `L<number>`.
- `name_length`: number of words in each generated name-like string.
- `--splits`: comma-separated split sizes in `train,val,test` order. Defaults
  to `0,250,250`.
- `--seed`: random seed. Defaults to `42`.
- `--male-file`: CSV file for male first names. Defaults to
  `support-files/processed/male1000.csv`.
- `--female-file`: CSV file for female first names. Defaults to
  `support-files/processed/female1000.csv`.
- `--last-file`: CSV file for last names. Defaults to `support-files/processed/last.csv`.
- `--output-dir`: directory where generated dataset folders are written.
  Defaults to `datasets`.

Examples of `type`:

- `L1`: concatenate the last letter of each word.
- `L2`: concatenate the second-to-last letter of each word.
- `L3`: concatenate the third-to-last letter of each word.

The value after `L` must be a positive integer. For example, `L4` is valid, but
`L0` is not.

## Output Format

Each requested split is written as a CSV file under:

```text
<output-dir>/<type>-<name-length>/
```

For example:

```text
datasets/L2-4/train.csv
datasets/L2-4/val.csv
datasets/L2-4/test.csv
```

Each CSV has four columns:

```text
id,name,x,y
```

Columns:

- `id`: integer example id.
- `name`: generated name-like string.
- `x`: natural-language prompt.
- `y`: expected answer.

Example row:

```csv
id,name,x,y
0,Anne Davis,"Take the second-to-last letters of the words in “Anne Davis” and concatenate them.",ni
```

## How Generation Works

The script first reads names from the local CSV files:

- first names are read from `male-file` and `female-file`
- last names are read from `last-file`

Each input CSV must contain a `name` column. Other columns, such as `rank` and
`frequency`, are allowed but are not used by the generator.

Then it filters out any name shorter than the requested `i` in `Li`. For
example, `L3` only keeps names with at least three letters.

For each example, the script:

1. randomly chooses how many of the `name_length` words should come from the
   first-name pool
2. fills the remaining words from the last-name pool
3. concatenates the `i`-th to last character from each word
4. writes the prompt and answer to the requested split CSV

For `L1`, the answer uses the last letters. For `L2`, it uses the
second-to-last letters, and so on.

## Notes

- Existing output files are overwritten when the same split is regenerated.
- Splits with size `0` are skipped.
- The global `id` counter continues across splits in `train`, `val`, `test`
  order.
- The generation is random but reproducible with `--seed`.

## Citation

If you find this repository helpful or relevant to your work, please kindly cite the following paper:

```bibtex
[TBA]
```
