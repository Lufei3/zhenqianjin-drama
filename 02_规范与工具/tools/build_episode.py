#!/usr/bin/env python3
"""
单源事实（SSOT）派生与增量资产派单工具

功能：
1. 读取唯一事实源 shots/<EP>_spec.json
2. 自动派生：
   - shots/<EP>_master.md      （人类可读总控表）
   - shots/<EP>_prompts.md     （可复制的生成提示词）
   - shots/<EP>_assets_todo.json（自动比对 LOCKED*.json 与磁盘后的纯增量缺口派单表）

用法：
  python build_episode.py --ep E01
  python build_episode.py --spec shots/E01_spec.json --root .
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from asset_lock import load_lock_map, sha256_file
from episode_spec import select_shots, shot_durations, shot_refs, video_model


def check_asset_status(root: Path, rel_path: str, lock_map: dict[str, str]) -> str:
    """返回资产状态: locked_ok | unlocked | hash_mismatch | missing"""
    norm = Path(rel_path.replace("\\", "/")).as_posix()
    full_path = root / norm
    if not full_path.is_file():
        return "missing"
    expected_hash = lock_map.get(norm)
    if not expected_hash:
        return "unlocked"
    actual_hash = sha256_file(full_path)
    return "locked_ok" if actual_hash == expected_hash else "hash_mismatch"


def format_presence(presence: str) -> str:
    mapping = {
        "on_screen": "🎬",
        "off_screen": "👂",
        "absent": "❌",
    }
    return mapping.get(presence, presence)


def collect_refs_summary(shot: dict[str, Any]) -> str:
    refs = shot_refs(shot)
    mode = str(shot.get("mode", "A")).upper()
    parts: list[str] = []
    if mode == "A":
        if refs.get("first_frame"):
            parts.append(f"`首帧={refs['first_frame']}`")
    elif mode == "A+":
        if refs.get("first_frame"):
            parts.append(f"`首帧={refs['first_frame']}`")
        if refs.get("last_frame"):
            parts.append(f"`尾帧={refs['last_frame']}`")
    elif mode == "B":
        for item in refs.get("mode_b_refs") or []:
            if isinstance(item, dict):
                alias = item.get("alias", "")
                path = item["path"]
                parts.append(f"`{alias}={path}`" if alias else f"`{path}`")
            elif isinstance(item, str):
                parts.append(f"`{item}`")
    return " ".join(parts) if parts else "（未配置）"


def build_master_md(spec: dict[str, Any]) -> str:
    ep = spec.get("episode", "EXX")
    title = spec.get("title", "")
    platform = spec.get("target_platform") or "未设置"
    model = video_model(spec)
    shots = spec.get("shots", [])
    optional_fields = [
        (field, heading)
        for field, heading in (("shot_goal", "制作目标"), ("first_frame_note", "首帧要求"))
        if any(shot.get(field) for shot in shots)
    ]
    extra_headers = "".join(f" {heading} |" for _, heading in optional_fields)
    lines = [
        f"# {ep} 分镜总控表 — {title}",
        "",
        f"> **自动派生文件**：由 `shots/{ep}_spec.json` 生成。目标平台：`{platform}`。视频模型：`{model}`。",
        "",
        "| Shot | 生成时长 | 剪辑时长 | Cadence | Scene / Angle | Characters | Mode | Audio Mode | Refs | Dialogue | Handoff |" + extra_headers,
        "| :--- | ---: | ---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |" + " :--- |" * len(optional_fields),
    ]
    for shot in shots:
        sid = shot.get("id", "")
        dur, cut_duration = shot_durations(shot)
        cadence = shot.get("cadence", "")
        scene = shot.get("scene", "")
        angle = shot.get("camera_angle", "默认")
        chars = "；".join(
            f"{c.get('name', '')}({c.get('state', '默认')}) {format_presence(c.get('presence', ''))}"
            for c in (shot.get("characters") or [])
        )
        mode = shot.get("mode", "A")
        audio_mode = shot.get("audio_mode", "sfx_only")
        refs_str = collect_refs_summary(shot)
        dialogue = shot.get("dialogue") or "—"
        if shot.get("speaker") and shot.get("dialogue"):
            dialogue = f"{shot['speaker']}：{dialogue}"
        dialogue = dialogue.replace("|", "\\|").replace("\n", "<br>")
        handoff = (shot.get("handoff_note") or "—").replace("|", "\\|").replace("\n", "<br>")
        optional_cells = [
            (shot.get(field) or "—").replace("|", "\\|").replace("\n", "<br>")
            for field, _ in optional_fields
        ]
        lines.append(
            f"| **{sid}** | {dur:g}s | {cut_duration:g}s | {cadence} | {scene} / {angle} | {chars} | {mode} | {audio_mode} | {refs_str} | {dialogue} | {handoff} |"
            + "".join(f" {cell} |" for cell in optional_cells)
        )
    lines.append("")
    return "\n".join(lines)


def build_prompts_md(spec: dict[str, Any]) -> str:
    ep = spec.get("episode", "EXX")
    title = spec.get("title", "")
    aspect_ratio = spec.get("aspect_ratio", "16:9")
    model = video_model(spec)
    lines = [
        f"# {ep} {model} 分镜提示词集 — {title}",
        "",
        f"> **自动派生文件**：由 `shots/{ep}_spec.json` 生成。提交时使用代码块和对应的生成参数、挂载。",
        "",
    ]
    for shot in spec.get("shots", []):
        sid = shot.get("id", "")
        dur, cut_duration = shot_durations(shot)
        mode = str(shot.get("mode", "A")).upper()
        audio_mode = str(shot.get("audio_mode", "sfx_only")).lower()
        refs_str = collect_refs_summary(shot)
        handoff = shot.get("handoff_note") or "无"
        audio_file = shot.get("audio_file")
        dialogue = shot.get("dialogue")
        prompt = (shot.get("video_prompt") or "").strip()

        mode_label = {
            "A": "Mode A (单首帧)",
            "A+": "Mode A+ (首尾双帧)",
            "B": "Mode B (轻量多参)",
        }.get(mode, f"Mode {mode}")

        lines.append(f"## {sid}")
        lines.append(
            f"- **生成参数**：`{model}` ｜ `{mode_label}` ｜ `{aspect_ratio}` ｜ `{dur:g}s`"
        )
        lines.append(f"- **视频挂载**：{refs_str}")
        lines.append(f"- **剪辑时长**：`{cut_duration:g}s` ｜ **声音路线**：`{audio_mode}`")
        if audio_mode == "vo_lipsync" and audio_file:
            audio_line = f"- **后期配音（供对口型和混音）**：`{audio_file}`"
            if dialogue:
                audio_line += f"（台词：“{dialogue}”）"
            lines.append(audio_line)
        lines.append(f"- **衔接（不贴入提示词）**：{handoff}")
        lines.append("")
        lines.append("```text")
        lines.append(prompt)
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def build_assets_todo(spec: dict[str, Any], root: Path) -> dict[str, Any]:
    lock_map = load_lock_map(root)
    ep = spec.get("episode", "EXX")

    pending_by_path: dict[str, tuple[str, dict[str, Any]]] = {}
    todo: dict[str, list[dict[str, Any]]] = {
        "characters": [],
        "scenes": [],
        "props": [],
        "frames": [],
        "sketches": [],
        "audio_vo": [],
    }

    def add_item(bucket: str, path: str, shot_id: str, meta: dict[str, Any]) -> None:
        norm = Path(path.replace("\\", "/")).as_posix()
        usage = {"shot_id": shot_id, "kind": bucket, **meta}
        pending = pending_by_path.get(norm)
        if pending:
            old_bucket, entry = pending
            if shot_id not in entry["used_in_shots"]:
                entry["used_in_shots"].append(shot_id)
            if usage not in entry["usages"]:
                entry["usages"].append(usage)
            if bucket == "frames" and old_bucket != "frames":
                todo[old_bucket].remove(entry)
                entry.update(meta, required_for_video=True)
                todo[bucket].append(entry)
                pending_by_path[norm] = (bucket, entry)
            return

        if bucket in {"sketches", "audio_vo"}:
            if (root / norm).is_file():
                return
            status = "missing"
        else:
            status = check_asset_status(root, norm, lock_map)
        if status == "locked_ok":
            return
        entry = {
            "path": norm,
            "status": status,
            "used_in_shots": [shot_id],
            "required_for_video": bucket == "frames",
            "usages": [usage],
            **meta,
        }
        todo[bucket].append(entry)
        pending_by_path[norm] = (bucket, entry)

    for shot in spec.get("shots", []):
        sid = shot.get("id", "")
        scene = shot.get("scene")
        angle = shot.get("camera_angle") or "默认"
        mode = str(shot.get("mode", "A")).upper()
        refs = shot_refs(shot)
        scene_file = refs.get("scene_plate")
        if "scene_plate" not in refs and scene and mode in {"A", "A+"}:
            angle_suffix = "默认" if angle == "默认" else f"机位_{angle.removeprefix('机位_')}"
            scene_file = f"cast/{scene}.{angle_suffix}.png"
        if scene_file:
            add_item("scenes", scene_file, sid, {"scene": scene, "angle": angle})

        if mode in {"A", "A+"}:
            for ch in shot.get("characters") or []:
                if ch.get("presence") == "on_screen":
                    cname = ch.get("name", "")
                    cstate = ch.get("state") or "默认"
                    if cname:
                        add_item("characters", f"cast/{cname}.{cstate}.png", sid, {"character": cname, "state": cstate})

        for path in refs.get("props") or []:
            if isinstance(path, str) and path:
                add_item("props", path, sid, {})

        if mode in {"A", "A+"} and refs.get("first_frame"):
            add_item("frames", refs["first_frame"], sid, {"frame_role": "first", "scene": scene})
        if mode == "A+" and refs.get("last_frame"):
            add_item("frames", refs["last_frame"], sid, {"frame_role": "last", "scene": scene})
        if mode in {"A", "A+"} and refs.get("sketch"):
            add_item("sketches", refs["sketch"], sid, {"note": "用于首帧构图"})
        if mode == "B":
            for item in refs.get("mode_b_refs") or []:
                path = item.get("path", "") if isinstance(item, dict) else str(item)
                if path:
                    add_item("frames", path, sid, {"frame_role": "mode_b_ref"})

        if str(shot.get("audio_mode", "sfx_only")).lower() == "vo_lipsync":
            audio_file = shot.get("audio_file")
            if isinstance(audio_file, str) and audio_file.strip():
                add_item("audio_vo", audio_file, sid, {
                    "speaker": shot.get("speaker", ""),
                    "shot_id": sid,
                    "dialogue": shot.get("dialogue", ""),
                })

    summary = {k: len(v) for k, v in todo.items()}
    return {
        "episode": ep,
        "title": spec.get("title", ""),
        "summary": summary,
        "total_pending": sum(summary.values()),
        "todo": todo,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="从分镜 JSON 派生总控、提示词与素材缺口表")
    parser.add_argument("--ep", help="集数编号，如 E01（默认读取 shots/<EP>_spec.json）")
    parser.add_argument("--spec", help="显式指定 spec JSON 路径")
    parser.add_argument("--root", default=".", help="项目根目录（默认当前目录）")
    parser.add_argument("--shots", nargs="+", help="仅派生指定镜号，交付写入清单同级的 pilot/ 目录")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.spec:
        spec_path = Path(args.spec)
        if not spec_path.is_absolute():
            spec_path = root / spec_path
    elif args.ep:
        spec_path = root / "shots" / f"{args.ep}_spec.json"
    else:
        print("错误：请指定 --ep E01 或 --spec <path>", file=sys.stderr)
        return 2

    if not spec_path.exists():
        print(f"错误：找不到分镜清单 {spec_path}", file=sys.stderr)
        return 2

    try:
        spec = select_shots(json.loads(spec_path.read_text(encoding="utf-8")), args.shots)
        master = build_master_md(spec)
        prompts = build_prompts_md(spec)
        todo_data = build_assets_todo(spec, root)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    ep = spec.get("episode") or args.ep or spec_path.stem.replace("_spec", "")
    out_dir = spec_path.parent
    if args.shots:
        out_dir = out_dir / "pilot"
        out_dir.mkdir(exist_ok=True)

    master_path = out_dir / f"{ep}_master.md"
    prompts_path = out_dir / f"{ep}_prompts.md"
    todo_path = out_dir / f"{ep}_assets_todo.json"

    master_path.write_text(master, encoding="utf-8")
    prompts_path.write_text(prompts, encoding="utf-8")
    todo_path.write_text(json.dumps(todo_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[OK] 已从 {spec_path.name} 派生：")
    print(f"  - 总控表：{master_path}")
    print(f"  - 提示词：{prompts_path}")
    print(f"  - 增量派单：{todo_path}（待补齐共 {todo_data['total_pending']} 项：{todo_data['summary']}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
