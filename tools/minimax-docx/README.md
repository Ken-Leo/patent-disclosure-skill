# minimax-docx — 精确格式 Word 生成

## 概述

本目录是 [MiniMax-AI/skills](https://github.com/MiniMax-AI/skills) 中 `minimax-docx` 技能的适配副本，用于为本仓库的专利技术交底书生成格式精确的 Word (.docx) 文件。

## 作用

替代 `md_to_docx.py` 的基础 Markdown→Word 转换，通过复制参考示例的样式/主题/编号/页脚/节属性，使输出的 .docx 在字体、字号、行距、公式环境等方面与参考示例（华中科技大学专利技术交底书示例）精确匹配。

## 前置依赖

- **dotnet SDK 8.0+**（macOS: `brew install --cask dotnet-sdk`）
- **python-docx**（`pip install python-docx` 或通过 conda）

## 用法

### 方式一：Python template_fill（无需 dotnet）

```bash
# 准备内容 JSON
cat > content.json << SLASH_EOF
{
  "技术领域": "本发明属于...",
  "背景技术": "现有技术...",
  "发明内容": "本发明提供...",
  "权利要求书": ["1、一种...方法", "S1、..."]
}
SLASH_EOF

# 填充模板
python3 tools/minimax-docx/template_fill.py \
  --template "examples/参考示例.docx" \
  --content content.json \
  --output "outputs/交底书.docx"
```

### 方式二：C# base-replace（格式保留更精确，需 dotnet 8.0+）

```bash
# 内容 JSON 格式同方式一
dotnet run --project tools/minimax-docx/scripts/dotnet/MiniMaxAIDocx.Cli -- base-replace \
  --template "examples/参考示例.docx" \
  --content content.json \
  --output "outputs/交底书.docx"
```

特点：使用 OpenXML SDK 进行 in-place 文本替换，清除旧内容时保留段落格式（pPr）完整，
对含复杂公式（oMath）的段落也能正确处理。

### 内容 JSON 格式

支持的章节键（只填需要替换的即可）：

| JSON 键 | 值类型 | 说明 |
|---------|--------|------|
| `"说明书摘要"` | 字符串 | 摘要文本 |
| `"技术领域"` | 字符串 | 技术领域段落 |
| `"背景技术"` | 字符串 | 背景技术段落 |
| `"发明内容"` | 字符串 | 发明内容段落 |
| `"附图说明"` | 字符串 | 附图说明段落 |
| `"具体实施方式"` | 字符串 | 具体实施方式段落 |
| `"权利要求书"` | 数组 | 每项一条权利要求 |

字符串中的 `\n` 会被识别为段落换行；数组每一项为一个独立段落。


## 流程

1. `template_fill.py`（Python）或 `base-replace`（C#）以参考示例 DOCX 为模板
2. 删除目标章节的旧内容段落
3. 插入新内容段落，保留原段落格式（pPr、rPr、行距、缩进、字体、字号等）
4. PNG 图示通过 `tools/mermaid_render.py` 预先渲染后在模板中引用
5. 输出 .docx（9 张图、5 个页脚、分节符等全部保留）

## 文件说明

| 文件 | 说明 |
|------|------|
| `template_fill.py` | Python 模板填充工具（无需 dotnet） |
| `base-replace` (C# CLI) | C# OpenXML SDK 模板填充命令（需 dotnet 8.0+） |
| `scripts/dotnet/` | C# OpenXML SDK 项目（`$CLI` 命令） |
| `scripts/env_check.sh` | dotnet 环境检测 |
| `scripts/docx_preview.sh` | DOCX 预览 |
| `assets/xsd/` | XSD 校验 schema |
| `references/` | 排版与 OpenXML 参考文档 |

## 降级

若 dotnet 不可用，`template_fill.py`（Python 版）可不依赖 dotnet 直接使用。
