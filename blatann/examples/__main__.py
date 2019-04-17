from __future__ import absolute_import
import glob
from os import path
import sys
import blatann.examples

# Non-example python files to exclude
EXCLUDES = ["__init__", "__main__", "constants", "example_utils"]

_py_files = [path.splitext(path.basename(f))[0] for f in glob.glob(path.dirname(__file__) + "/*.py")]
examples = [f for f in _py_files if f not in EXCLUDES]


def print_help():
    print("\nUsage: python -m blatann.examples [example_filename] [comport]")
    print("Examples:")
    for e in examples:
        print("  {}".format(e))
    sys.exit(1)


def main():
    if len(sys.argv) < 3:
        print_help()

    example_name = sys.argv[1]
    comport = sys.argv[2]

    if example_name not in examples:
        print("Unknown example {}".format(example_name))
        print_help()

    module = __import__(blatann.examples.__name__, fromlist=[example_name])
    example = getattr(module, example_name)
    example.main(comport)


if __name__ == '__main__':
    main()
