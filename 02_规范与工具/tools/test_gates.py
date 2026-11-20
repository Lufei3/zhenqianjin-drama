#!/usr/bin/env python3
"""本地门禁自检。在仓库根目录运行：python 02_规范与工具/tools/test_gates.py"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from audit_shots import audit_episode
from build_episode import build_assets_todo

TOOLS = Path(__file__).resolve().parent
TEMPLATE = TOOLS.parent / "templates" / "05_单源分镜JSON_模板.json"


def main() -> None:
    spec = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    shot = spec["shots"][0]
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        errors, _ = audit_episode(spec, root, pre_mode=True)
        if errors:
            raise SystemExit(f"模板预检应通过：{errors}")

        errors, _ = audit_episode(spec, root, pre_mode=False)
        if not any("E10 挂载资产不存在" in error for error in errors):
            raise SystemExit(f"应拦截缺失首帧：{errors}")

        frame = Path(shot["refs"]["first_frame"])
        (root / frame).parent.mkdir(parents=True)
        (root / frame).write_bytes(b"image fixture")
        subprocess.run(
            [
                sys.executable, str(TOOLS / "asset_lock.py"),
                "lock", "--scope", "frames", "--file", str(frame),
            ],
            cwd=root,
            check=True,
        )
        errors, _ = audit_episode(spec, root, pre_mode=False)
        if errors or build_assets_todo(spec, root)["todo"]["frames"]:
            raise SystemExit(f"首帧已锁版，应通过生产检查并移出派单：{errors}")

        (root / frame).write_bytes(b"changed fixture")
        errors, _ = audit_episode(spec, root, pre_mode=False)
        if not any("E10 资产哈希不匹配" in error for error in errors):
            raise SystemExit(f"应拦截已变更首帧：{errors}")

    print("[门禁自检通过] JSON 预检、缺少首帧、锁版与派单、哈希变更。")


if __name__ == "__main__":
    main()
