
import argparse
import albo.albo_run as run


def main():
    """Entry point for console scripts."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    run_parser = subparsers.add_parser('run')
    run_parser.set_defaults(func=run.main)
    run.add_arguments(run_parser)

    args = parser.parse_args()
    args.func(args)
