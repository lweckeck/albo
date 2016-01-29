
import os
import argparse
import ConfigParser
import pkg_resources

import albo.albo_run as run
import albo.albo_list as list


def main():
    """Entry point for console scripts."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    run_parser = subparsers.add_parser('run')
    run_parser.set_defaults(func=run.main)
    run.add_arguments_to(run_parser)

    list_parser = subparsers.add_parser('list')
    list_parser.set_defaults(func=list.main)
    list.add_arguments_to(list_parser)

    args = parser.parse_args()
    update_from_config_file(args)
    args.func(args)


def update_from_config_file(args):
    """Update an argparse Namespace object from a configuration file.

    Given a Namespace object, read options from a configuration file and fill
    in all values which are 'None', if there is a value given in the
    configuration file.
    """
    if 'config' not in vars(args) or args.config is None:
        if os.path.isfile('~/.config/albo.conf'):
            args.config = '~/.config/albo.conf'
        else:
            args.config = pkg_resources.resource_filename(
                __name__, 'config/pipeline.conf')

    options = dict()
    parser = ConfigParser.ConfigParser()
    parser.read(args.config)
    for section in parser.sections():
        for key, value in parser.items(section):
            if os.path.isfile(value) or os.path.isdir(value):
                value = os.path.abspath(value)
            options[key] = value

    for key in options:
        if key not in vars(args) or vars(args)[key] is None:
            vars(args)[key] = options[key]
