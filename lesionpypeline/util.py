import os

def append_file_postfix(path, postfix):
    """
    Given a path and a postfix, appends the postfix to the filename while
    preserving file extensions.
    """
    head, tail = os.path.split(path)

    tokens = tail.split('.')
    tokens[0] += postfix

    tail = '.'.join(tokens)
    return os.path.join(head, tail)
