#!/usr/bin/env python3
import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ISSUE_RE = re.compile(r"https://github\.com/([^/\s]+)/([^/\s]+)/issues/(\d+)")
CODE_RE = re.compile(
    r"https://github\.com/([^/\s]+)/([^/\s]+)/blob/([0-9a-f]{40})/([^#\s]+)"
    r"#L(\d+)(?:-L(\d+))?"
)


def links(matrix):
    found = {}
    evidence = "\n".join(row.get("evidence", "") for row in matrix["rows"])
    for match in ISSUE_RE.finditer(evidence):
        url = match.group(0)
        found[url] = {"kind": "issue", "url": url, "repo": f"{match[1]}/{match[2]}",
                      "number": int(match[3])}
    for match in CODE_RE.finditer(evidence):
        url = match.group(0)
        start = int(match[5])
        found[url] = {"kind": "code", "url": url, "repo": f"{match[1]}/{match[2]}",
                      "sha": match[3], "path": match[4], "start": start,
                      "end": int(match[6] or match[5])}
    return [found[url] for url in sorted(found)]


def code_moved(pinned_lines, head_text):
    pinned = [line.strip() for line in pinned_lines]
    head = [line.strip() for line in head_text.splitlines()]
    return not any(head[i:i + len(pinned)] == pinned
                   for i in range(len(head) - len(pinned) + 1))


def diff(baseline, current):
    changes = []
    for url in sorted(set(baseline) | set(current)):
        if url not in baseline:
            changes.append(f"{url}: new")
        elif url not in current:
            changes.append(f"{url}: dropped")
        elif baseline[url] != current[url]:
            changes.append(f"{url}: {baseline[url]} -> {current[url]}")
    return changes


def fetch(url, token):
    request = urllib.request.Request(url, headers={"User-Agent": "askmux-watch"})
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=20) as response:
        return response.read().decode()


def state(link, token):
    if link["kind"] == "issue":
        url = f"https://api.github.com/repos/{link['repo']}/issues/{link['number']}"
        return json.loads(fetch(url, token))["state"]
    base = f"https://raw.githubusercontent.com/{link['repo']}"
    pinned = fetch(f"{base}/{link['sha']}/{link['path']}", token)
    try:
        head = fetch(f"{base}/HEAD/{link['path']}", token)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return "gone"
        raise
    lines = pinned.splitlines()[link["start"] - 1:link["end"]]
    return "moved" if code_moved(lines, head) else "same"


def main():
    with open(os.path.join(ROOT, "matrix.json")) as file:
        matrix = json.load(file)
    token = os.environ.get("GITHUB_TOKEN")
    items = links(matrix)
    if sys.argv[1:] == ["update"]:
        current = {link["url"]: state(link, token) for link in items}
        with open(os.path.join(ROOT, "watch.json"), "w") as file:
            json.dump(dict(sorted(current.items())), file, indent=2)
            file.write("\n")
        return 0
    if sys.argv[1:] != ["check"]:
        print("usage: watch.py check|update")
        return 2
    current = {}
    for link in items:
        try:
            current[link["url"]] = state(link, token)
        except (OSError, urllib.error.URLError, TimeoutError) as error:
            print(f"watch error: {link['url']}: {error}", file=sys.stderr)
            return 2
    with open(os.path.join(ROOT, "watch.json")) as file:
        baseline = json.load(file)
    changes = diff(baseline, current)
    print("\n".join(changes))
    return 1 if changes else 0


if __name__ == "__main__":
    sys.exit(main())
