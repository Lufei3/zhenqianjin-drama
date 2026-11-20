#!/usr/bin/env python3
"""
02_规范与工具/tools/slice_grid.py
场景四宫格多机位展板无损切片工具（对齐 PIPELINE_SPEC v3.5 · SCN-<place>-GRID）

数学原理：
  16:9 画幅图像横纵各平分（2x2 四宫格），每一格的宽高比严格保持 16:9（如 3840x2160 -> 四张 1920x1080）。
  单次在通用画布生成一张四宫格展板，即可零积分无损切出 4 个标准电影机位！

标准四宫格布局：
  - 左上 (top-left)    : 反打机位 (Reverse Angle)
  - 右上 (top-right)   : 俯视机位 (Top-Down / Overhead Angle)
  - 左下 (bottom-left) : 左侧机位 (Left Side Angle)
  - 右下 (bottom-right): 右侧机位 (Right Side Angle)

用法：
  python 02_规范与工具/tools/slice_grid.py --input cast/维修铺.多机位展板.png
  # 自定义输出命名：
  python 02_规范与工具/tools/slice_grid.py --input cast/红松林.多机位展板.png --names 反打 俯视 左侧 右侧
"""

import argparse
import sys
from pathlib import Path
from PIL import Image


def slice_2x2_grid(input_path: Path, output_names: list[str], output_dir: Path = None, prefix: str = None) -> int:
    if not input_path.exists():
        print(f"[错误] 输入文件不存在: {input_path}")
        return 1

    if len(output_names) != 4:
        print(f"[错误] 切片命名列表必须包含 4 个名称（当前 {len(output_names)} 个）")
        return 1

    try:
        # 使用 PIL 打开以获得对各种颜色空间与 Unicode 路径的原生支持
        img = Image.open(input_path)
    except Exception as e:
        print(f"[错误] 无法读取图片 {input_path}: {e}")
        return 1

    w, h = img.size
    print(f"[读取展板] {input_path.name} | 尺寸: {w}x{h} (比例: {w/h:.3f})")

    mid_x = w // 2
    mid_y = h // 2

    # 四个切片区域 (left, upper, right, lower)
    boxes = [
        ("左上", (0, 0, mid_x, mid_y)),
        ("右上", (mid_x, 0, w, mid_y)),
        ("左下", (0, mid_y, mid_x, h)),
        ("右下", (mid_x, mid_y, w, h)),
    ]

    out_folder = output_dir if output_dir else input_path.parent
    out_folder.mkdir(parents=True, exist_ok=True)

    # 推导前缀：如 维修铺.多机位展板.png -> 维修铺.机位_
    if prefix is None:
        base_name = input_path.stem
        for suffix in [".多机位展板", ".四宫格", ".多视角", ".展板", ".grid"]:
            if base_name.endswith(suffix):
                base_name = base_name[: -len(suffix)]
                break
        prefix = f"{base_name}.机位_"

    created_files = []
    for (pos_name, box), name in zip(boxes, output_names):
        slice_img = img.crop(box)
        sw, sh = slice_img.size
        out_filename = f"{prefix}{name}.png"
        out_path = out_folder / out_filename
        slice_img.save(out_path, format="PNG")
        created_files.append(out_path)
        print(f"  [切片成功] {pos_name} -> {out_path.name} ({sw}x{sh}, 比例: {sw/sh:.3f})")

    print(f"\n[全部完成] 成功从 {input_path.name} 切割出 4 个标准 16:9 机位图！")
    print(f"提示：请运行 `python 02_规范与工具/tools/asset_lock.py lock --scope cast` 锁定新生成的机位资产。")
    return 0


def main():
    parser = argparse.ArgumentParser(description="场景多机位四宫格展板无损切片工具")
    parser.add_argument("--input", "-i", required=True, help="输入的四宫格展板图片路径，如 cast/维修铺.多机位展板.png")
    parser.add_argument(
        "--names",
        "-n",
        nargs="+",
        default=["反打", "俯视", "左侧", "右侧"],
        help="4 个机位的命名，按 [左上, 右上, 左下, 右下] 顺序，默认: 反打 俯视 左侧 右侧",
    )
    parser.add_argument("--out-dir", "-o", help="输出目录，默认保存在输入文件同级目录")
    parser.add_argument("--prefix", "-p", help="输出文件名前缀，默认自动提取，如 维修铺.机位_")

    args = parser.parse_args()
    rc = slice_2x2_grid(
        input_path=Path(args.input),
        output_names=args.names,
        output_dir=Path(args.out_dir) if args.out_dir else None,
        prefix=args.prefix,
    )
    sys.exit(rc)


if __name__ == "__main__":
    main()
