# cast 视觉资产库目录指南（通用模板）

本目录由**【窗口② 资产与首尾帧生产专员】**专属负责写入，其他窗口（分镜、视频）只读引用。严禁静默覆盖已锁版资产！

## 目录与资产规范

1. **根目录 `cast/`**：
   - 存放新剧的核心视觉资产卡（`.md` 提示词 + `.png` 验收图）：
     - 基础纯人物空手三视图：`cast/<角色>.默认.png`（严守双手自然下垂无外挂道具铁律，对齐模板 01）；
     - 持械/背负/战损/表情变体：`cast/<角色>.<形态>.png`（从纯净基础卡派生）；
     - 场景主控图：`cast/<场景>.默认.png`（对齐模板 02）；
     - 场景多机位四宫格展板：`cast/<场景>.多机位展板.png`（用 `tools/slice_grid.py` 切割出反打/俯视/左侧/右侧机位）；
     - 核心道具卡：`cast/<道具>.默认.png`（对齐模板 03）。
   - **锁版文件**：`cast/LOCKED.json`（记录所有基础图 SHA-256）。
2. **`cast/frames/`**：
   - 存放 Mode A 专用首尾帧定姿关键帧（`cast/frames/EXX_SXX_first.png`）或从过审视频无损抽取的接力末帧（`tools/extract_last_frame.py`）；
   - **锁版文件**：`cast/frames/LOCKED_FRAMES.json`。
3. **`cast/blocking/`**：
   - 存放单镜极简 3D 白模人偶站位图（`cast/blocking/EXX_SXX_blocking.png`，对齐模板 05）；
   - **锁版文件**：`cast/blocking/LOCKED_BLOCKING.json`。
4. **`cast/canon/`**：
   - 跨集长剧典范总清单：`cast/canon/CANON.json` 与漂移审计日志 `DRIFT_LOG.md`。
5. **`cast/storyboard/`**：
   - 3D 导演台白模摆位截图（`.director.png`）与故事板；
   - **红线**：仅供人眼审阅规划，永不允许作为 `--ref` 挂载给视频模型！

## 常用工具命令

```bash
# 1. 资产提示词推上画布前红线检查：
python 02_规范与工具/tools/audit_cast.py cast/ --only-characters

# 2. 四宫格场景展板无损切片（反打/俯视/左/右）：
python 02_规范与工具/tools/slice_grid.py --input cast/<场景>.多机位展板.png

# 3. 720 全景切片无损提取：
python 02_规范与工具/tools/extract_pano.py --input cast/<场景>.全景720.png --yaw 0 --pitch 0 --fov 80 --output cast/<场景>.机位_平视.png

# 4. 全部资产下载验收后一键全量锁版：
python 02_规范与工具/tools/asset_lock.py lock --scope all --reason "本集资产全量锁版"
```
