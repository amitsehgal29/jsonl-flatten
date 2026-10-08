#!/usr/bin/env python3
"""jsonl-flatten: turn nested JSON Lines into a flat CSV with dotted column names.

Standard library only. Each input line is one JSON object. Nested objects become
dotted columns (customer.address.city). Lists are either JSON-encoded into one
cell (default) or exploded into one output row per list item (--explode PATH).
The column set is the union across all records, in first-seen order.
"""
import argparse
import csv
import json
import sys


def flatten(obj, prefix="", sep="."):
    """Flatten nested dicts into {"a.b": value}. Lists stay as lists."""
    out = {}
    for key, value in obj.items():
        name = f"{prefix}{sep}{key}" if prefix else str(key)
        if isinstance(value, dict) and value:
            out.update(flatten(value, name, sep))
        else:
            out[name] = value
    return out


def explode(record, path, sep="."):
    """Yield one flat record per item in the list at `path`.

    Missing or empty lists yield the record once with the path column empty.
    Items that are objects are flattened under the path prefix.
    """
    flat = flatten(record, sep=sep)
    items = flat.pop(path, None)
    if not isinstance(items, list) or not items:
        flat[path] = None
        yield flat
        return
    for item in items:
        row = dict(flat)
        if isinstance(item, dict):
            row.update(flatten(item, path, sep))
        else:
            row[path] = item
        yield row


def cell(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (list, dict)):
        return json.dumps(value, separators=(",", ":"), ensure_ascii=False)
    return value


def convert(lines, explode_path=None, sep="."):
    """Return (columns, rows) from an iterable of JSON Lines strings.

    Raises ValueError naming the 1-based line number for bad JSON or non-objects.
    """
    rows, columns, seen = [], [], set()
    for n, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as e:
            raise ValueError(f"line {n}: invalid JSON ({e.msg})") from None
        if not isinstance(record, dict):
            raise ValueError(f"line {n}: expected a JSON object, got {type(record).__name__}")
        produced = explode(record, explode_path, sep) if explode_path else [flatten(record, sep=sep)]
        for row in produced:
            for col in row:
                if col not in seen:
                    seen.add(col)
                    columns.append(col)
            rows.append(row)
    return columns, rows


def main(argv=None):
    p = argparse.ArgumentParser(description="Flatten nested JSON Lines into CSV.")
    p.add_argument("path", nargs="?", help="JSONL file (default: stdin)")
    p.add_argument("-o", "--output", default="-", help="CSV output path (default: stdout)")
    p.add_argument("--explode", metavar="PATH", help="dotted path of a list to expand into one row per item, e.g. items")
    p.add_argument("--sep", default=".", help="separator for nested column names (default: .)")
    args = p.parse_args(argv)

    src = open(args.path, encoding="utf-8") if args.path else sys.stdin
    try:
        columns, rows = convert(src, args.explode, args.sep)
    except ValueError as e:
        print(f"jsonl-flatten: {e}", file=sys.stderr)
        return 2
    finally:
        if args.path:
            src.close()

    out = sys.stdout if args.output == "-" else open(args.output, "w", newline="", encoding="utf-8")
    try:
        w = csv.writer(out)
        w.writerow(columns)
        for row in rows:
            w.writerow([cell(row.get(c)) for c in columns])
    finally:
        if out is not sys.stdout:
            out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
