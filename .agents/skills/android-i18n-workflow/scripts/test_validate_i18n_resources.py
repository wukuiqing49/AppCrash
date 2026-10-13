"""覆盖跨语言复数与损坏资源的门禁回归。"""

import tempfile
import unittest
from pathlib import Path

from validate_i18n_resources import validate_res_dir


class ResourceValidationTest(unittest.TestCase):
    def validate(self, localized, base=None):
        base = base or '<plurals name="count"><item quantity="one">%d item</item><item quantity="other">%d items</item></plurals>'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for locale, text in (("values", base), ("values-ar", localized)):
                (root / locale).mkdir()
                (root / locale / "strings.xml").write_text(f"<resources>{text}</resources>", encoding="utf-8")
            errors, warnings = [], []
            validate_res_dir(root, errors, warnings, strict_missing=True)
            return errors

    def test_language_specific_plural_categories(self):
        for quantities in (("other",), ("zero", "one", "two", "few", "many", "other")):
            with self.subTest(quantities=quantities):
                items = ''.join(f'<item quantity="{q}">%d عنصر</item>' for q in quantities)
                self.assertEqual([], self.validate(f'<plurals name="count">{items}</plurals>'))

    def test_placeholder_loss_in_one_branch_fails(self):
        errors = self.validate('<plurals name="count"><item quantity="one">عنصر</item><item quantity="other">%d عناصر</item></plurals>')
        self.assertTrue(any('placeholder mismatch' in error for error in errors))

    def test_missing_other_and_duplicate_quantity_fail(self):
        errors = self.validate('<plurals name="count"><item quantity="one">%d</item><item quantity="one">%d</item></plurals>')
        self.assertTrue(any('invalid plural' in error for error in errors))
        self.assertTrue(any('duplicate quantity' in error for error in errors))

    def test_duplicate_resource_and_broken_xml_fail(self):
        self.assertTrue(any('duplicate resource' in error for error in self.validate('<string name="label">a</string><string name="label">b</string>', '<string name="label">label</string>')))
        self.assertTrue(any('invalid XML' in error for error in self.validate('<string name="label">broken')))

    def test_missing_translation_fails(self):
        self.assertTrue(any('missing' in error for error in self.validate('')))


if __name__ == '__main__':
    unittest.main()
