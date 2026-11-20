#!/usr/bin/env python3
"""
build_episode.py (PIPELINE_SPEC v4.0)
单源事实（SSOT）派生与增量资产派单工具

功能：
1. 读取唯一事实源 shots/<EP>_spec.json
2. 自动派生：
   - shots/<EP>_master.md      （人类可读总控表）
   - shots/<EP>_prompts.md     （Seedance 2.5 纯净复制粘贴版提示词）
   - shots/<EP>_assets_todo.json（自动比对 LOCKED*.json 与磁盘后的纯增量缺口派单表）

用法：
  python build_episode.py --ep E01
  python build_episode.py --spec shots/E01_spec.json --root .
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_lock_map(root: Path) -> dict[str, str]:
    """合并 cast/LOCKED.json 与 cast/frames/LOCKED_FRAMES.json 中的路径->哈希映射。"""
    lock_files = [
        root / "cast" / "LOCKED.json",
        root / "cast" / "frames" / "LOCKED_FRAMES.json",
    ]
    merged: dict[str, str] = {}
    for lf in lock_files:
        if not lf.exists():
            continue
        try:
            data = json.loads(lf.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        # 兼容 {path: hash} 或 {"files": {path: {"sha256": ...}}} 两种常见锁表结构
        entries = data.get("files", data) if isinstance(data, dict) else {}
        if isinstance(entries, dict):
            for k, v in entries.items():
                norm_key = k.replace("\\", "/")
                if isinstance(v, str):
                    merged[norm_key] = v
                elif isinstance(v, dict) and isinstance(v.get("sha256"), str):
                    merged[norm_key] = v["sha256"]
    return merged


def check_asset_status(root: Path, rel_path: str, lock_map: dict[str, str]) -> str:
    """返回资产状态: locked_ok | unlocked | hash_mismatch | missing"""
    norm = rel_path.replace("\\", "/")
    full_path = root / norm
    if not full_path.exists():
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
    refs = shot.get("refs") or {}
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
                path = item.get("path", "")
                parts.append(f"`{alias}={path}`")
            elif isinstance(item, str):
                parts.append(f"`{item}`")
    return " ".join(parts) if parts else "（未配置）"


def build_master_md(spec: dict[str, Any]) -> str:
    ep = spec.get("episode", "EXX")
    title = spec.get("title", "")
    platform = spec.get("target_platform", "douyin_hongguo")
    lines = [
        f"# {ep} 分镜总控表 — {title}",
        "",
        f"> **自动派生文件**：由 `shots/{ep}_spec.json` 通过 `build_episode.py` 自动生成，请勿手工修改。目标平台：`{platform}`。",
        "",
        "| Shot | Dur | Cadence | Scene / Angle | Characters | Mode | Audio Mode | Refs | Dialogue | Handoff |",
        "| :--- | ---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for shot in spec.get("shots", []):
        sid = shot.get("id", "")
        dur = shot.get("dur", 0)
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
        dialogue = (shot.get("dialogue") or "—").replace("|", "\\|")
        handoff = (shot.get("handoff_note") or "—").replace("|", "\\|")
        lines.append(
            f"| **{sid}** | {dur}s | {cadence} | {scene} / {angle} | {chars} | {mode} | {audio_mode} | {refs_str} | {dialogue} | {handoff} |"
        )
    lines.append("")
    return "\n".join(lines)


def build_prompts_md(spec: dict[str, Any]) -> str:
    ep = spec.get("episode", "EXX")
    title = spec.get("title", "")
    lines = [
        f"# {ep} Seedance 2.5 即粘分镜提示词集 — {title}",
        "",
        f"> **自动派生文件**：由 `shots/{ep}_spec.json` 生成。代码块内为纯净高信号提示词（≤240字），可直接全选粘贴。",
        "",
    ]
    for shot in spec.get("shots", []):
        sid = shot.get("id", "")
        dur = shot.get("dur", 0)
        cadence = shot.get("cadence", "")
        mode = str(shot.get("mode", "A")).upper()
        audio_mode = shot.get("audio_mode", "sfx_only")
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
            f"- **参数**：`Seedance 2.5` ｜ `{mode_label}` ｜ `16:9` ｜ `{dur}s` ｜ `Audio: {audio_mode}` ｜ `Cadence: {cadence}`"
        )
        mount_line = f"- **挂载**：{refs_str}"
        if audio_mode == "vo_lipsync" and audio_file:
            mount_line += f" ｜ `后期音频`=`{audio_file}`"
            if dialogue:
                mount_line += f"（台词：“{dialogue}”）"
        lines.append(mount_line)
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

    seen: set[tuple[str, str]] = set()
    todo: dict[str, list[dict[str, Any]]] = {
        "characters": [],
        "scenes": [],
        "frames": [],
        "sketches": [],
        "audio_vo": [],
    }

    def add_item(bucket: str, path: str, shot_id: str, meta: dict[str, Any]) -> None:
        norm = path.replace("\\", "/")
        status = check_asset_status(root, norm, lock_map)
        if status == "locked_ok":
            return
        key = (bucket, norm)
        if key in seen:
            # 仅追加引用镜号
            for existing in todo[bucket]:
                if existing["path"] == norm and shot_id not in existing["used_in_shots"]:
                    existing["used_in_shots"].append(shot_id)
            return
        seen.add(key)
        entry = {
            "path": norm,
            "status": status,
            "used_in_shots": [shot_id],
            **meta,
        }
        todo[bucket].append(entry)

    for shot in spec.get("shots", []):
        sid = shot.get("id", "")
        scene = shot.get("scene")
        angle = shot.get("camera_angle") or "默认"
        if scene:
            scene_file = f"cast/{scene}.{angle}.png" if angle == "默认" else f"cast/{scene}.机位_{angle}.png"
            add_item("scenes", scene_file, sid, {"scene": scene, "angle": angle})

        for ch in shot.get("characters") or []:
            if ch.get("presence") == "on_screen":
                cname = ch.get("name", "")
                cstate = ch.get("state") or "默认"
                if cname:
                    add_item("characters", f"cast/{cname}.{cstate}.png", sid, {"character": cname, "state": cstate})

        refs = shot.get("refs") or {}
        if refs.get("first_frame"):
            add_item("frames", refs["first_frame"], sid, {"frame_role": "first", "scene": scene})
        if refs.get("last_frame"):
            add_item("frames", refs["last_frame"], sid, {"frame_role": "last", "scene": scene})
        if refs.get("sketch"):
            add_item("sketches", refs["sketch"], sid, {"note": "仅限0积分生图构图参考，严禁喂给视频模型"})
        for item in refs.get("mode_b_refs") or []:
            path = item.get("path", "") if isinstance(item, dict) else str(item)
            if path:
                add_item("frames", path, sid, {"frame_role": "mode_b_ref"})

        if shot.get("audio_mode") == "vo_lipsync":
            audio_file = shot.get("audio_file") or f"audio/{ep}_{sid}.wav"
            full_audio = root / audio_file
            if not full_audio.exists():
                todo["audio_vo"].append(
                    {
                        "path": audio_file.replace("\\", "/"),
                        "status": "missing",
                        "shot_id": sid,
                        "dialogue": shot.get("dialogue", ""),
                    }
                )

    summary = {k: len(v) for k, v in todo.items()}
    return {
        "episode": ep,
        "title": spec.get("title", ""),
        "summary": summary,
        "total_pending": sum(summary.values()),
        "todo": todo,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="PIPELINE_SPEC v4.0 单源分镜派生与增量派单工具")
    parser.add_argument("--ep", help="集数编号，如 E01（默认读取 shots/<EP>_spec.json）")
    parser.add_argument("--spec", help="显式指定 spec JSON 路径")
    parser.add_argument("--root", default=".", help="项目根目录（默认当前目录）")
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

    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    ep = spec.get("episode") or args.ep or spec_path.stem.replace("_spec", "")
    out_dir = spec_path.parent

    master_path = out_dir / f"{ep}_master.md"
    prompts_path = out_dir / f"{ep}_prompts.md"
    todo_path = out_dir / f"{ep}_assets_todo.json"

    master_path.write_text(build_master_md(spec), encoding="utf-8")
    prompts_path.write_text(build_prompts_md(spec), encoding="utf-8")
    todo_data = build_assets_todo(spec, root)
    todo_path.write_text(json.dumps(todo_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[OK] 已从 {spec_path.name} 派生：")
    print(f"  - 总控表：{master_path}")
    print(f"  - 提示词：{prompts_path}")
    print(f"  - 增量派单：{todo_path}（待补齐共 {todo_data['total_pending']} 项：{todo_data['summary']}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())