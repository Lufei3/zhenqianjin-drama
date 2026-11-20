#!/usr/bin/env python3
"""
无损全分辨率视频末帧/指定帧提取工具（用于首尾帧锚定 --first-frame）
用法示例：
  python tools/extract_last_frame.py --input out/E01/S01.mp4 --output cast/frames/E01_S01_last.png
"""

import argparse
import os
import sys
from collections import deque

import cv2
import numpy as np


def imwrite_unicode(path: str, img) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    ext = os.path.splitext(path)[1] or ".png"
    ok, buf = cv2.imencode(ext, img)
    if not ok:
        raise RuntimeError(f"无法编码图像至: {path}")
    buf.tofile(path)


def main():
    parser = argparse.ArgumentParser(description="提取视频 100% 原始分辨率末帧（支持中文路径）")
    parser.add_argument("--input", "-i", required=True, help="输入 MP4 视频路径")
    parser.add_argument("--output", "-o", required=True, help="输出 PNG 路径")
    parser.add_argument("--offset", type=int, default=1, help="倒数第几帧（默认 1 即最后一帧）")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"错误：找不到视频文件 {args.input}", file=sys.stderr)
        sys.exit(1)

    cap = cv2.VideoCapture(args.input)
    if not cap.isOpened():
        print(f"错误：无法打开视频 {args.input}", file=sys.stderr)
        sys.exit(1)

    # 短镜只有数秒。顺序读到结尾，避免 CAP_PROP_POS_FRAMES 停在倒数第二帧或黑帧。
    buf = deque(maxlen=max(1, args.offset))
    total = 0
    while True:
        ret, frame_i = cap.read()
        if not ret:
            break
        total += 1
        buf.append(frame_i)
    cap.release()
    frame = buf[0] if buf else None

    if frame is None:
        print(f"错误：无法从视频中读取有效帧: {args.input}", file=sys.stderr)
        sys.exit(1)

    imwrite_unicode(args.output, frame)
    h, w = frame.shape[:2]
    picked = total - len(buf) + 1
    print(f"OK: 已提取无损末帧 -> {args.output} ({w}x{h}, frame {picked}/{total})")


if __name__ == "__main__":
    main()
