# 分镜与派生文件

每集用 `shots/EXX_spec.json` 管理制作分镜。在顶层按项目设置写入 `aspect_ratio` 和 `video_model`。旧分镜省略时分别沿用 `16:9` 和 `Seedance 2.5`。已有完整清单时，从中选择连续样片镜头。新建制作分镜时，可以先从 [JSON 模板](../02_规范与工具/templates/05_单源分镜JSON_模板.json) 登记样片，验收后再补齐其余镜头。

G1 先用占位静帧和试读或临时配音粗剪。安排每镜的主要动作和切点，确认人物出入画、视线方向以及道具跨镜状态。用 `dur` 记录模型收到的生成时长，用 `cut_duration` 记录计划剪入的时长，省略后者时默认等于 `dur`。单首帧 Mode A 是起点。确实需要同时锁定首尾构图、且当前入口支持时使用 Mode A+。已试过单首帧仍缺身份或场景信息的镜头，可在入口支持时试 Mode B。已选场景参考用 `refs.scene_plate` 指定。若 A/A+ 镜头的首帧已有合适场景，可填 `refs.scene_plate: null`，派单不会从场景名补推一张图。B 模式以实际挂载列表为准。

下面以 `E01` 为例。新建分镜时，在仓库根目录把模板复制过去，已存在的分镜会保留。

```sh
if [ ! -e shots/E01_spec.json ]; then
  cp 02_规范与工具/templates/05_单源分镜JSON_模板.json shots/E01_spec.json
fi
```

复制后先把技术示例替换为已确认的镜头，再运行：

```bash
python 02_规范与工具/tools/audit_shots.py shots/E01_spec.json --pre
python 02_规范与工具/tools/build_episode.py --ep E01
```

脚本派生三份文件：

- `E01_master.md` 供分镜和后期检查镜号、生成时长、剪辑时长、参考和跨镜衔接。
- `E01_prompts.md` 的代码块用于提交视频提示词。参数、挂载和衔接备注留在代码块外。
- `E01_assets_todo.json` 供资产和后期领取素材缺口，优先补当前样片涉及的条目。

分镜字段或提示词有变动时，更新制作 JSON，再运行派生工具。直接复制图像、视频或制作助手的指令前，先查[提示词手册](../02_规范与工具/PROMPT_PLAYBOOK.md)。实际素材和应先准备的配音 WAV 就绪后，运行 `python 02_规范与工具/tools/audit_shots.py shots/E01_spec.json`。审计通过后还需看样片，核对执行输入、人物和空间连续性以及音画。

已有完整清单时，可在三个命令后都加 `--shots S01 S02`，把镜号换成本轮样片的范围。派生文件写在 `shots/pilot/`。放量时使用不带 `--shots` 的命令处理整份清单。
