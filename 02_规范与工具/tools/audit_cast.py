#!/usr/bin/env python3
"""
资产设定卡提交前检查。
在把任何 cast/<角色|场景|道具>.md 写入通用画布节点前执行，任一项违例即返回退出码 1 阻断。

用法：
  python 02_规范与工具/tools/audit_cast.py cast/主角.md
  python 02_规范与工具/tools/audit_cast.py cast/
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_style_line(label: str) -> str | None:
    """读取已经登记的风格句。"""
    readme = ROOT / "README.md"
    if not readme.exists():
        return None
    text = readme.read_text(encoding="utf-8")
    match = re.search(rf"^### {re.escape(label)}[ \t]*\n(?:[ \t]*\n)*>[ \t]*(.+)$", text, flags=re.M)
    if not match:
        return None
    line = match.group(1).strip().strip("`")
    return line if line and "<<" not in line and ">>" not in line else None


def is_blocking_prompt(*parts: str) -> bool:
    blob = "\n".join(parts)
    return "白模" in blob and "人偶" in blob

# 仅针对角色基础三视图（## 默认）的「纯人物空手无外挂铁律」违禁词（§4.1）
CLEAN_BASE_FORBIDDEN_PROPS = [
    "手持", "手握", "握持", "竖握", "反握", "怀抱", "抱持", "背负", "斜挎", "挎着",
    "武器", "拐杖", "手杖", "短棍", "骨角矛", "骨矛", "长矛", "战矛", "石斧", "小刀",
    "扳手", "螺丝刀", "工具袋", "工具包", "双肩包", "背包", "登山包", "手册", "书本", "玉米袋",
]

# 所有资产提交小节通用违禁模式
COMMON_FORBIDDEN = [
    (r"镜头", "规则5.0：提交正文严禁出现「镜头」二字"),
    (r"\bcamera\b", "规则5.0：提交正文严禁出现 camera"),
    (r"\blens\b", "规则5.0：提交正文严禁出现 lens"),
    (r"暴怒|极度震惊|仰天嚎哭|嚎叫", "规则3：禁用抽象强情绪词"),
    (r"\b(furious|horrified|wailing hysterically|terrified|enraged)\b", "规则3：禁用英文抽象强情绪词"),
    (r"不要|绝不|没有|严禁", "规则6：提交正文默认用正向描述，避免否定句反向召回"),
    (r"\b(8k|masterpiece|perfect face|best quality|unreal engine)\b", "规则11：禁止无效画质词堆砌，请用具体物理材质微瑕疵描述"),
    (r"<<|>>|<!--", "§1.1-2：提交正文严禁残留占位符 << >> 或 HTML 注释"),
]


def detect_kind(text: str, explicit_kind: str | None) -> str:
    if explicit_kind:
        return explicit_kind
    setup_match = re.search(r"^## 设定\s*\n(.*?)(?=^## |\Z)", text, flags=re.M | re.S)
    setup = setup_match.group(1) if setup_match else ""
    if re.search(r"分级[：:].*(主角|配角|反派)", setup) or "角色三视图设计展板" in text:
        return "character"
    if re.search(r"空间类型[：:]", setup) or "全景" in setup:
        return "scene"
    return "prop_or_creature"


def parse_sections(text: str) -> list[tuple[str, str]]:
    parts = re.split(r"^## ([^\r\n]+)\s*$", text, flags=re.M)[1:]
    return [(h.strip(), b.strip()) for h, b in zip(parts[0::2], parts[1::2])]


def audit_one(md_path: Path, explicit_kind: str | None = None) -> list[str]:
    issues: list[str] = []
    text = md_path.read_text(encoding="utf-8")
    kind = detect_kind(text, explicit_kind)
    style_label = "资产风格句" if kind == "character" else "全片风格句"
    approved_style = load_style_line(style_label)
    sections = parse_sections(text)
    setup = next((body for heading, body in sections if heading == "设定"), "")
    is_portrait = re.search(r"参考版式[：:]\s*定妆照\b", setup) is not None

    submit_sections = [(h, b) for h, b in sections if h != "设定"]
    if not submit_sections:
        return [f"[{md_path.name}] 未找到可提交的小节（如 ## 默认）"]

    char_name = md_path.stem

    for heading, body in submit_sections:
        tag = f"{md_path.name}#{heading}"
        non_empty_lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
        if not non_empty_lines:
            issues.append(f"[{tag}] 小节正文为空")
            continue

        # 1. 首句风格句校验（白模站位图、720 全景是两种例外）
        first_line = non_empty_lines[0]
        blocking = is_blocking_prompt(heading, body)
        uses_style = kind == "character" or (not blocking and not (kind == "scene" and heading == "全景720"))
        if uses_style:
            if approved_style is None:
                issues.append(f"[{tag}] 请先在 README.md 登记已确认的「{style_label}」")
            elif first_line != approved_style:
                issues.append(f"[{tag}] 首句必须逐字使用 README.md 的「{style_label}」")
            elif body.count(approved_style) > 1:
                issues.append(f"[{tag}] 「{style_label}」只能使用一次")

        # 2. 通用违禁词校验
        for pat, reason in COMMON_FORBIDDEN:
            if re.search(pat, body, flags=re.I):
                issues.append(f"[{tag}] 命中违禁模式 `{pat}` -> {reason}")

        # 3. 角色专属校验
        if kind == "character":
            if heading == "默认":
                # §4.1 纯人物空手无外挂铁律
                hit_props = [w for w in CLEAN_BASE_FORBIDDEN_PROPS if w in body]
                if hit_props:
                    issues.append(
                        f"[{tag}] §4.1 纯人物空手铁律违例：基础三视图严禁出现手持/外挂道具词 {hit_props}（请移至派生变体）"
                    )
                layout_terms = ("定妆照",) if is_portrait else ("三视图", "正面", "侧面", "背面")
                for term in layout_terms:
                    if term not in body:
                        issues.append(f"[{tag}] 基础角色卡缺少版式要素「{term}」")
                if re.search(r"\{\{[^}]+\}\}", body):
                    issues.append(f"[{tag}] 基础角色卡不应包含 {{{{别名}}}} 引用")
            else:
                # §4.2 派生形态/变体锁脸前缀校验
                expected_ref = f"{{{{{char_name}}}}}"
                if expected_ref not in body or "同一角色的基础形象" not in body:
                    issues.append(
                        f"[{tag}] §4.2：角色派生形态必须引用 {expected_ref} 并包含标准锁脸前缀「是同一角色的基础形象」"
                    )

    return issues


def main():
    parser = argparse.ArgumentParser(description="资产设定卡提交前检查")
    parser.add_argument("target", help="单个 .md 文件路径或 cast/ 目录路径")
    parser.add_argument("--kind", choices=["character", "scene", "prop_or_creature"], default=None, help="手动指定资产类型")
    parser.add_argument("--only-characters", action="store_true", help="扫描目录时仅审计角色设定卡")
    args = parser.parse_args()

    target = Path(args.target)
    if not target.exists():
        print(f"[错误] 路径不存在: {target}")
        sys.exit(1)

    files = sorted(target.glob("*.md")) if target.is_dir() else [target]
    all_issues: list[str] = []
    checked = 0

    for f in files:
        if f.name.lower() == "readme.md":
            continue
        if args.only_characters:
            if detect_kind(f.read_text(encoding="utf-8"), None) != "character":
                continue
        checked += 1
        all_issues.extend(audit_one(f, explicit_kind=args.kind))

    if all_issues:
        print(f"[资产预检拦截] 共检查 {checked} 个设定文件，发现 {len(all_issues)} 处违例：")
        for idx, item in enumerate(all_issues, 1):
            print(f"  {idx}. {item}")
        sys.exit(1)

    print(f"[资产预检通过] 共 {checked} 个设定文件通过。")
    sys.exit(0)


if __name__ == "__main__":
    main()
