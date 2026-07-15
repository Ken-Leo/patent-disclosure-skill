#!/usr/bin/env python3
"""
模板填充工具：以参考示例 DOCX 为模板，替换内容，保留全部格式。

用法:
  python3 template_fill.py --template 参考示例.docx --content content.json --output 新.docx
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


NSMAP = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def _register_ns():
    for pfx, uri in NSMAP.items():
        ET.register_namespace(pfx, uri)
    ET.register_namespace("", "http://schemas.openxmlformats.org/wordprocessingml/2006/main")


_register_ns()

SECTION_MARKERS = [
    "说明书摘要", "摘要附图", "权利要求书", "说明书",
    "技术领域", "背景技术", "发明内容", "附图说明",
    "具体实施方式", "说明书附图",
]


def _get_text(p) -> str:
    return "".join(t.text or "" for t in p.iter(f"{W}t")).strip()


def _clone_pPr_rPr(para, body):
    """
    从段落克隆 pPr 和 rPr 模板。
    注意：必须在段落被从 body 移除前调用，否则 find() 因命名空间丢失而失效。
    """
    pPr = para.find(f"{W}pPr")
    pPr_copy = copy.deepcopy(pPr) if pPr is not None else None

    first_run = para.find(f"{W}r")
    rPr = first_run.find(f"{W}rPr") if first_run is not None else None
    rPr_copy = copy.deepcopy(rPr) if rPr is not None else None

    return pPr_copy, rPr_copy


def _make_paragraph(pPr_copy, rPr_copy, text: str) -> ET.Element:
    """用模板格式创建新段落"""
    p = ET.Element(f"{W}p")
    if pPr_copy is not None:
        p.append(copy.deepcopy(pPr_copy))
    r = ET.SubElement(p, f"{W}r")
    if rPr_copy is not None:
        r.append(copy.deepcopy(rPr_copy))
    else:
        # 默认 rPr
        rPr = ET.SubElement(r, f"{W}rPr")
        sz = ET.SubElement(rPr, f"{W}sz")
        sz.set(f"{W}val", "28")
        szCs = ET.SubElement(rPr, f"{W}szCs")
        szCs.set(f"{W}val", "28")
    t = ET.SubElement(r, f"{W}t")
    t.text = text
    t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    return p


def fill_template(template_bytes: bytes, content: dict) -> bytes:
    with zipfile.ZipFile(io.BytesIO(template_bytes), "r") as tz:
        template_data = {n: tz.read(n) for n in tz.namelist()}

    doc_root = ET.fromstring(template_data["word/document.xml"])
    body = doc_root.find(f".//{W}body")

    # 构建章节标记映射
    all_paras = list(body.iter(f"{W}p"))
    section_map: dict[str, tuple[int, ET.Element]] = {}
    for pi, p in enumerate(all_paras):
        t = _get_text(p)
        if t in SECTION_MARKERS:
            section_map[t] = (pi, p)

    # 按顺序处理章节
    for sec_name in SECTION_MARKERS:
        if sec_name not in content:
            continue
        if sec_name not in section_map:
            print(f"  警告: 模板中无章节 [{sec_name}]")
            continue

        sec_content = content[sec_name]
        new_lines = []
        if isinstance(sec_content, str):
            new_lines = [l for l in sec_content.split("\n") if l.strip()]
        else:
            new_lines = list(sec_content)
        if not new_lines:
            continue

        current_paras = list(body.iter(f"{W}p"))
        marker_idx, marker_para = section_map[sec_name]
        # 刷新标记位置
        current_marker_pos = current_paras.index(marker_para)
        content_start = current_marker_pos + 1

        # 找下一个章节标记
        content_end = len(current_paras) - 1
        for j in range(content_start, len(current_paras)):
            if _get_text(current_paras[j]) in SECTION_MARKERS:
                content_end = j - 1
                break

        old_paras = current_paras[content_start:content_end + 1] if content_start <= content_end else []

        # ★ 关键: 在删除前克隆格式模板 ★
        fmt_para = None
        for op in old_paras:
            if op.find(f"{W}r") is not None:
                fmt_para = op
                break
        if fmt_para is None:
            fmt_para = marker_para  # 用标记段落作为格式参考

        pPr_tpl, rPr_tpl = _clone_pPr_rPr(fmt_para, body)

        print(f"  [{sec_name}] 替换 {len(old_paras)} 段 → {len(new_lines)} 段")

        # 删除旧段落（从后往前）
        for op in reversed(old_paras):
            body.remove(op)

        # 插入新段落
        current_marker_pos = list(body.iter(f"{W}p")).index(marker_para)
        for li, line_text in enumerate(new_lines):
            new_p = _make_paragraph(pPr_tpl, rPr_tpl, line_text)
            body.insert(current_marker_pos + 1 + li, new_p)

    template_data["word/document.xml"] = ET.tostring(
        doc_root, xml_declaration=True, encoding="unicode"
    ).encode("utf-8")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as out_z:
        for n, d in template_data.items():
            out_z.writestr(n, d)
    return buf.getvalue()


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--template", "-t", required=True)
    p.add_argument("--content", "-c")
    p.add_argument("--output", "-o", required=True)
    p.add_argument("--set", "-s", action="append", metavar="SECTION=TEXT")
    return p.parse_args()


def main():
    args = _parse_args()
    tp = Path(args.template)
    op = Path(args.output)
    if not tp.is_file():
        print(f"错误: {tp}", file=sys.stderr)
        return 1
    content = {}
    if args.content:
        with open(args.content) as f:
            content = json.load(f)
    if args.set:
        for s in args.set:
            if "=" in s:
                k, v = s.split("=", 1)
                content[k] = v
    if not content:
        print("错误: 无内容", file=sys.stderr)
        return 1
    result = fill_template(tp.read_bytes(), content)
    op.parent.mkdir(parents=True, exist_ok=True)
    op.write_bytes(result)
    print(f"\n✓ {op} ({len(result)//1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
