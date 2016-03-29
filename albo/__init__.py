"""Provides an entry point for albo console scripts."""
import argparse


def main():
    """Entry point for console scripts."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    import albo.albo_run as run
    run_parser = subparsers.add_parser('run')
    run_parser.set_defaults(func=run.main)
    run.add_arguments_to(run_parser)

    import albo.albo_list as list
    list_parser = subparsers.add_parser('list')
    list_parser.set_defaults(func=list.main)
    list.add_arguments_to(list_parser)

    import albo.albo_update as update
    update_parser = subparsers.add_parser('update')
    update_parser.set_defaults(func=update.main)
    update.add_arguments_to(update_parser)

    args = parser.parse_args()
    args.func(args)
