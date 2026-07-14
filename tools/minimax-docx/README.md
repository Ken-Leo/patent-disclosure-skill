# minimax-docx — 精确格式 Word 生成

## 概述

本目录是 [MiniMax-AI/skills](https://github.com/MiniMax-AI/skills) 中 `minimax-docx` 技能的适配副本，用于为本仓库的专利技术交底书生成格式精确的 Word (.docx) 文件。

## 作用

替代 `md_to_docx.py` 的基础 Markdown→Word 转换，通过复制参考示例的样式/主题/编号/页脚/节属性，使输出的 .docx 在字体、字号、行距、公式环境等方面与参考示例（华中科技大学专利技术交底书示例）精确匹配。

## 前置依赖

- **dotnet SDK 8.0+**（macOS: `brew install --cask dotnet-sdk`）
- **python-docx**（`pip install python-docx` 或通过 conda）

## 用法

```bash
# 优先路径：格式精确转换
bash tools/minimax-docx/build_disclosure.sh \
  --markdown "outputs/案件/稿.md" \
  --output "outputs/案件/案件名_时间戳.docx"

# 可指定模板（默认使用 examples/ 下的参考示例）
bash tools/minimax-docx/build_disclosure.sh \
  --markdown "稿.md" \
  --template "examples/参考示例.docx" \
  --output "输出.docx"
```

## 流程

1. `build_disclosure.sh` 调用 `tools/md_to_docx.py` 生成基础 .docx
2. `apply_reference_style.py` 读取基础 .docx 内容、读取参考示例样式
3. 映射段落样式（Heading1→"1"、Heading2→"2"、Normal→"a" 等）
4. 复制参考示例的 styles.xml / theme / numbering / footers / section properties
5. 输出格式精确的 .docx

## 文件说明

| 文件 | 说明 |
|------|------|
| `build_disclosure.sh` | 交底书生成入口脚本 |
| `apply_reference_style.py` | 样式映射与模板应用引擎 |
| `scripts/dotnet/` | C# OpenXML SDK 项目（`$CLI` 命令） |
| `scripts/env_check.sh` | dotnet 环境检测 |
| `scripts/docx_preview.sh` | DOCX 预览 |
| `assets/xsd/` | XSD 校验 schema |
| `references/` | 排版与 OpenXML 参考文档 |

## 降级

若 dotnet 不可用，`build_disclosure.sh` 会自动降级到 `md_to_docx.py` 输出基础 .docx。
