"""sappy.

Usage:
  sappy setup
  sappy build <package>
  sappy sync
  sappy (-h | --help)
  sappy --version

Options:
  -h --help     Show this screen.
  --version     Show version.

"""
from docopt import docopt
from operations import build, sync, setup

if __name__ == '__main__':
    args = docopt(__doc__, version='sappy 1.0.0-dev')
    
    if args.get('setup'):
      setup()
    elif args.get('build'):
      build(args.get('<package>'))

    elif args.get('sync'):
      sync()