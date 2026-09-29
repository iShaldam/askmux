#!/usr/bin/env python3
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
START = "<!-- matrix:start -->"
END = "<!-- matrix:end -->"


def table(path, text, matrix):
    def line(cells):
        return ("| " + " | ".join(cells) + " |").replace(" |  |", " | |")

    rows = []
    if path == "MATRIX.md":
        rows = ["| harness | tool | surface / mode | model | result | unanswered | evidence |",
                "|---|---|---|---|---|---|---|"]
        rows += [line(
            [f"`{r['harness']}`", f"`{r['tool']}`", r["surface"], r["model"],
             r["result"], r["unanswered"], r["evidence"]])
                 for r in matrix["rows"]]
    elif path == "README.md":
        rows = ["| harness | tool | interactive | headless | notes |",
                "|---|---|---|---|---|"]
        rows += [line(
            [h["name"], f"`{h['tool']}`", h["grid"]["interactive"],
             h["grid"]["headless"], h["grid"]["notes"]])
                 for h in matrix["harnesses"].values()]
    else:
        rows = ["| Harness | Tool | Where it works |",
                "|---|---|---|"]
        rows += [line([h["name"], f"`{h['tool']}`", h["where"]])
                 for h in matrix["harnesses"].values()]
    match = re.search(re.escape(START) + r"\n.*?\n" + re.escape(END), text, re.S)
    if not match:
        raise ValueError(path)
    return text[:match.start()] + START + "\n" + "\n".join(rows) + "\n" + END + text[match.end():]


def files(matrix):
    return [(name, os.path.join(ROOT, name)) for name in
            ("MATRIX.md", "README.md", "skills/askmux/SKILL.md")]


def main(command):
    with open(os.path.join(ROOT, "matrix.json")) as f:
        matrix = json.load(f)
    rendered = {}
    try:
        for name, path in files(matrix):
            with open(path) as f:
                rendered[name] = table(name, f.read(), matrix)
    except (OSError, ValueError) as error:
        print("matrix: " + str(error))
        return 2
    if command == "render":
        for name, path in files(matrix):
            with open(path, "w") as f:
                f.write(rendered[name])
        return 0
    if command == "check":
        status = 0
        for name, path in files(matrix):
            with open(path) as f:
                if f.read() != rendered[name]:
                    print(f"matrix: {name} is out of date, run: python3 scripts/matrix.py render")
                    status = 1
        return status
    print("usage: matrix.py render|check")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) == 2 else ""))
