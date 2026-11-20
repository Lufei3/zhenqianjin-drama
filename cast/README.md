# 视觉资产库

从分镜派单领取当前批次的角色、场景和参考帧。样片派单通常位于 `shots/pilot/EXX_assets_todo.json`，整集派单在分镜 JSON 同目录。优先制作场内需要的定妆参考、可复用的场景参考和即将开拍的首帧。多个镜头共用场景图时，在分镜里填 `refs.scene_plate`，由资产用它对齐首帧的布局、方向与主光。

| 位置 | 放什么 |
|---|---|
| `cast/` | 角色、场景、道具的验收参考图及其设定卡，沿用 `<名称>.<状态>.png`。普通对白场可先用单张定妆照，角色卡设定段写 `参考版式：定妆照`。需要全身结构或多个机位时，再补三视图或全景。 |
| `cast/frames/` | Mode A/A+ 的拍摄参考帧，例如 `E01_S01_first.png`；已过审且确实要接姿态的末帧也可入库。 |
| `cast/sketch/`、`cast/blocking/`、`cast/storyboard/` | 构图草图、白模或故事板，只用于预演和协助生图。视频模型使用通过验收的成片风格参考。 |
| `cast/canon/` | 跨集复用的设定与漂移记录。 |

先人工看图，检查脸、发型、服装、道具、人物位置、视线和场景光向是否适合下游镜头。返工候选用独立文件保存。挑中后从仓库根目录按文件锁版：

```bash
python 02_规范与工具/tools/asset_lock.py lock --scope cast --file 'cast/场景名.默认.png' --reason '样片场景参考通过'
python 02_规范与工具/tools/asset_lock.py lock --scope frames --file cast/frames/E01_S01_first.png --reason '样片 S01 首帧通过'
```

同一范围可重复传 `--file`。图像锁表分别在 `cast/LOCKED.json` 和 `cast/frames/LOCKED_FRAMES.json`。换版前核对哪些镜头正在引用旧版，再按新文件调整分镜并锁定。哈希可以核对文件是否变化，素材质量以人工看片为准。

资产可由项目绑定的通用画布准备。只在当前界面确认素材生成可用「0 积分畅用」时使用该队列，生成后挑图，再下载到库。工具入口及其他生产顺序见 [制作流程](../02_规范与工具/PIPELINE_SPEC.md)。
