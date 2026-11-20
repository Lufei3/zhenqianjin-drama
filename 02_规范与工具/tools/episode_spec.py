"""分镜 JSON 的公共字段和镜头范围选择。"""

import math
import re

DEFAULT_VIDEO_MODEL = "Seedance 2.5"
ID_RE = re.compile(r"\w[\w.-]*")


def shots_with_ids(spec: dict) -> list[dict]:
    if not isinstance(spec, dict):
        raise ValueError("分镜清单必须是 JSON 对象")

    episode = spec.get("episode")
    if episode is not None and (not isinstance(episode, str) or not ID_RE.fullmatch(episode)):
        raise ValueError("episode 必须是可用于文件名的集号，例如 E01")

    shots = spec.get("shots")
    if not isinstance(shots, list) or not shots:
        raise ValueError("shots 必须是非空镜头列表")

    seen = set()
    for index, shot in enumerate(shots, start=1):
        if not isinstance(shot, dict):
            raise ValueError(f"shots 第 {index} 项必须是镜头对象")
        shot_id = shot.get("id")
        if not isinstance(shot_id, str) or not ID_RE.fullmatch(shot_id):
            raise ValueError(f"shots 第 {index} 项的 id 必须是有效镜号，例如 S01")
        if shot_id in seen:
            raise ValueError(f"镜号重复：{shot_id}")
        seen.add(shot_id)
    return shots


def video_model(spec: dict) -> str:
    model = spec.get("video_model", DEFAULT_VIDEO_MODEL)
    if not isinstance(model, str) or not model.strip():
        raise ValueError("video_model 必须是非空模型名")
    return model.strip()


def positive_duration(value, field: str) -> float:
    try:
        seconds = float(value) if not isinstance(value, bool) else 0
    except (TypeError, ValueError, OverflowError):
        seconds = 0
    if not math.isfinite(seconds) or seconds <= 0:
        raise ValueError(f"{field} 必须是大于零的有限秒数")
    return seconds


def shot_durations(shot: dict) -> tuple[float, float]:
    dur = positive_duration(shot.get("dur"), "dur")
    cut_duration = positive_duration(shot["cut_duration"], "cut_duration") if "cut_duration" in shot else dur
    if cut_duration > dur:
        raise ValueError("cut_duration 不能超过生成时长 dur")
    return dur, cut_duration


def shot_refs(shot: dict) -> dict:
    refs = shot.get("refs")
    if refs is None:
        return {}
    if not isinstance(refs, dict):
        raise ValueError("refs 必须是对象")

    for field in ("first_frame", "last_frame", "scene_plate", "sketch"):
        path = refs.get(field)
        if path is not None and (not isinstance(path, str) or (path and not path.strip())):
            raise ValueError(f"refs.{field} 必须是素材路径")

    props = refs.get("props")
    if props is not None and (not isinstance(props, list) or any(not isinstance(path, str) or not path.strip() for path in props)):
        raise ValueError("refs.props 必须是非空路径组成的列表")

    mode_b_refs = refs.get("mode_b_refs")
    if mode_b_refs is not None:
        if not isinstance(mode_b_refs, list):
            raise ValueError("refs.mode_b_refs 必须是参考图列表")
        for ref in mode_b_refs:
            path = ref.get("path") if isinstance(ref, dict) else ref
            if not isinstance(path, str) or not path.strip():
                raise ValueError("refs.mode_b_refs 每项都必须指定参考图路径")
            if isinstance(ref, dict) and ref.get("alias") is not None and not isinstance(ref["alias"], str):
                raise ValueError("refs.mode_b_refs 的 alias 必须是字符串")
    return refs


def select_shots(spec: dict, shot_ids: list[str] | None) -> dict:
    shots = shots_with_ids(spec)
    if not shot_ids:
        return spec

    requested = set(shot_ids)
    if len(requested) != len(shot_ids):
        raise ValueError("--shots 包含重复镜号")
    selected = [shot for shot in shots if shot["id"] in requested]
    missing = requested - {shot["id"] for shot in selected}
    if missing:
        raise ValueError(f"清单中没有这些镜号：{', '.join(sorted(missing))}")
    return {**spec, "shots": selected}
