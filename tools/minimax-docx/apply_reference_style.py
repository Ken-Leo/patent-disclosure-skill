#!/usr/bin/env python3
"""
Apply reference example styles to a basic DOCX disclosure document.

Reads a basic DOCX (produced by md_to_docx.py with Heading1/2/3/Normal styles),
maps those styles to the reference example's numeric style IDs, and copies
the reference's styles.xml, theme, numbering, footers, and section properties
to produce a document that matches the reference format exactly.

Usage:
  python3 apply_reference_style.py --input basic.docx --template reference.docx --output final.docx
"""

from __future__ import annotations

import argparse
import copy
import io
import re
import shutil
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


def _parse_args():
    p = argparse.ArgumentParser(description="Apply reference example styles to a DOCX")
    p.add_argument("--input", "-i", required=True, help="Basic DOCX from md_to_docx.py")
    p.add_argument("--template", "-t", required=True, help="Reference example DOCX")
    p.add_argument("--output", "-o", required=True, help="Output DOCX path")
    return p.parse_args()


NSMAP = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "wp": "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "pic": "http://schemas.openxmlformats.org/drawingml/2006/picture",
    "mc": "http://schemas.openxmlformats.org/markup-compatibility/2006",
}

STYLE_MAP = {
    "Heading1": "1",
    "Heading2": "2",
    "Heading3": "3",
    "Heading4": "3",
    "Heading5": "3",
    "Heading6": "3",
    "Normal": "a",
    "ListBullet": "a",
    "ListNumber": "a",
    "BodyText": "a",
}


def _register_namespaces():
    for prefix, uri in NSMAP.items():
        ET.register_namespace(prefix, uri)
    ET.register_namespace("", "http://schemas.openxmlformats.org/wordprocessingml/2006/main")


def _read_part(z: zipfile.ZipFile, path: str) -> bytes | None:
    if path in z.namelist():
        return z.read(path)
    return None


def _build_output(input_bytes: bytes, template_bytes: bytes, style_map: dict[str, str]) -> bytes:
    """
    Build the output DOCX as bytes by:
    1. Starting with input as base
    2. Mapping styles in document.xml
    3. Replacing styles/theme/numbering/footers/sectPr from template
    """
    _register_namespaces()

    # Read both ZIPs into memory
    with zipfile.ZipFile(io.BytesIO(input_bytes), "r") as input_z:
        input_names = input_z.namelist()
        input_data = {name: input_z.read(name) for name in input_names}

    with zipfile.ZipFile(io.BytesIO(template_bytes), "r") as template_z:
        template_names = template_z.namelist()
        template_data = {name: template_z.read(name) for name in template_names}

    # Start with all input files
    output_data = dict(input_data)

    # Map styles in document.xml
    if "word/document.xml" in output_data:
        doc_xml = output_data["word/document.xml"]
        root = ET.fromstring(doc_xml)
        body = root.find(".//w:body", NSMAP)
        if body is not None:
            for para in body.iter(f"{{{NSMAP['w']}}}p"):
                pPr = para.find(f"{{{NSMAP['w']}}}pPr")
                if pPr is None:
                    continue
                pStyle = pPr.find(f"{{{NSMAP['w']}}}pStyle")
                if pStyle is not None and pStyle.get(f"{{{NSMAP['w']}}}val") in style_map:
                    src = pStyle.get(f"{{{NSMAP['w']}}}val")
                    pStyle.set(f"{{{NSMAP['w']}}}val", style_map[src])
            output_data["word/document.xml"] = ET.tostring(
                root, xml_declaration=True, encoding="unicode"
            ).encode("utf-8")
        print("  Mapped: paragraph styles (e.g., Heading1→1, Normal→a)")

    # Replace styles.xml from template
    if "word/styles.xml" in template_data:
        output_data["word/styles.xml"] = template_data["word/styles.xml"]
        print("  Copied: styles.xml from template")

    # Replace theme
    if "word/theme/theme1.xml" in template_data:
        output_data["word/theme/theme1.xml"] = template_data["word/theme/theme1.xml"]
        print("  Copied: theme from template")

    # Replace numbering
    if "word/numbering.xml" in template_data:
        output_data["word/numbering.xml"] = template_data["word/numbering.xml"]
        print("  Copied: numbering from template")

    # Copy header/footer files from template
    header_footer_pattern = re.compile(r"word/(header|footer)\d*\.xml")
    header_footer_rels_pattern = re.compile(r"word/_rels/(header|footer)\d*\.xml\.rels")
    for name in template_names:
        if header_footer_pattern.match(name) or name in ("word/header.xml", "word/footer.xml"):
            output_data[name] = template_data[name]
        if header_footer_rels_pattern.match(name):
            output_data[name] = template_data[name]

    # Copy section properties from template's document.xml
    if "word/document.xml" in template_data:
        t_root = ET.fromstring(template_data["word/document.xml"])
        t_body = t_root.find(".//w:body", NSMAP)
        if t_body is not None:
            t_sectPrs = t_body.findall(f"{{{NSMAP['w']}}}sectPr")
            if t_sectPrs:
                our_root = ET.fromstring(output_data["word/document.xml"])
                our_body = our_root.find(".//w:body", NSMAP)
                if our_body is not None:
                    # Remove existing section properties from our body
                    for sp in our_body.findall(f"{{{NSMAP['w']}}}sectPr"):
                        our_body.remove(sp)
                    # Copy from template
                    for sp in t_sectPrs:
                        our_body.append(copy.deepcopy(sp))
                    output_data["word/document.xml"] = ET.tostring(
                        our_root, xml_declaration=True, encoding="unicode"
                    ).encode("utf-8")
                print("  Copied: section properties from template")

    # Add any missing [Content_Types].xml entries for headers/footers
    if "[Content_Types].xml" in output_data:
        ct_root = ET.fromstring(output_data["[Content_Types].xml"])
        ct_ns = "http://schemas.openxmlformats.org/package/2006/content-types"
        known_parts = {e.get("PartName", "") for e in ct_root.iter(f"{{{ct_ns}}}Override")}
        for name in output_data:
            if name.startswith("word/") and name.endswith(".xml") and f"/{name}" not in known_parts:
                # Determine content type
                if "header" in name:
                    ct = "application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"
                elif "footer" in name:
                    ct = "application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"
                else:
                    continue
                ET.SubElement(ct_root, f"{{{ct_ns}}}Override", {
                    "PartName": f"/{name}",
                    "ContentType": ct,
                })
        output_data["[Content_Types].xml"] = ET.tostring(
            ct_root, xml_declaration=True, encoding="unicode"
        ).encode("utf-8")

    # Write output ZIP
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as out_z:
        for name, data in output_data.items():
            out_z.writestr(name, data)

    return buf.getvalue()


def main():
    args = _parse_args()
    input_path = Path(args.input)
    template_path = Path(args.template)
    output_path = Path(args.output)

    if not input_path.is_file():
        print(f"Error: input not found: {input_path}", file=sys.stderr)
        return 1
    if not template_path.is_file():
        print(f"Error: template not found: {template_path}", file=sys.stderr)
        return 1

    input_bytes = input_path.read_bytes()
    template_bytes = template_path.read_bytes()

    output_bytes = _build_output(input_bytes, template_bytes, STYLE_MAP)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(output_bytes)
    print(f"\n✓ Output: {output_path} ({len(output_bytes) // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
