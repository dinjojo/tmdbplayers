# Content from __init__.py

from pathlib import Path
import argparse
from halo import Halo

from app.view import print_directory_with_restricted_access, print_biggest_files
from app.helper import prepare_filter_config
from app.scanner import traverse_dir


def main(argv):
    conditions = prepare_filter_config(argv)

    scanned = []
    permission_issue = []

    path = Path.cwd().joinpath(argv.path).resolve()
    spinner = Halo(text='Scanning files', spinner='bouncingBall', text_color="green")
    spinner.start()
    traverse_dir(path, scanned, permission_issue, conditions)
    spinner.stop()
    print_biggest_files(scanned, argv.limit)

    if(argv.hide_limited_access == 'false'):
        print_directory_with_restricted_access(permission_issue)



def initialize():
    parser = argparse.ArgumentParser(description='An CLI application to find big files in the file system.',)
    parser.add_argument('--limit', '-limit', '-l', type=int,
                        help='Number of files you want to see in the table. Default value is 10. Maximum accepted value is 200', default=15)
    parser.add_argument('--min-size', '-min-size', dest="min_file_size",
                        help='Minimum file size to search. Accepted values are b, KB, MB, TB. For example --min_file_size 10KB')
    parser.add_argument('--max-size', '-max-size', dest="max_file_size",
                        help='Maximum file size to search. Accepted values are b, KB, MB, TB. For example --max_file_size 10KB')
    parser.add_argument('--search', '-search', '-s', help="Search by name. --search 'my_file.png'")
    parser.add_argument('--hide-limited-access', '-hide-limited-access', dest="hide_limited_access", default="false", help='Hide the table that contains directories with no access right. Only true or false are accepted')
    parser.add_argument('--extension', '-ext', default=[], nargs='*',
                        help='Extension of file such as .txt, .jpeg, .png, .mp3. Multiple extensions are accepted. Such as --extension .txt .png')
    parser.add_argument('path', help="relative path where you want to start search. For example ./")
    args = parser.parse_args()
    main(args)


# Content from __main__.py
from app import initialize


if __name__ == '__main__':
    initialize()


# Content from constants.py
MAX_CHAR_LENGTH_PER_LINE=120 # To control/wrap the file path inside table ui

MAX_ROW_COUNT=200


# Content from helper.py
from math import ceil, pow
from os import linesep
import re

from app.validator import isFileSize



def prepare_filter_config(argv):
    conditions = {
        "minimum_size": 0,
        "maximum_size": float("inf"),
        "extensions": argv.extension,
        "search": argv.search,
    }

    if(not argv.path):
        print("Please enter a valid path to start searching. Such as ./")
        exit(1)

    if(argv.min_file_size):
        if(isFileSize(argv.min_file_size)):
            conditions["minimum_size"] = convert_to_byte(argv.min_file_size)
        else:
            raise ValueError("Invalid value provided for --min-size")

    if(argv.min_file_size ):
        if(isFileSize(argv.max_file_size)):
            conditions["maximum_size"] = convert_to_byte(argv.max_file_size)
        else:
            raise ValueError("Invalid value provided for --max-size")

    return conditions


def break_line(text, max_line_length):
    if(len(text) > 0 and max_line_length > 0):
        line_nums = ceil(len(text)/max_line_length)
        lines = []
        for line in range(0, line_nums):
            start_index = line*max_line_length
            lines.append(text[start_index:start_index+max_line_length])
        return linesep.join(lines)
    return text


def convert_bytes_to_readable_unit(size):
    for x in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return "%3.1f %s" % (size, x)
        size /= 1024.0

    return size


def convert_to_byte(size):
    result = re.search('(\d+\.?\d*)(b|kb|mb|gb|tb)', size.lower())
    if(result and result.groups()):
        unit = result.groups()[1]
        amount = float(result.groups()[0])
        index = ['b', 'kb', 'mb', 'gb', 'tb'].index(unit)
        return amount * pow(1024, index)
    raise ValueError("Invalid size provided, value is "+size)
    

# Content from scanner.py
from pathlib import Path

from app.validator import  haveFileConditionsMet


def traverse_dir(path, scanned, permission_issue, conditions):
    try:
        result = Path(path).iterdir()
        for item in result:
            if(item.is_symlink()):
                continue
            if(item.is_dir()):
                traverse_dir(item, scanned, permission_issue, conditions)
            elif(item.is_file() and haveFileConditionsMet(item, conditions)):
                scanned.append({
                    "path": str(item),
                    "size": item.stat().st_size
                })
    except PermissionError as _:
        permission_issue.append(path)

# Content from validator.py
import re
from os import sep

def isFileSize(value):
    if(not value):
        return False
    pattern = re.compile("\d+\.?\d*(b|kb|mb|gb|tb)")
    return bool(pattern.fullmatch(value.lower()))


def haveFileConditionsMet(file, options):
    stat = file.stat()
    file_path = str(file)
    path_list = file_path.split(sep)
    file_name = path_list[-1:]

    if(len(options['extensions']) and file.suffix not in options['extensions']):
        return False

    if(options["search"] and not re.search(re.compile(options["search"].lower()),str(file_name).lower())):
        return False

    if(options["minimum_size"] > 0 and stat.st_size < options["minimum_size"]):
        return False

    if(options["maximum_size"] > 0 and stat.st_size > options["maximum_size"]):
        return False

    return True


# Content from view.py

import heapq
from tabulate import tabulate

from app.helper import break_line, convert_bytes_to_readable_unit
from app.constants import MAX_CHAR_LENGTH_PER_LINE, MAX_ROW_COUNT


def print_directory_with_restricted_access(permission_issue):
    if(len(permission_issue) > 0):
        print("\n\033[33m"+tabulate([[break_line(str(item), MAX_CHAR_LENGTH_PER_LINE)] for item in permission_issue], headers=["Index",
              "Could not scan these directories because of limited permission"], showindex="always", tablefmt="fancy_grid"))


def print_biggest_files(scanned, limit=15):
    if(limit > MAX_ROW_COUNT):
        limit = MAX_ROW_COUNT
    largest_files = heapq.nlargest(limit, scanned, key=lambda item: item['size'])
    print("\n\033[32m"+tabulate([[convert_bytes_to_readable_unit(row["size"]), break_line(row["path"], MAX_CHAR_LENGTH_PER_LINE)] for row in largest_files], headers=[
          "Index", "Size", "File Path"], showindex="always", tablefmt="fancy_grid"))


