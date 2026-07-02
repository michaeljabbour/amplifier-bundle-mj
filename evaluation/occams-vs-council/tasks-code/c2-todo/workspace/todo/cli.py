"""Command-line interface for the todo app."""
import argparse

from todo import service, store

DEFAULT_PATH = "todos.json"


def main(argv=None):
    parser = argparse.ArgumentParser(prog="todo")
    parser.add_argument("--file", default=DEFAULT_PATH)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add")
    p_add.add_argument("title")

    sub.add_parser("list")

    p_done = sub.add_parser("done")
    p_done.add_argument("id", type=int)

    args = parser.parse_args(argv)
    todos = store.load(args.file)

    if args.cmd == "add":
        t = service.add(todos, args.title)
        print(f"added #{t['id']}: {t['title']}")
    elif args.cmd == "list":
        for t in service.list_todos(todos):
            mark = "x" if t["done"] else " "
            print(f"[{mark}] #{t['id']} {t['title']}")
    elif args.cmd == "done":
        t = service.complete(todos, args.id)
        print(f"completed #{t['id']}")

    store.save(args.file, todos)


if __name__ == "__main__":
    main()
