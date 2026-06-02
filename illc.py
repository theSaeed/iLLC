from utils import extract_names
import argparse
import random
import csv
import os
import re

def parse_splits(s):
    parts = s.split(',')
    if len(parts) != 3:
        raise argparse.ArgumentTypeError(
            "Expected three comma-separated integers for train,val,test splits"
        )
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        raise argparse.ArgumentTypeError("Splits must be integers")


def generate_name(first_names, last_names, name_length, i_to_last):
    if name_length < 1:
        raise ValueError("name_length must be at least 1")
    # Build list: first (first_name_length) words from first_names, then last name
    first_name_length = random.randint(0, name_length)
    words_list = [random.choice(first_names) for _ in range(first_name_length)]
    words_list += [random.choice(last_names) for _ in range(name_length - first_name_length)]
    name = ' '.join(words_list)
    last_letter_list = [word[-i_to_last] for word in words_list]
    last_letter_concat = ''.join(last_letter_list)
    return name, last_letter_concat


def main():
    parser = argparse.ArgumentParser(description='Generate letter-concatenation examples from name CSV files')
    parser.add_argument('type',
                        help='Type of task to generate (e.g. L1, L2, L3, L4, etc.)')
    parser.add_argument('name_length', type=int,
                        help='The length of the names (the number of words) to generate')
    parser.add_argument('--splits', type=parse_splits, default='0,250,250',
                        help='Comma-separated train,val,test sizes as integers, e.g. "80,10,10"')
    parser.add_argument('--seed', type=int, default=42,
                        help='Random seed for reproducibility')
    parser.add_argument('--male-file', default=os.path.join('support-files', 'processed', 'male1000.csv'),
                        help='CSV file for male names')
    parser.add_argument('--female-file', default=os.path.join('support-files', 'processed', 'female1000.csv'),
                        help='CSV file for female names')
    parser.add_argument('--last-file', default=os.path.join('support-files', 'processed', 'last.csv'),
                        help='CSV file for last names')
    parser.add_argument('--output-dir', default='datasets',
                        help='Output directory to write generated dataset folders')
    args = parser.parse_args()
    random.seed(args.seed)

    male_names = extract_names(args.male_file)
    female_names = extract_names(args.female_file)
    
    match = re.match(r'^L([1-9]\d*)$', args.type)
    if not match:
        raise ValueError("Type must be formatted as L<number>, e.g., L1, L2, L3")
    i_to_last = int(match.group(1))

    if i_to_last == 1:
        ith_to_last = 'last'
    elif i_to_last == 2:
        ith_to_last = 'second-to-last'
    elif i_to_last == 3:
        ith_to_last = 'third-to-last'
    else:
        suffix = 'th'
        if i_to_last % 10 == 1 and i_to_last % 100 != 11:
            suffix = 'st'
        elif i_to_last % 10 == 2 and i_to_last % 100 != 12:
            suffix = 'nd'
        elif i_to_last % 10 == 3 and i_to_last % 100 != 13:
            suffix = 'rd'
        ith_to_last = f'{i_to_last}{suffix}-to-last'

    first_names = [n for n in (male_names + female_names) if len(n) >= i_to_last]
    last_names = [n for n in extract_names(args.last_file) if len(n) >= i_to_last]

    if not first_names or not last_names:
        raise ValueError(f"No names found with at least {i_to_last} letters.")

    uid = 0
    for split_file_name, split_size in zip(['train.csv', 'val.csv', 'test.csv'], args.splits):
        if split_size < 1:
            continue
        split_file_path = os.path.join(
            args.output_dir,
            f'{args.type}-{args.name_length}',
            split_file_name,
        )
        os.makedirs(os.path.dirname(split_file_path), exist_ok=True)
        with open(split_file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'x', 'y'])
            for i in range(split_size):
                name, last_letter_concat = generate_name(first_names, last_names, args.name_length, i_to_last)
                question = f'Take the {ith_to_last} letters of the words in “{name}” and concatenate them.'
                writer.writerow([uid, name, question, last_letter_concat])
                uid += 1


if __name__ == '__main__':
    main()
