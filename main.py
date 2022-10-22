"""sappy.

Usage:
  sappy build <package>
  sappy chroot
  sappy sync
  sappy (-h | --help)
  sappy --version

Options:
  -h --help     Show this screen.
  --version     Show version.

"""
from docopt import docopt


if __name__ == '__main__':
    arguments = docopt(__doc__, version='sappy 1.0.0-dev')
    print(arguments)