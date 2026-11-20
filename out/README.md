# out 视频生成与合成目录指南（通用模板）

本目录由**【窗口④ 视频生成与合成专员】**专属负责写入，其他窗口只读。

## 目录结构

- **`out/EXX/`**：
  - `S01.mp4`, `S02.mp4` ...：单镜视频生成产物（由通用画布或 CLI 下载落盘）；
  - `SXX_vo.wav`：外挂配音音轨（仅 `vo_lipsync` 镜头）；
  - `SXX_lipsync.mp4`：外部对口型后产物；
  - `RUNLOG.md`：只追加（append-only）记录每一次生成尝试、改动变量、失败分类与实扣积分。
- **`out/EXX.mp4`**：
  - 本集最终拼合、对齐字幕的成片输出；
- **`out/EXX.srt`**：
  - 本集时间戳精度 ≤ 100ms 的对齐字幕文件。

## 标准生成作业流

1. **生成前预检**：
   ```bash
   python 02_规范与工具/tools/audit_shots.py shots/EXX.md
   ```
2. **两镜试拍与报价**：
   在放量前必须先试拍 2 镜代表样本（1 镜室内微反应 + 1 镜室外高速爆发动作），过审方可放量；每次扣费前先用 `credit estimate` 报总价等用户确认。
3. **末帧接力提取**：
   如果下镜需要接力当前镜头的最终姿态，使用原生抽帧工具抽取 100% 无损末帧入库：
   ```bash
   python 02_规范与工具/tools/extract_last_frame.py --input out/EXX/S01.mp4 --output cast/frames/EXX_S01_last.png
   # 并锁入帧清单：
   python 02_规范与工具/tools/asset_lock.py lock --scope frames --reason "锁定S01接力帧"
   ```
