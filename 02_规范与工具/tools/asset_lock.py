#!/usr/bin/env python3
"""
阶段 3.5 锁版、阶段 4.5 接力帧与第 9 节典范层的 SHA-256 校验。阶段 2.5 只是分镜语法预检，不在本脚本。
支持锁版文件：
  - cast/LOCKED.json               (核心角色/场景/道具资产锁版)
  - cast/frames/LOCKED_FRAMES.json (原画质接力帧/首尾帧锁版)
  - cast/blocking/LOCKED_BLOCKING.json (彩色白模站位图锁版)
  - cast/canon/CANON.json          (跨集长剧典范总清单，记录 *.默认.png 与 *全景*.png)

用法：
  python 02_规范与工具/tools/asset_lock.py lock --scope all --reason "说明"
  python 02_规范与工具/tools/asset_lock.py lock --scope frames --file cast/frames/E01_S01_first.png
  python 02_规范与工具/tools/asset_lock.py verify --scope all
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import sys
import tempfile
from pathlib import Path

SCOPES = {
    "cast": (Path("cast"), Path("cast/LOCKED.json"), Path("cast/old"), lambda p: p.suffix.lower() == ".png"),
    "frames": (Path("cast/frames"), Path("cast/frames/LOCKED_FRAMES.json"), Path("cast/frames/old"), lambda p: p.suffix.lower() == ".png"),
    "blocking": (Path("cast/blocking"), Path("cast/blocking/LOCKED_BLOCKING.json"), Path("cast/blocking/old"), lambda p: p.suffix.lower() == ".png"),
    "canon": (
        Path("cast"),
        Path("cast/canon/CANON.json"),
        Path("cast/canon/old"),
        lambda p: p.suffix.lower() == ".png" and (".默认." in p.name or "全景" in p.name),
    ),
}


def lock_entries(data: dict) -> dict:
    """读取当前 assets、旧版 files 或旧版平铺映射。"""
    entries = data.get("assets", data.get("files", data))
    if not isinstance(entries, dict):
        raise ValueError("锁版清单的资产映射必须是对象")
    return entries


def entry_hash(value) -> str | None:
    digest = value.get("sha256") if isinstance(value, dict) else value
    return digest if isinstance(digest, str) else None


def load_lock_map(root: Path) -> dict[str, str]:
    """按项目相对路径索引可用于视频的已锁资产。"""
    hashes: dict[str, str] = {}
    for scope in ("cast", "frames"):
        src_dir, lock_file, _, _ = SCOPES[scope]
        try:
            data = json.loads((root / lock_file).read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                continue
            entries = lock_entries(data)
        except (OSError, ValueError):
            continue

        for name, value in entries.items():
            if entries is data and name in {"scope", "locked_at", "reason"}:
                continue
            digest = entry_hash(value)
            if digest:
                path = Path(name.replace("\\", "/"))
                key = src_dir / path if path.parent == Path(".") else path
                hashes[key.as_posix()] = digest
    return hashes


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def asset_record(path: Path) -> dict:
    stat = path.stat()
    return {
        "sha256": sha256_file(path),
        "size_bytes": stat.st_size,
        "mtime_iso": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    }


def scan_scope(scope_name: str) -> dict:
    src_dir, _, _, matcher = SCOPES[scope_name]
    src_dir.mkdir(parents=True, exist_ok=True)
    assets = {}
    for p in sorted(src_dir.iterdir()):
        if not p.is_file() or not matcher(p):
            continue
        assets[p.name] = asset_record(p)
    return assets


def locked_assets(data: dict, src_dir: Path) -> dict:
    assets = {}
    for name, value in lock_entries(data).items():
        path = Path(name.replace("\\", "/"))
        digest = entry_hash(value)
        if digest and path.suffix.lower() == ".png" and path.parent in (Path("."), src_dir):
            assets[path.name] = value if isinstance(value, dict) else {"sha256": digest}
    return assets


def lock_one(scope_name: str, reason: str, files: list[Path] | None = None) -> int:
    src_dir, lock_file, old_dir, _ = SCOPES[scope_name]
    lock_file.parent.mkdir(parents=True, exist_ok=True)

    prev_version = 0
    old_contents = None
    assets = {}
    if lock_file.exists():
        try:
            contents = lock_file.read_text(encoding="utf-8")
            old_data = json.loads(contents)
            if not isinstance(old_data, dict):
                raise ValueError("锁版清单必须是对象")
            prev_version = int(old_data.get("lock_version", 0))
            if files is not None:
                assets = locked_assets(old_data, src_dir)
            old_contents = contents
        except (OSError, TypeError, ValueError) as e:
            if files is not None:
                print(f"[阻断:{scope_name}] 无法保留旧锁版清单：{e}", file=sys.stderr)
                return 1
            print(f"[警告:{scope_name}] 读取旧锁版失败，将新建 v1: {e}")
            prev_version = 0

    if files is None:
        assets = scan_scope(scope_name)
    else:
        assets.update({path.name: asset_record(path) for path in files})

    if old_contents is not None:
        old_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%dT%H%M")
        archive_path = old_dir / f"{lock_file.stem}_v{prev_version}_{ts}.json"
        archive_path.write_text(old_contents, encoding="utf-8")
        print(f"[归档:{scope_name}] 旧锁版已备份至: {archive_path}")

    lock_data = {
        "scope": scope_name,
        "lock_version": prev_version + 1,
        "locked_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "reason": reason,
        "asset_count": len(assets),
        "assets": assets,
    }
    with tempfile.TemporaryDirectory(dir=lock_file.parent) as tmp_dir:
        pending_lock = Path(tmp_dir) / lock_file.name
        pending_lock.write_text(json.dumps(lock_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        pending_lock.replace(lock_file)
    print(f"[锁版成功:{scope_name}] v{lock_data['lock_version']} 共锁定 {len(assets)} 项 -> {lock_file}")
    return 0


def verify_one(scope_name: str, allow_untracked: bool = False) -> int:
    src_dir, lock_file, _, matcher = SCOPES[scope_name]
    if not lock_file.exists():
        if scope_name == "blocking" and not any(matcher(path) and path.is_file() for path in src_dir.glob("*")):
            print(f"[跳过:{scope_name}] 站位图目录暂无文件且未生成锁版。")
            return 0
        print(f"[阻断:{scope_name}] 未找到锁版文件 {lock_file}！请先运行 `python 02_规范与工具/tools/asset_lock.py lock --scope {scope_name}`。")
        return 1

    try:
        lock_data = json.loads(lock_file.read_text(encoding="utf-8"))
        if not isinstance(lock_data, dict):
            raise ValueError("锁版清单必须是对象")
        entries = locked_assets(lock_data, src_dir)
    except (OSError, ValueError) as e:
        print(f"[阻断:{scope_name}] 无法读取锁版清单：{e}", file=sys.stderr)
        return 1
    current_assets = scan_scope(scope_name)

    missing = [n for n in entries if n not in current_assets]
    mismatched = [
        (n, entries[n]["sha256"][:12], current_assets[n]["sha256"][:12])
        for n in entries
        if n in current_assets and current_assets[n]["sha256"] != entries[n]["sha256"]
    ]
    untracked = [n for n in current_assets if n not in entries]

    if missing or mismatched or (untracked and not allow_untracked):
        print(f"[阻断报警:{scope_name}] 哈希校验未通过（锁版 v{lock_data.get('lock_version')}）！")
        for m in missing:
            print(f"  [缺失] {m}")
        for name, exp, got in mismatched:
            print(f"  [哈希变更] {name}: 锁版={exp}... != 当前={got}...")
        for u in untracked:
            print(f"  [未锁版新增] {u}")
        return 1

    print(f"[校验通过:{scope_name}] {len(entries)} 项资产 SHA-256 100% 匹配（v{lock_data.get('lock_version')}）。")
    return 0


def main():
    parser = argparse.ArgumentParser(description="资产/接力帧/站位图/典范层 SHA-256 锁版工具")
    sub = parser.add_subparsers(dest="action", required=True)

    p_lock = sub.add_parser("lock", help="生成或升级锁版 JSON")
    p_lock.add_argument("--scope", choices=["cast", "frames", "blocking", "canon", "all"], default="cast")
    p_lock.add_argument("--reason", default="阶段验收锁版冻结")
    p_lock.add_argument("--file", type=Path, action="append", help="仅锁定指定资产，路径相对项目根目录（可重复）")

    p_ver = sub.add_parser("verify", help="比对当前文件与锁版 JSON")
    p_ver.add_argument("--scope", choices=["cast", "frames", "blocking", "canon", "all"], default="all")
    p_ver.add_argument("--allow-untracked", action="store_true")

    args = parser.parse_args()
    files = getattr(args, "file", None)
    if files:
        if args.scope == "all":
            p_lock.error("使用 --file 时请指定单一 --scope")
        src_dir, _, _, matcher = SCOPES[args.scope]
        for path in files:
            if path.parent != src_dir or path.is_symlink() or not path.is_file() or not matcher(path):
                p_lock.error(f"未找到 {src_dir} 目录下可锁定的资产：{path}")
    targets = ["cast", "frames", "blocking", "canon"] if args.scope == "all" else [args.scope]

    rc = 0
    for t in targets:
        r = lock_one(t, args.reason, files) if args.action == "lock" else verify_one(t, args.allow_untracked)
        if r != 0:
            rc = r
    sys.exit(rc)


if __name__ == "__main__":
    main()
