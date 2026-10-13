#!/usr/bin/env python3
"""Validate Android string/plurals locale coverage and placeholder consistency."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


PLACEHOLDER_RE = re.compile(
    r"(?<!%)%(?!%)(?:\d+\$)?[-#+ 0,(<]*\d*(?:\.\d+)?[bBhHsScCdoxXeEfgGaAtTn]"
)
TOOLS_LOCALE = "{http://schemas.android.com/tools}locale"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Android i18n resources.")
    parser.add_argument("--res-dir", action="append", default=[], help="res directory to scan.")
    parser.add_argument("--strict-missing", action="store_true", help="Treat missing localized keys as errors.")
    return parser.parse_args()


def read_xml(path: Path) -> ET.Element | None:
    try:
        return ET.fromstring(path.read_text(encoding="utf-8", errors="replace"))
    except ET.ParseError as exc:
        print(f"ERROR: {path}: XML parse failed: {exc}")
        return None


def placeholders(value: str) -> tuple[str, ...]:
    return tuple(sorted(PLACEHOLDER_RE.findall(value or "")))


def text_of(element: ET.Element) -> str:
    return "".join(element.itertext())


def collect_values(values_dir: Path, errors: list[str]) -> dict[str, tuple[str, object]]:
    result: dict[str, tuple[str, object]] = {}
    for path in values_dir.glob("*.xml"):
        root = read_xml(path)
        if root is None:
            errors.append(f"ERROR: {path}: invalid XML resources")
            continue
        for item in root:
            name = item.attrib.get("name")
            if not name:
                continue
            if item.tag not in {"string", "plurals"} or item.attrib.get("translatable") == "false":
                continue
            key = f"{item.tag}/{name}"
            if key in result:
                errors.append(f"ERROR: {path}: duplicate resource {key}")
            if item.tag == "string":
                if item.attrib.get("translatable") == "false":
                    continue
                value = text_of(item)
                item_placeholders = () if item.attrib.get("formatted") == "false" else placeholders(value)
                result[f"string/{name}"] = (value, item_placeholders)
            elif item.tag == "plurals":
                ph = {}
                for quantity in item.findall("item"):
                    q_name = quantity.attrib.get("quantity", "")
                    if q_name in ph:
                        errors.append(f"ERROR: {path}: duplicate quantity for {key}/{q_name}")
                    ph[q_name] = placeholders(text_of(quantity))
                if "other" not in ph or set(ph) - {"zero", "one", "two", "few", "many", "other"}:
                    errors.append(f"ERROR: {path}: invalid plural quantities for {key}")
                result[f"plurals/{name}"] = ("plurals", ph)
    return result


def declared_default_locale(values_dir: Path) -> str | None:
    for path in values_dir.glob("*.xml"):
        root = read_xml(path)
        if root is not None and root.attrib.get(TOOLS_LOCALE):
            return root.attrib[TOOLS_LOCALE].replace("_", "-")
    return None


def locale_of_values_dir(path: Path) -> str:
    qualifier = path.name.removeprefix("values-")
    if qualifier.startswith("b+"):
        return qualifier.removeprefix("b+").replace("+", "-")
    return qualifier.replace("-r", "-")


def is_locale_values_dir(path: Path) -> bool:
    qualifier = path.name.removeprefix("values-")
    if qualifier.startswith("b+"):
        return True
    first = qualifier.split("-")[0]
    return bool(re.fullmatch(r"[a-z]{2,3}", first))


def validate_res_dir(res_dir: Path, errors: list[str], warnings: list[str], strict_missing: bool) -> None:
    default_dir = res_dir / "values"
    if not default_dir.is_dir():
        warnings.append(f"WARN: {res_dir}: missing default values directory.")
        return
    default_values = collect_values(default_dir, errors)
    if not default_values:
        warnings.append(f"WARN: {default_dir}: no string/plurals resources found.")
        return
    default_locale = declared_default_locale(default_dir)
    locale_dirs = sorted(path for path in res_dir.glob("values-*") if path.is_dir() and is_locale_values_dir(path))
    for locale_dir in locale_dirs:
        localized = collect_values(locale_dir, errors)
        missing = sorted(set(default_values) - set(localized))
        extra = sorted(set(localized) - set(default_values))
        is_default_locale_override = default_locale == locale_of_values_dir(locale_dir)
        if missing and not is_default_locale_override:
            target = errors if strict_missing else warnings
            prefix = "ERROR" if strict_missing else "WARN"
            target.append(f"{prefix}: {locale_dir}: missing {len(missing)} localized key(s): {', '.join(missing[:10])}")
        if extra:
            warnings.append(f"WARN: {locale_dir}: extra localized key(s) not in default values: {', '.join(extra[:10])}")
        for key in sorted(set(default_values) & set(localized)):
            default_meta = default_values[key]
            locale_meta = localized[key]
            if key.startswith("plurals/"):
                # 各语言的复数类别不同；逐分支检查，不要求与英语类别相同。
                quantities = locale_meta[1]
                if "other" not in quantities or set(quantities) - {"zero", "one", "two", "few", "many", "other"}:
                    errors.append(f"ERROR: {locale_dir}: invalid plural quantities for {key}")
                for quantity, ph in quantities.items():
                    expected = default_meta[1].get(quantity, default_meta[1].get("other", ()))
                    if ph != expected:
                        errors.append(f"ERROR: {locale_dir}: placeholder mismatch for {key}/{quantity}: {ph} != {expected}")
            elif default_meta[1] != locale_meta[1]:
                errors.append(f"ERROR: {locale_dir}: placeholder mismatch for {key}: {locale_meta[1]} != {default_meta[1]}")


def validate_raw_html(res_dir: Path, errors: list[str], warnings: list[str]) -> None:
    raw_dirs = [path for path in res_dir.glob("raw*") if path.is_dir()]
    html_files = [path for raw_dir in raw_dirs for path in raw_dir.glob("*.html")]
    if not html_files:
        return
    node = shutil.which("node")
    script_re = re.compile(r"<script[^>]*>(?P<script>[\s\S]*?)</script>", re.I)
    for path in html_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        scripts = [match.group("script").strip() for match in script_re.finditer(text) if match.group("script").strip()]
        if not scripts:
            continue
        if node is None:
            warnings.append(f"WARN: {path}: script tag found but Node.js is unavailable; raw HTML script syntax was not checked.")
            continue
        for index, script in enumerate(scripts, start=1):
            result = subprocess.run(
                [node, "-e", f"new Function({script!r});"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            if result.returncode != 0:
                errors.append(f"ERROR: {path}: script #{index} syntax check failed: {result.stderr.strip()}")


def main() -> int:
    args = parse_args()
    errors: list[str] = []
    warnings: list[str] = []
    res_dirs = [Path(path) for path in args.res_dir]
    if not res_dirs:
        res_dirs = [Path("app/src/main/res"), Path("feature/feature_res/src/main/res")]
    for res_dir in res_dirs:
        if res_dir.exists():
            validate_res_dir(res_dir, errors, warnings, args.strict_missing)
            validate_raw_html(res_dir, errors, warnings)
    for item in warnings:
        print(item)
    for item in errors:
        print(item)
    if errors:
        print(f"i18n validation failed: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"i18n validation passed: {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
