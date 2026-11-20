#!/usr/bin/env python3
"""门禁自测。在仓库根目录运行：python 02_规范与工具/tools/test_gates.py"""

import sys
import tempfile
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import audit_cast
import audit_shots


STYLE = audit_shots.load_film_style()
ASSET = audit_cast.load_style_line("资产风格句", audit_cast.ASSET_STYLE_FALLBACK)


def write(dir_path: Path, name: str, content: str) -> Path:
    path = dir_path / name
    path.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")
    return path


def good_pair(dir_path: Path) -> Path:
    write(
        dir_path,
        "E01_master.md",
        f"""
        # E01

        | Shot | Dur | Scene | Characters | Mode | Refs | Frame Status | Audio Mode | Emotion In → Out | Bridge | Cadence Beat | Deps | QC & Attempts |
        | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
        | **S01** | 4.0 | 工坊 | 角色A 🎬 | B | `@工坊=cast/工坊.默认.png` `@角色A=cast/角色A.默认.png` | Not Required | native | 专注→开口 | None | Inhale (4-6s) | cast/工坊.默认.png | 未检 / 0 |
        | **S02** | 2.5 | 林地 | 角色A 🎬 | A | `首帧=cast/frames/E01_S02_first.png` | Mandatory | native | 蓄力→撞击 | None | Exhale (1.5-3s) | cast/frames/E01_S02_first.png | 未检 / 0 |
        """,
    )
    return write(
        dir_path,
        "E01.md",
        f"""
        # E01

        ## S01
        - **参数**：`Seedance 2.5` ｜ `Mode B（多参考图）` ｜ `16:9` ｜ `4.0s` ｜ `Audio: native` ｜ `Cadence: Inhale`
        - **挂载参考图**：`@工坊`=`cast/工坊.默认.png` ｜ `@角色A`=`cast/角色A.默认.png`

        ```text
        {STYLE}

        参考映射：@工坊 为场景空间与布光基准。@角色A 为面部与服饰基准。
        本片段设定在 @工坊。桌面散落零件，窗外有雨。
        拍子1（0.0–2.0秒）：@角色A 站在台前，视线落在齿轮上，双手撑住桌沿，胸膛随呼吸起伏。<雨声>
        拍子2（2.0–4.0秒）：@角色A 直起身，衣摆甩动后落定，开口说道：「零件被动过了。」面部保持自然肤色。<桌面摩擦声>
        音轨仅保留角色人声、环境声与物理动作音效。不要生成旁白字幕、台词字幕或对白字幕。
        衔接：角色A站在桌前。
        ```

        ## S02
        - **参数**：`Seedance 2.5` ｜ `Mode A（首尾帧 I2V）` ｜ `16:9` ｜ `2.5s` ｜ `Audio: native` ｜ `Cadence: Exhale (Burst)`
        - **挂载首帧**：`首帧`=`cast/frames/E01_S02_first.png`

        ```text
        {STYLE}

        紧接首帧画面直接延续动作。雨丝打在泥地上。
        拍子1（0.0–1.2秒）：角色A 压低重心后向前刺出，衣摆向后拉直。<破风声>
        拍子2（1.2–2.5秒）：矛尖撞上树干，双臂锁死，衣摆晃了两次后贴回。<撞击声>
        画面中所有出镜角色全程不说话。音轨仅保留环境声与物理动作音效。不要生成旁白字幕、台词字幕或对白字幕。
        衔接：角色A保持刺出后的姿态。
        ```
        """,
    )


def assert_fail(path: Path, needle: str, check_files: bool = False) -> None:
    from io import StringIO
    from contextlib import redirect_stdout

    buf = StringIO()
    with redirect_stdout(buf):
        rc = audit_shots.audit_file(path, check_files=check_files)
    output = buf.getvalue()
    if rc == 0 or needle not in output:
        raise SystemExit(f"期望拦截「{needle}」，实际 rc={rc}\n{output}")


def main() -> int:
    if "国漫3D（CG）" not in STYLE or "人物解剖" not in ASSET:
        raise SystemExit(f"风格句没有从 README 读到：\n{STYLE}\n{ASSET}")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        ok = good_pair(root)
        if audit_shots.audit_file(ok, check_files=False) != 0:
            raise SystemExit("合格样例应通过")

        missing = write(root, "E02.md", ok.read_text(encoding="utf-8").replace("E01", "E02"))
        assert_fail(missing, "缺少总控表")

        flat_dir = root / "same"
        flat_dir.mkdir()
        write(
            flat_dir,
            "E03_master.md",
            """
            | Shot | Dur | Scene | Characters | Mode | Refs | Frame Status | Audio Mode | Emotion In → Out | Bridge | Cadence Beat | Deps | QC & Attempts |
            | **S01** | 4.0 | 工坊 | 角色A 🎬 | B | `@工坊=cast/a.png` `@角色A=cast/b.png` | Not Required | native | 平 | None | Inhale (4-6s) | a | 0 |
            | **S02** | 4.0 | 工坊 | 角色A 🎬 | B | `@工坊=cast/a.png` `@角色A=cast/b.png` | Not Required | native | 平 | None | Inhale (4-6s) | a | 0 |
            | **S03** | 4.0 | 工坊 | 角色A 🎬 | B | `@工坊=cast/a.png` `@角色A=cast/b.png` | Not Required | native | 平 | None | Inhale (4-6s) | a | 0 |
            """,
        )
        body = f"""
        # E03
        ## S01
        - **参数**：Mode B
        - **挂载参考图**：`@工坊`=`cast/a.png` ｜ `@角色A`=`cast/b.png`
        ```text
        {STYLE}
        @工坊 是空间。@角色A 站在台前，视线落在齿轮上，胸膛起伏。
        拍子1（0.0–4.0秒）：@角色A 双手撑住桌沿。<雨声>
        音轨仅保留角色人声、环境声与物理动作音效。不要生成旁白字幕、台词字幕或对白字幕。他说：「好。」
        ```
        ## S02
        - **参数**：Mode B
        - **挂载参考图**：`@工坊`=`cast/a.png` ｜ `@角色A`=`cast/b.png`
        ```text
        {STYLE}
        @工坊 是空间。@角色A 站在台前，视线落在齿轮上，胸膛起伏。
        拍子1（0.0–4.0秒）：@角色A 双手撑住桌沿。<雨声>
        音轨仅保留角色人声、环境声与物理动作音效。不要生成旁白字幕、台词字幕或对白字幕。他说：「好。」
        ```
        ## S03
        - **参数**：Mode B
        - **挂载参考图**：`@工坊`=`cast/a.png` ｜ `@角色A`=`cast/b.png`
        ```text
        {STYLE}
        @工坊 是空间。@角色A 站在台前，视线落在齿轮上，胸膛起伏。
        拍子1（0.0–4.0秒）：@角色A 双手撑住桌沿。<雨声>
        音轨仅保留角色人声、环境声与物理动作音效。不要生成旁白字幕、台词字幕或对白字幕。他说：「好。」
        ```
        """
        same = write(flat_dir, "E03.md", body)
        assert_fail(same, "附录A-17")

        stare = ok.read_text(encoding="utf-8").replace("视线落在齿轮上", "看着对方")
        stare_path = write(root, "E04.md", stare)
        write(root, "E04_master.md", (root / "E01_master.md").read_text(encoding="utf-8"))
        assert_fail(stare_path, "看着对方")

        if audit_shots.audit_file(ok, check_files=True) == 0:
            raise SystemExit("缺图时应拦截")

    print("[门禁自测通过] 风格句读取、合格样例、缺总控表、等长节拍、看着对方、缺图落盘。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
