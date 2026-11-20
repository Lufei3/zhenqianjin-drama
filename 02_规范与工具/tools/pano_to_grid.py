#!/usr/bin/env python3
"""
02_规范与工具/tools/pano_to_grid.py
从 720° 全景图全自动提取并合成「绝对吻合的场景四宫格展板」与 4 个单机位切片

核心原理：
  1. 720° 等距柱状球形全景图包含了场景 360°x180° 的全部真实结构与光影。
  2. 本工具利用虚拟针孔摄影机，从同一球体中无畸变提取 4 个核心电影机位：
     - 左上格：反打视角 (Reverse Angle · yaw=180°, pitch=0°)
     - 右上格：俯视全貌 (Top-down Angle · yaw=0°, pitch=-50°, fov=90°)
     - 左下格：左侧机位 (Left Side Angle · yaw=-90°, pitch=0°)
     - 右下格：右侧机位 (Right Side Angle · yaw=90°, pitch=0°)
  3. 将 4 个单机位画面拼合成标准的 16:9 四宫格展板（cast/<场景>.多机位展板.png），
     同时输出 4 张独立的 16:9 机位图（cast/<场景>.机位_反打.png 等）。
  4. 四个视角全部来自同一三维空间，100% 绝对吻合、零穿帮！

用法：
  python 02_规范与工具/tools/pano_to_grid.py --input cast/维修铺.全景720.png
"""

import argparse
import os
import sys
import cv2
import numpy as np
from pathlib import Path


def imread_unicode(path: str):
    data = np.fromfile(path, dtype=np.uint8)
    img = cv2.imdecode(data, cv2.IMREAD_COLOR)
    if img is None:
        raise RuntimeError(f"无法读取图像文件: {path}")
    return img


def imwrite_unicode(path: str, img) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    ext = os.path.splitext(path)[1] or ".png"
    ok, buf = cv2.imencode(ext, img)
    if not ok:
        raise RuntimeError(f"编码输出图像失败: {path}")
    buf.tofile(path)


def equi2persp(img, fov_deg: float = 80.0, yaw_deg: float = 0.0, pitch_deg: float = 0.0, out_w: int = 1920, out_h: int = 1080):
    in_h, in_w = img.shape[:2]
    fov_rad = np.radians(fov_deg)
    f = 0.5 * out_w / np.tan(fov_rad / 2.0)

    x = np.arange(out_w, dtype=np.float32) - out_w / 2.0
    y = np.arange(out_h, dtype=np.float32) - out_h / 2.0
    xx, yy = np.meshgrid(x, y)

    zz = np.full_like(xx, f)
    dirs = np.stack([xx, -yy, zz], axis=-1)
    dirs /= np.linalg.norm(dirs, axis=-1, keepdims=True)

    yaw_rad = np.radians(yaw_deg)
    pitch_rad = np.radians(pitch_deg)

    Ry = np.array([
        [np.cos(yaw_rad), 0.0, np.sin(yaw_rad)],
        [0.0, 1.0, 0.0],
        [-np.sin(yaw_rad), 0.0, np.cos(yaw_rad)],
    ], dtype=np.float32)

    Rx = np.array([
        [1.0, 0.0, 0.0],
        [0.0, np.cos(pitch_rad), -np.sin(pitch_rad)],
        [0.0, np.sin(pitch_rad), np.cos(pitch_rad)],
    ], dtype=np.float32)

    R = Ry @ Rx
    dirs_rot = dirs @ R.T

    X = dirs_rot[..., 0]
    Y = dirs_rot[..., 1]
    Z = dirs_rot[..., 2]

    theta = np.arctan2(X, Z)
    phi = np.arcsin(np.clip(Y, -1.0, 1.0))

    map_x = ((theta / (2.0 * np.pi) + 0.5) * in_w) % in_w
    map_y = (0.5 - phi / np.pi) * in_h

    return cv2.remap(img, map_x.astype(np.float32), map_y.astype(np.float32), cv2.INTER_LANCZOS4)


def process_pano_to_grid(input_path: Path, output_grid_path: Path = None, out_w: int = 1920, out_h: int = 1080):
    if not input_path.exists():
        print(f"[错误] 输入全景图不存在: {input_path}")
        return 1

    pano_img = imread_unicode(str(input_path))
    in_h, in_w = pano_img.shape[:2]
    print(f"[读取全景图] {input_path.name} | 尺寸: {in_w}x{in_h}")

    # 提取 4 个核心机位参数: (机位名, yaw, pitch, fov)
    cameras = [
        ("反打", 180.0, 0.0, 80.0),
        ("俯视", 0.0, -50.0, 90.0),
        ("左侧", -90.0, 0.0, 80.0),
        ("右侧", 90.0, 0.0, 80.0),
    ]

    base_name = input_path.stem
    for suffix in [".全景720", ".720全景", ".pano", ".720"]:
        if base_name.endswith(suffix):
            base_name = base_name[: -len(suffix)]
            break

    parent_dir = input_path.parent
    extracted_slices = []

    print("[正在进行三维空间摄影机投影切片...]")
    for name, yaw, pitch, fov in cameras:
        persp = equi2persp(pano_img, fov_deg=fov, yaw_deg=yaw, pitch_deg=pitch, out_w=out_w, out_h=out_h)
        slice_path = parent_dir / f"{base_name}.机位_{name}.png"
        imwrite_unicode(str(slice_path), persp)
        extracted_slices.append(persp)
        print(f"  -> 生成纯净切片: {slice_path.name} (yaw={yaw}°, pitch={pitch}°, fov={fov}°)")

    # 拼接纯净四宫格 (2x2 Grid) - 严禁包含任何文字标牌或文字水印，保持纯净画面
    # top: 反打, 俯视
    # bottom: 左侧, 右侧
    top_row = np.hstack([extracted_slices[0], extracted_slices[1]])
    bottom_row = np.hstack([extracted_slices[2], extracted_slices[3]])
    grid_img = np.vstack([top_row, bottom_row])

    if output_grid_path is None:
        output_grid_path = parent_dir / f"{base_name}.多机位展板.png"

    imwrite_unicode(str(output_grid_path), grid_img)
    print(f"\n[四宫格展板生成成功!] -> {output_grid_path.name} (总分辨率: {grid_img.shape[1]}x{grid_img.shape[0]})")
    print(f"纯净无字展板: 左上[反打] | 右上[俯视] | 左下[左侧] | 右下[右侧]")
    print(f"所有机位均来源于同一 720° 全景空间，空间与材质 100% 吻合！")
    return 0
    print(f"所有机位均来源于同一 720° 全景空间，空间与材质 100% 吻合！")
    return 0


def main():
    parser = argparse.ArgumentParser(description="从 720 全景图提取并生成吻合的四宫格展板与单机位切片")
    parser.add_argument("--input", "-i", required=True, help="输入的 720 全景图路径，如 cast/维修铺.全景720.png")
    parser.add_argument("--output", "-o", help="输出的四宫格展板路径，默认 cast/<场景>.多机位展板.png")
    parser.add_argument("--width", type=int, default=1920, help="单格宽度，默认 1920")
    parser.add_argument("--height", type=int, default=1080, help="单格高度，默认 1080")
    args = parser.parse_args()

    rc = process_pano_to_grid(
        input_path=Path(args.input),
        output_grid_path=Path(args.output) if args.output else None,
        out_w=args.width,
        out_h=args.height,
    )
    sys.exit(rc)


if __name__ == "__main__":
    main()
