import os

FILENAME_MARKER = "#%FILENAME "
IMPORT_MARKER = "#%IMPORT "

class Error(Exception):
    """So we can tell the difference between our exceptions and others"""
    pass

def change_dir_to_project_root():
    """
    We want to work from the root of the project (where .git) is.  This will
    help ensure we're not off clobbering the wrong directories.
    """
    while True:
        if os.path.exists(".git"):
            break
        elif len(os.getcwd()) < 5:
            raise Error("Couldn't find project root.  Try running from within the project directory.")
        os.chdir(os.path.pardir)
