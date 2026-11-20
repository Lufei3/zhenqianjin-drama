#!/usr/bin/env python3
"""
720° 等距柱状全景图 (Equirectangular) -> 无畸变电影机位 (Rectilinear 16:9) 提取工具
用法示例：
  python tools/extract_pano.py --input cast/维修铺.全景720.png --output cast/维修铺.机位_工作台.png --yaw 45 --pitch -8 --fov 80
"""

import argparse
import os
import sys
import cv2
import numpy as np


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


def equi2persp(img, fov_deg: float = 80.0, yaw_deg: float = 0.0, pitch_deg: float = 0.0, out_w: int = 2560, out_h: int = 1440):
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


def main():
    parser = argparse.ArgumentParser(description="从 720 全景图提取无畸变 16:9 电影机位图")
    parser.add_argument("--input", "-i", required=True, help="输入 720 全景图路径")
    parser.add_argument("--output", "-o", required=True, help="输出机位图路径")
    parser.add_argument("--yaw", type=float, default=0.0, help="水平旋转角（-180 到 180，默认 0 为正中）")
    parser.add_argument("--pitch", type=float, default=0.0, help="俯仰角（负值俯拍，正值仰拍，默认 0）")
    parser.add_argument("--fov", type=float, default=80.0, help="水平视场角（默认 80°，特写可调 50-65°）")
    parser.add_argument("--width", type=int, default=2560, help="输出宽度（默认 2560）")
    parser.add_argument("--height", type=int, default=1440, help="输出高度（默认 1440）")
    args = parser.parse_args()

    img = imread_unicode(args.input)
    out = equi2persp(img, fov_deg=args.fov, yaw_deg=args.yaw, pitch_deg=args.pitch, out_w=args.width, out_h=args.height)
    imwrite_unicode(args.output, out)
    print(f"OK: {args.output} ({args.width}x{args.height}, yaw={args.yaw}, pitch={args.pitch}, fov={args.fov})")


if __name__ == "__main__":
    main()
