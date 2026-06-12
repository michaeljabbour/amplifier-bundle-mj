"""Command-line entry point.

``main`` is wired as a console script in pyproject.toml
(``[project.scripts] pulse = "pulse.cli:main"``). It has no in-repo callers but
is the installed ``pulse`` command's entry point.
"""

import sys

from pulse.messages import format_message


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    title = argv[0] if argv else "hello"
    print(format_message({"title": title, "body": "from pulse"}))
    return 0
