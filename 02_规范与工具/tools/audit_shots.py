#!/usr/bin/env python3
"""
audit_shots.py (PIPELINE_SPEC v4.0)
瘦身版自动化门禁校验工具（10 条硬红线 Error + 5 条软提醒 Warning）

用法：
  # 阶段 1.5 预检（跳过磁盘文件与哈希锁校验）
  python audit_shots.py shots/E01_spec.json --pre

  # 阶段 3 开拍前全量终审（启用磁盘、音频时长与 SHA-256 哈希锁校验）
  python audit_shots.py shots/E01_spec.json --root .
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import wave
from pathlib import Path
from typing import Any

from asset_lock import load_lock_map, sha256_file
from episode_spec import select_shots

# 硬红线词库
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
NATIVE_DURATIONS = {2.0, 2.5, 3.0, 4.0, 5.0}
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


def dialogue_net_chars(dialogue: str) -> tuple[int, int]:
    """返回 (有效汉字/字母数字字数, 停顿标点数)。"""
    pause_count = len(re.findall(r"[，,、；;……]", dialogue))
    clean = re.sub(r"[\s，,。\.！!？?、；;：“”\"「」…\-—]", "", dialogue)
    return len(clean), pause_count


def audit_episode(spec: dict[str, Any], root: Path, pre_mode: bool) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    lock_map = {} if pre_mode else load_lock_map(root)

    aspect_ratio = spec.get("aspect_ratio", "16:9")
    if aspect_ratio not in ("16:9", "9:16"):
        errors.append(f"[GLOBAL] aspect_ratio 必须为 16:9 或 9:16（当前为 {aspect_ratio!r}）")

    shots = spec.get("shots") or []
    if not shots:
        errors.append("[GLOBAL] shots 列表为空")
        return errors, warnings

    mode_b_count = 0
    dur_streak = 0
    last_dur: float | None = None

    for shot in shots:
        sid = shot.get("id", "UNKNOWN")
        dur = float(shot.get("dur") or 0)
        mode = str(shot.get("mode", "A")).upper()
        audio_mode = str(shot.get("audio_mode", "sfx_only")).lower()
        prompt = shot.get("video_prompt") or ""
        dialogue = (shot.get("dialogue") or "").strip()
        refs = shot.get("refs") or {}

        # --- E1: Prompt 净字数上限 (≤240) ---
        char_len = net_char_count(prompt)
        if char_len > MAX_PROMPT_CHARS:
            errors.append(
                f"[{sid}] E1 Prompt 过长：{char_len} 字（硬上限 {MAX_PROMPT_CHARS} 字，防注意力稀释）"
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
            mode_b_count += 1
            for item in refs.get("mode_b_refs") or []:
                if isinstance(item, dict):
                    if item.get("path"):
                        video_ref_paths.append(item["path"])
                    if item.get("alias"):
                        alias = item["alias"]
                        mode_b_aliases.add(alias if alias.startswith("@") else f"@{alias}")
                elif isinstance(item, str):
                    video_ref_paths.append(item)

        # --- E2: 禁止向视频模型投喂白模与草图 ---
        for p in video_ref_paths:
            norm_p = p.replace("\\", "/")
            for bad in FORBIDDEN_REF_TOKENS:
                if bad in norm_p:
                    errors.append(f"[{sid}] E2 禁止挂载非视频资产路径：{norm_p}（命中 {bad}）")

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
            mb = refs.get("mode_b_refs") or []
            if len(mb) == 0 or len(mb) > 3:
                errors.append(f"[{sid}] E4 Mode B 挂载参考图数量必须为 1–3 张（当前 {len(mb)} 张）")
            if refs.get("first_frame") or refs.get("last_frame"):
                errors.append(f"[{sid}] E4 Mode B 不可与 first_frame/last_frame 混用")
            missing_in_refs = prompt_aliases - mode_b_aliases
            if missing_in_refs:
                errors.append(f"[{sid}] E4 Mode B 正文 @别名未在挂载列表声明：{sorted(missing_in_refs)}")
        else:
            errors.append(f"[{sid}] E4 未知生成模式：{mode}（仅支持 A / A+ / B）")

        # --- E5: native 模式台词字数公式校验 ---
        if audio_mode not in {"native", "sfx_only", "vo_lipsync"}:
            errors.append(f"[{sid}] E5 未知音频模式：{audio_mode}（仅支持 native / sfx_only / vo_lipsync）")
        elif audio_mode == "native":
            if not dialogue:
                warnings.append(f"[{sid}] native 模式未填写 dialogue 字段")
            else:
                d_chars, pauses = dialogue_net_chars(dialogue)
                max_limit = max(0, math.floor((dur - 0.8) * 5.0 - 1.5 * pauses))
                if d_chars > max_limit:
                    errors.append(
                        f"[{sid}] E5 台词字数越界：{d_chars} 字（含 {pauses} 处停顿），{dur}s 镜头极限上限 {max_limit} 字"
                    )
        elif audio_mode == "sfx_only" and dialogue:
            errors.append(f"[{sid}] E5 sfx_only 模式不可填写台词：{dialogue}")

        # --- E6: vo_lipsync 音频先行校验 ---
        if audio_mode == "vo_lipsync":
            audio_file = shot.get("audio_file")
            if not isinstance(audio_file, str) or Path(audio_file).suffix.lower() != ".wav":
                errors.append(f"[{sid}] E6 vo_lipsync 模式必须指定 WAV 格式的 audio_file")
            elif not pre_mode:
                af_path = root / audio_file.replace("\\", "/")
                if not af_path.is_file():
                    errors.append(f"[{sid}] E6 找不到前置配音文件：{audio_file}")
                else:
                    wav_dur = get_wav_duration(af_path)
                    if wav_dur is None:
                        errors.append(f"[{sid}] E6 前置配音不是可读取的非空 WAV 文件：{audio_file}")
                    elif dur < wav_dur + 0.5:
                        errors.append(
                            f"[{sid}] E6 视频时长 {dur}s 短于配音 {wav_dur:.2f}s + 0.5s 气口要求"
                        )
            if QUOTED_DIALOGUE_RE.search(prompt):
                errors.append(f"[{sid}] E6 vo_lipsync 模式的 video_prompt 严禁包含引号台词（应保持闭口表演）")

        # --- E7: 字面染色与 BGM 红线 ---
        lower_prompt = prompt.lower()
        for w in DYEING_AND_BGM_WORDS:
            if w.lower() in lower_prompt:
                errors.append(f"[{sid}] E7 命中字面染色或 BGM 红线词：「{w}」")

        # --- E8: 绝对视线红线 ---
        for w in GAZE_REDLINE_WORDS:
            if w in prompt:
                errors.append(f"[{sid}] E8 命中视线红线词：「{w}」")

        # --- E9: 无字幕声明 ---
        if "无字幕" not in prompt and "不要生成旁白字幕" not in prompt:
            errors.append(f"[{sid}] E9 缺少「无字幕」约束声明")

        # --- E10: 哈希锁版校验（生产模式） ---
        if not pre_mode:
            for p in video_ref_paths:
                norm_p = Path(p.replace("\\", "/")).as_posix()
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
            if w in prompt:
                warnings.append(f"[{sid}] W1 含粉红大象/防御词「{w}」，建议改写为纯正向视觉描述")

        # --- W2: 拍子时间总和偏差 ---
        beats = BEAT_RANGE_RE.findall(prompt)
        if beats:
            max_end = max(float(end) for _, end in beats)
            if abs(max_end - dur) > 0.15:
                warnings.append(f"[{sid}] W2 拍子结束时间 {max_end}s 与镜头时长 {dur}s 不一致")

        # --- W3: 连续 4 镜同长预警 ---
        if last_dur is not None and abs(dur - last_dur) < 1e-6:
            dur_streak += 1
            if dur_streak >= 4:
                warnings.append(f"[{sid}] W3 已连续 {dur_streak} 镜为 {dur}s，建议调整呼吸节拍")
        else:
            dur_streak = 1
            last_dur = dur

        # --- W4: 非原生甜点档位预警 ---
        if dur not in NATIVE_DURATIONS:
            warnings.append(f"[{sid}] W4 时长 {dur}s 非推荐模型甜点档 {sorted(NATIVE_DURATIONS)}")

    # --- W5: Mode B 占比过高预警 ---
    if len(shots) >= 4 and (mode_b_count / len(shots)) > 0.20:
        pct = (mode_b_count / len(shots)) * 100
        warnings.append(
            f"[GLOBAL] W5 Mode B 占比达 {pct:.1f}%（>{20}%），建议尽量转为 Mode A 写实首帧以控成本与稳画质"
        )

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="PIPELINE_SPEC v4.0 自动化门禁校验工具")
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
    print(f"=== audit_shots v4.0 [{mode_tag}] : {spec_path.name} ===")
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
