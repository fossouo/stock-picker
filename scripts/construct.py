# Attempt at building the code from src/algo into something that
# quantopian can digest.

import os
import errno
import shutil
import sys
from lib import Error, change_dir_to_project_root, IMPORT_MARKER, FILENAME_MARKER

STAGE_DIR = "stage/construction"
SRC_DIR = "src/algo"

def prep_stage_dir(dir_path):
    """
    Destroy and recreate a staging directory
    """
    try:
        shutil.rmtree(dir_path)
    except OSError as e:
        if e.errno == errno.ENOENT:
            pass

    os.makedirs(dir_path)


def build_from_source(source_dir, target_file_name):
    """
    Creates a new quantopian-compatible file from the source.  This is basically just concatinating all the files together, but with some markers for our own info and to remove things that quantopian doesn't understand
    """

    with open(target_file_name, "w") as output:

        filenames = filter(lambda fname: fname.endswith(".py"),
            os.listdir(source_dir))
        chain = map(lambda fname: fname[:-3], filenames)
        library_names = set(chain)

        for filename in filenames:
            # TODO: skip swp files.  Or all non-py files?
            file_path = os.path.join(SRC_DIR, filename)

            output.write(FILENAME_MARKER + filename + "\n")
            add_file_to_build(file_path, output, library_names)


def add_file_to_build(file_path, output, library_names):
    """
    Goes line-by-line in the file, commenting out things that quantopian will
    be confused by. (Right now, that means import statements.)
    """
    with open(file_path) as input_file:
        for line in input_file:
            output_line = line
            if is_unacceptable_import_statement(line, library_names):
                output_line = IMPORT_MARKER + line

            output.write(output_line)

def is_unacceptable_import_statement(line, library_names):
    for token in line.split():
        if token in library_names:
            return True
    return False

### Main ###
def main(args):
    change_dir_to_project_root()
    prep_stage_dir(STAGE_DIR)
    build_from_source(SRC_DIR, os.path.join(STAGE_DIR, "algo.py"))
    #move_to_build_dir()
    

if __name__ == "__main__":

    import argparse
    parser = argparse.ArgumentParser(description='Quantopian algorithm constructor. Combines our source files into a single large file that Quantopian can use.  Tries to use a format that we can later deconstruct back into source code.')

    parser.add_argument('-v','--verbose', action='store_const', const=True, 
        default=False, help="Enable verbose output")

    args = parser.parse_args()

    try:
        main(args)
    except Error as e:
        print e
        sys.exit(1)
