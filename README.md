# jsonl-flatten

A tiny, standard-library-only CLI that turns nested JSON Lines (one JSON object per line, as API exports and event logs often are) into a flat CSV you can load into a warehouse or open in a spreadsheet.

- Nested objects become dotted columns, like `customer.address.city`.
- The column set is the union of every record, in first-seen order, so records with missing fields still line up.
- Lists go into one JSON-encoded cell by default, or `--explode PATH` turns them into one row per item.
- Bad lines fail loudly with the line number instead of being skipped silently.

## Usage

```bash
python3 jsonl_flatten.py samples/orders.jsonl
```

```csv
order_id,customer.name,customer.address.city,items,paid,coupon
1001,alice,Dubai,"[{""sku"":""A1"",""qty"":2},{""sku"":""B7"",""qty"":1}]",true,
1002,bob,Pune,"[{""sku"":""C3"",""qty"":5}]",false,OCT10
1003,carol,,[],true,
```

Explode the order lines into one row per item:

```bash
python3 jsonl_flatten.py samples/orders.jsonl --explode items -o order_lines.csv
```

```csv
order_id,customer.name,customer.address.city,paid,items.sku,items.qty,coupon,items
1001,alice,Dubai,true,A1,2,,
1001,alice,Dubai,true,B7,1,,
1002,bob,Pune,false,C3,5,OCT10,
1003,carol,,true,,,,
```

Other options: read from stdin when no path is given, and use `--sep _` for underscore column names.

## Tests

```bash
python3 -m unittest
```
