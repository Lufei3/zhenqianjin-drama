#!/usr/bin/env python3
"""
检查分镜数据、视频挂载和外配音频的开拍条件。

用法：
  # 分镜预检（跳过磁盘文件与哈希锁校验）
  python audit_shots.py shots/E01_spec.json --pre

  # 开拍前检查实际文件、音频时长与 SHA-256 锁版
  python audit_shots.py shots/E01_spec.json --root .
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import wave
from pathlib import Path
from typing import Any

from asset_lock import load_lock_map, sha256_file
from episode_spec import select_shots, shot_durations, shot_refs, shots_with_ids, video_model

FORBIDDEN_REF_TOKENS = ("blocking/", "sketch/", "storyboard/", ".director.")
PLACEHOLDER_RE = re.compile(r"\{\{[^}]+\}\}|<<[^>]+>>|\bTBD\b", re.IGNORECASE)
DYEING_AND_BGM_WORDS = (
    "脸红",
    "涨红",
    "脸色惨白",
    "面无血色",
    "眼前一黑",
    "眼前发黑",
    "暴怒",
    "咬牙切齿",
    "BGM",
    "背景音乐",
    "配乐",
    "music",
    "score",
)
GAZE_REDLINE_WORDS = ("正视前方", "直视前方", "看向观众", "面向正前方", "看着对方")
QUOTED_DIALOGUE_RE = re.compile(r"[「“\"][^」”\"]{2,}[」”\"]")
ALIAS_RE = re.compile(r"@[\u4e00-\u9fa5A-Za-z0-9_]+")

# 软提醒词库与正则
PINK_ELEPHANT_WORDS = ("不要", "避免", "留在参考图里", "调色漂移", "塑料")
BEAT_RANGE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*[–\-~]\s*(\d+(?:\.\d+)?)\s*(?:s|秒)")
MAX_PROMPT_CHARS = 240


def get_wav_duration(path: Path) -> float | None:
    try:
        with wave.open(str(path), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if frames <= 0 or rate <= 0:
                return None
            bytes_per_frame = wf.getnchannels() * wf.getsampwidth()
            remaining = frames
            while remaining > 0:
                count = min(remaining, 8192)
                if len(wf.readframes(count)) != count * bytes_per_frame:
                    return None
                remaining -= count
            return frames / rate
    except (wave.Error, EOFError, OSError):
        return None


def net_char_count(text: str) -> int:
    """统计去除空白换行后的净字数。"""
    return len(re.sub(r"\s+", "", text))


def without_ordered_dialogue(prompt: str, dialogue: str) -> str | None:
    """核对原句出场顺序，返回除去原句的描述。"""
    compact_prompt = re.sub(r"\s+", "", prompt)
    unmatched = []
    offset = 0
    for raw_line in dialogue.splitlines():
        line = re.sub(r"\s+", "", raw_line)
        if not line:
            continue
        start = compact_prompt.find(line, offset)
        if start == -1:
            return None
        unmatched.append(compact_prompt[offset:start])
        offset = start + len(line)
    unmatched.append(compact_prompt[offset:])
    return " ".join(unmatched)


def audit_episode(spec: dict[str, Any], root: Path, pre_mode: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        shots = shots_with_ids(spec)
        model = video_model(spec)
    except ValueError as error:
        return [f"[GLOBAL] {error}"], warnings

    if PLACEHOLDER_RE.search(model):
        errors.append("[GLOBAL] video_model 尚未填写实际模型名")

    aspect_ratio = spec.get("aspect_ratio", "16:9")
    if aspect_ratio not in ("16:9", "9:16"):
        errors.append(f"[GLOBAL] aspect_ratio 必须为 16:9 或 9:16（当前为 {aspect_ratio!r}）")

    lock_map = {} if pre_mode else load_lock_map(root)

    for shot in shots:
        sid = shot["id"]
        try:
            dur, cut_duration = shot_durations(shot)
            refs = shot_refs(shot)
        except ValueError as error:
            errors.append(f"[{sid}] {error}")
            continue

        mode = str(shot.get("mode", "A")).upper()
        audio_mode = str(shot.get("audio_mode", "sfx_only")).lower()
        prompt = shot.get("video_prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            errors.append(f"[{sid}] E1 video_prompt 必须填写实际生成指令")
            continue
        dialogue = shot.get("dialogue")
        if dialogue is not None and not isinstance(dialogue, str):
            errors.append(f"[{sid}] E5 dialogue 必须是字符串")
            continue
        dialogue = (dialogue or "").strip()
        style_text = without_ordered_dialogue(prompt, dialogue) if audio_mode == "native" else prompt

        char_len = net_char_count(prompt)
        if char_len > MAX_PROMPT_CHARS:
            warnings.append(
                f"[{sid}] Prompt 为 {char_len} 字，超过仓库建议的 {MAX_PROMPT_CHARS} 字，请按实际入口限制精简"
            )

        # 收集实际挂载给视频模型的路径
        video_ref_paths: list[str] = []
        mode_b_aliases: set[str] = set()
        if mode == "A":
            if refs.get("first_frame"):
                video_ref_paths.append(refs["first_frame"])
        elif mode == "A+":
            if refs.get("first_frame"):
                video_ref_paths.append(refs["first_frame"])
            if refs.get("last_frame"):
                video_ref_paths.append(refs["last_frame"])
        elif mode == "B":
            for item in refs.get("mode_b_refs") or []:
                if isinstance(item, dict):
                    video_ref_paths.append(item["path"])
                    if item.get("alias"):
                        alias = item["alias"] if item["alias"].startswith("@") else f"@{item['alias']}"
                        if not ALIAS_RE.fullmatch(alias) or alias in mode_b_aliases:
                            errors.append(f"[{sid}] E4 Mode B 的挂载别名无效或重复：{alias}")
                        mode_b_aliases.add(alias)
                else:
                    video_ref_paths.append(item)

        # --- E2: 禁止向视频模型投喂白模与草图 ---
        video_ref_paths = [Path(path.replace("\\", "/")).as_posix() for path in video_ref_paths]
        if mode == "B" and len(set(video_ref_paths)) != len(video_ref_paths):
            errors.append(f"[{sid}] E4 Mode B 的参考图路径不能重复")
        for norm_p in video_ref_paths:
            for bad in FORBIDDEN_REF_TOKENS:
                if bad in norm_p.lower():
                    errors.append(f"[{sid}] E2 禁止挂载非视频资产路径：{norm_p}（命中 {bad}）")
            if PLACEHOLDER_RE.search(norm_p):
                errors.append(f"[{sid}] E3 挂载路径包含占位符：{norm_p}")

        # --- E3: 未解析占位符清零 ---
        ph_match = PLACEHOLDER_RE.search(prompt)
        if ph_match:
            errors.append(f"[{sid}] E3 存在未解析占位符：{ph_match.group(0)}")

        # --- E4: 模式与挂载一致性 ---
        prompt_aliases = set(ALIAS_RE.findall(prompt))
        if mode == "A":
            if not refs.get("first_frame") or refs.get("last_frame") or (refs.get("mode_b_refs") or []):
                errors.append(f"[{sid}] E4 Mode A 必须且仅能挂载 1 张 first_frame")
            if prompt_aliases:
                errors.append(f"[{sid}] E4 Mode A 正文严禁出现 @别名：{sorted(prompt_aliases)}")
        elif mode == "A+":
            if not refs.get("first_frame") or not refs.get("last_frame") or (refs.get("mode_b_refs") or []):
                errors.append(f"[{sid}] E4 Mode A+ 必须同时挂载 first_frame 与 last_frame，且不可混用 mode_b_refs")
            if prompt_aliases:
                errors.append(f"[{sid}] E4 Mode A+ 正文严禁出现 @别名：{sorted(prompt_aliases)}")
        elif mode == "B":
            if not video_ref_paths:
                errors.append(f"[{sid}] E4 Mode B 至少需要 1 张参考图，数量上限以生成入口为准")
            if refs.get("first_frame") or refs.get("last_frame"):
                errors.append(f"[{sid}] E4 Mode B 不可与 first_frame/last_frame 混用")
            missing_in_refs = prompt_aliases - mode_b_aliases
            if missing_in_refs:
                errors.append(f"[{sid}] E4 Mode B 正文 @别名未在挂载列表声明：{sorted(missing_in_refs)}")
        else:
            errors.append(f"[{sid}] E4 未知生成模式：{mode}（仅支持 A / A+ / B）")

        # --- E5: 台词与音频路线一致 ---
        if audio_mode not in {"native", "sfx_only", "vo_lipsync"}:
            errors.append(f"[{sid}] E5 未知音频模式：{audio_mode}（仅支持 native / sfx_only / vo_lipsync）")
        elif audio_mode in {"native", "vo_lipsync"} and not dialogue:
            errors.append(f"[{sid}] E5 {audio_mode} 模式需填写原台词 dialogue")
        elif audio_mode == "native" and style_text is None:
            errors.append(f"[{sid}] E5 native 模式的提示词须按顺序包含 dialogue 原句")
        elif audio_mode == "sfx_only" and dialogue:
            errors.append(f"[{sid}] E5 sfx_only 模式不可填写台词：{dialogue}")
        if PLACEHOLDER_RE.search(dialogue):
            errors.append(f"[{sid}] E3 dialogue 包含未解析占位符")

        # --- E6: vo_lipsync 音频先行校验 ---
        if audio_mode == "vo_lipsync":
            audio_file = shot.get("audio_file")
            if not isinstance(audio_file, str) or Path(audio_file).suffix.lower() != ".wav":
                errors.append(f"[{sid}] E6 vo_lipsync 模式必须指定 WAV 格式的 audio_file")
            elif PLACEHOLDER_RE.search(audio_file):
                errors.append(f"[{sid}] E6 audio_file 包含未解析占位符")
            elif not pre_mode:
                af_path = root / audio_file.replace("\\", "/")
                if not af_path.is_file():
                    errors.append(f"[{sid}] E6 找不到前置配音文件：{audio_file}")
                else:
                    wav_dur = get_wav_duration(af_path)
                    if wav_dur is None:
                        errors.append(f"[{sid}] E6 前置配音不是可读取的非空 WAV 文件：{audio_file}")
                    else:
                        if dur < wav_dur + 0.5:
                            errors.append(f"[{sid}] E6 生成时长 {dur}s 短于配音 {wav_dur:.2f}s + 0.5s 气口要求")
                        if "cut_duration" in shot and cut_duration < wav_dur:
                            warnings.append(f"[{sid}] 剪辑时长 {cut_duration}s 短于配音 {wav_dur:.2f}s，请核对跨镜对白和实际入点")
            if QUOTED_DIALOGUE_RE.search(prompt):
                errors.append(f"[{sid}] E6 vo_lipsync 模式的 video_prompt 严禁包含引号台词（应保持闭口表演）")

        # 风格提醒只检查生成描述，保留原台词措辞。
        style_text = prompt if style_text is None else style_text
        lower_prompt = style_text.lower()
        for w in DYEING_AND_BGM_WORDS:
            if w.lower() in lower_prompt:
                warnings.append(f"[{sid}] 提示词含「{w}」，请核对是否需要生成对应颜色、情绪或音乐")

        for w in GAZE_REDLINE_WORDS:
            if w in style_text:
                warnings.append(f"[{sid}] 提示词含「{w}」，请核对画内视线目标")

        # --- E9: 无字幕声明 ---
        if "无字幕" not in prompt and "不要生成旁白字幕" not in prompt:
            errors.append(f"[{sid}] E9 缺少「无字幕」约束声明")

        # --- E10: 哈希锁版校验（生产模式） ---
        if not pre_mode:
            for norm_p in dict.fromkeys(video_ref_paths):
                full_p = root / norm_p
                if not full_p.is_file():
                    errors.append(f"[{sid}] E10 挂载资产不存在：{norm_p}")
                    continue
                expected = lock_map.get(norm_p)
                if not expected:
                    errors.append(f"[{sid}] E10 资产尚未锁版（未录入 LOCKED*.json）：{norm_p}")
                else:
                    actual = sha256_file(full_p)
                    if actual != expected:
                        errors.append(f"[{sid}] E10 资产哈希不匹配（疑似被篡改）：{norm_p}")

        # --- W1: 粉红大象词预警 ---
        for w in PINK_ELEPHANT_WORDS:
            if w in style_text:
                warnings.append(f"[{sid}] 提示词含「{w}」，可检查是否能直接写出所需画面")

        for start, end in BEAT_RANGE_RE.findall(style_text):
            if float(start) >= float(end) or float(end) > dur:
                errors.append(f"[{sid}] 提示词时间段 {start}–{end}s 超出生成范围或顺序无效（生成时长 {dur}s）")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="分镜数据、挂载和前置配音检查")
    parser.add_argument("spec", help="分镜单源清单路径，如 shots/E01_spec.json")
    parser.add_argument("--root", default=".", help="项目根目录（默认当前目录）")
    parser.add_argument("--pre", action="store_true", help="预检模式：跳过磁盘资产与哈希锁校验")
    parser.add_argument("--shots", nargs="+", help="仅检查指定镜号，例如 --shots S01 S02")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    spec_path = Path(args.spec)
    if not spec_path.is_absolute():
        spec_path = root / spec_path

    if not spec_path.exists():
        print(f"错误：找不到分镜清单 {spec_path}", file=sys.stderr)
        return 2

    try:
        spec = select_shots(json.loads(spec_path.read_text(encoding="utf-8")), args.shots)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    errors, warnings = audit_episode(spec, root, pre_mode=args.pre)

    mode_tag = "预检模式 (--pre)" if args.pre else "开拍前检查"
    print(f"=== audit_shots [{mode_tag}] : {spec_path.name} ===")
    if args.shots:
        print(f"镜头范围：{', '.join(shot['id'] for shot in spec['shots'])}")

    if warnings:
        print(f"\n[WARNINGS: {len(warnings)}]")
        for w in warnings:
            print(f"  ⚠️  {w}")

    if errors:
        print(f"\n[ERRORS: {len(errors)}]")
        for e in errors:
            print(f"  ❌ {e}")
        print("\n结论：红灯拦截，请修复以上 Error 后重新校验。")
        return 1

    print("\n结论：绿灯放行（0 Error）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
