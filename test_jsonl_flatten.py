import unittest

from jsonl_flatten import cell, convert, explode, flatten

LINES = [
    '{"id": 1, "user": {"name": "a", "geo": {"city": "Dubai"}}, "tags": ["x", "y"]}',
    "",
    '{"id": 2, "user": {"name": "b"}, "extra": null}',
]


class FlattenTests(unittest.TestCase):
    def test_nested_keys_become_dotted(self):
        self.assertEqual(flatten({"a": {"b": {"c": 1}}, "d": 2}), {"a.b.c": 1, "d": 2})

    def test_empty_dict_is_kept_as_value(self):
        self.assertEqual(flatten({"a": {}}), {"a": {}})

    def test_columns_are_union_in_first_seen_order(self):
        cols, rows = convert(LINES)
        self.assertEqual(cols, ["id", "user.name", "user.geo.city", "tags", "extra"])
        self.assertEqual(len(rows), 2)

    def test_lists_are_json_encoded_cells(self):
        _, rows = convert(LINES)
        self.assertEqual(cell(rows[0]["tags"]), '["x","y"]')

    def test_cell_formats_none_and_bools(self):
        self.assertEqual((cell(None), cell(True), cell(False)), ("", "true", "false"))

    def test_explode_objects_one_row_per_item(self):
        rec = {"id": 1, "items": [{"sku": "A", "qty": 2}, {"sku": "B", "qty": 1}]}
        rows = list(explode(rec, "items"))
        self.assertEqual(rows, [
            {"id": 1, "items.sku": "A", "items.qty": 2},
            {"id": 1, "items.sku": "B", "items.qty": 1},
        ])

    def test_explode_empty_list_keeps_parent_row(self):
        self.assertEqual(list(explode({"id": 3, "items": []}, "items")), [{"id": 3, "items": None}])

    def test_explode_nested_path(self):
        rec = {"o": {"lines": [1, 2]}}
        self.assertEqual(list(explode(rec, "o.lines")), [{"o.lines": 1}, {"o.lines": 2}])

    def test_bad_json_reports_line_number(self):
        with self.assertRaisesRegex(ValueError, "line 2"):
            convert(['{"a": 1}', '{oops}'])

    def test_non_object_rejected(self):
        with self.assertRaisesRegex(ValueError, "expected a JSON object"):
            convert(["[1, 2]"])


if __name__ == "__main__":
    unittest.main()
