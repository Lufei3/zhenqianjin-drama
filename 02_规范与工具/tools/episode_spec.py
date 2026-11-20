"""分镜 JSON 的镜头范围选择。"""


def select_shots(spec: dict, shot_ids: list[str] | None) -> dict:
    if not shot_ids:
        return spec

    requested = set(shot_ids)
    shots = [shot for shot in spec.get("shots", []) if shot.get("id") in requested]
    missing = requested - {shot["id"] for shot in shots}
    if missing:
        raise ValueError(f"清单中没有这些镜号：{', '.join(sorted(missing))}")
    if len(shots) != len(requested):
        raise ValueError("选定范围包含重复镜号，请核对源清单")
    return {**spec, "shots": shots}
