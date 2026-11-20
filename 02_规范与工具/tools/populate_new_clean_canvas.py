import subprocess
import json
import time

CLI = r"C:\Users\Administrator\bin\dreamina-canvas.exe"

ASSETS = [
    # 1. 戚月基础三视图
    {
        "title": "戚月_默认",
        "mode": "t2i",
        "refs": [],
        "x": 0,
        "y": 0,
        "prompt": """国漫3D写实高精度古风CG电影渲染，顶级虚幻引擎5电影光影，严谨东方人体骨相解剖结构，真实皮肤毛孔与丝绸棉麻纤维质感。

18岁古代英气少女，身形纤细但柔韧矫健，骨相冷艳英气，桃花眼乌黑深邃。利落半束发配墨竹发簪，额前垂微散碎发。身穿洗旧深墨绿素色棉麻窄袖胡服劲装，黑色束腰，下摆微磨损，黑色马靴。双手空手自然下垂放松。

16:9 角色三视图设计展板。正面、九十度侧面、背面三个全身立姿等高对齐，右侧排列同一人的正面高精面部特写。纯净浅灰单色中性展板背景，均匀摄影棚柔光，五官骨相与棉麻织物纹理纤毫毕现，无任何多余文字与水印。"""
    },
    # 2. 老夫人基础三视图
    {
        "title": "老夫人_默认",
        "mode": "t2i",
        "refs": [],
        "x": 0,
        "y": 700,
        "prompt": """国漫3D写实高精度古风CG电影渲染，顶级虚幻引擎5电影光影，严谨东方人体骨相解剖结构，真实皮肤毛孔与丝绸棉麻纤维质感。

65岁名门侯府老夫人，满头银发盘严谨高髻，插点翠双头簪，面容威严有气度，眼神沉稳端庄。身穿深红色缎面如意云纹华贵长袍，领口与宽袖刺绣精致银线如意纹，颈项佩戴粗红珊瑚圆珠串。双手空手自然下垂放松。

16:9 角色三视图设计展板。正面、九十度侧面、背面三个全身立姿等高对齐，右侧排列同一人的正面高精面部特写。纯净浅灰单色中性展板背景，均匀摄影棚柔光，五官骨相与丝绸缎面纹理纤毫毕现，无任何多余文字与水印。"""
    },
    # 3. 正厅主视图
    {
        "title": "正厅_默认",
        "mode": "t2i",
        "refs": [],
        "x": 0,
        "y": 2000,
        "prompt": """国漫3D写实高精度古风CG电影渲染，顶级虚幻引擎5古建电影级光影，真实木质与刺绣织物自然微瑕疵纹理，强烈冷暖明暗情绪反差，浅景深与空气介质微尘感。

架空古代高门镇北侯府正厅荣德堂宽银幕建立全景。五间挑高朱红梁柱贯通屋顶，重檐歇山顶建筑内部，雕花朱漆彩绘大梁横跨。正中高堂设立宽大紫檀木雕花罗汉榻主位，后方矗立一幅高耸刺绣长春松鹤图双面屏风；堂中两侧整齐陈设四张厚重紫檀圈椅与高脚茶几；平整光亮的黑漆金砖地面倒映高堂红烛光泽与窗扉轮廓。空气中悬浮袅袅名贵檀香青烟与轻柔漂浮的细微浮尘，门外斜透阴天冷光，室内高台红烛摇曳形成沉稳冷暖对比。

广角三层景深构图，纯环境空镜，画面中只有高门府邸陈设与空间光影，无人物出现，无文字水印。"""
    },
    # 4. 紫檀佛珠
    {
        "title": "紫檀佛珠_默认",
        "mode": "t2i",
        "refs": [],
        "x": 2800,
        "y": 0,
        "prompt": """国漫3D写实高精度古风CG电影渲染，顶级虚幻引擎5古建电影级光影，真实木质与刺绣织物自然微瑕疵纹理，强烈冷暖明暗情绪反差，浅景深与空气介质微尘感。

侯府老太君贴身紫檀佛珠串高精特写展板。由一百零八颗名贵小叶紫檀圆珠串成，深棕褐色木质表面带有岁月沉淀的玻璃底油润老包浆，木纹细腻隐现金星与牛毛纹，佛头处配一颗老蜜蜡圆珠和暗金明黄双丝编织流苏。

干净深灰色中性摄影棚展板背景，佛珠串自然盘绕平放居中展示，柔和漫射光映照出木料油润光泽与自然微瑕疵，无文字水印。"""
    },
    # 5. 墨竹发簪
    {
        "title": "墨竹发簪_默认",
        "mode": "t2i",
        "refs": [],
        "x": 2800,
        "y": 700,
        "prompt": """国漫3D写实高精度古风CG电影渲染，顶级虚幻引擎5古建电影级光影，真实木质与刺绣织物自然微瑕疵纹理，强烈冷暖明暗情绪反差，浅景深与空气介质微尘感。

戚月贴身墨竹发簪高精度特写展板。由一整块深墨绿老坑墨玉雕刻而成的七寸发簪，造型为古朴挺拔的四节细竹节，簪身修长圆润，强光下隐隐透出温润翠绿通透质感，簪尖打磨坚硬锐利，簪头处浅浮雕两片修长竹叶纹理。

干净深灰色中性摄影棚展板背景，墨玉发簪单独居中水平放置展示，侧光凸显玉石油脂光泽与竹节微距刻痕，无文字水印。"""
    }
]

def main():
    print("=== 开始在新画布上创建第一批纯净基准节点 ===")
    node_map = {}
    
    # 1. 创建基础 t2i 节点
    for item in ASSETS:
        cmd = [
            CLI, "--format", "json",
            "node", "create", "image",
            "--title", item["title"],
            "--mode", item["mode"],
            "--model", "seedream_5.5",
            "--ratio", "16:9",
            "--resolution", "2K",
            "--count", "1",
            "--x", str(item["x"]),
            "--y", str(item["y"]),
            "--prompt", item["prompt"]
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            res = json.loads(r.stdout)
            nid = res.get("data", {}).get("node", {}).get("nodeId")
            node_map[item["title"]] = nid
            print(f"[OK] 创建基准节点: {item['title']} -> {nid}")
        else:
            print(f"[FAIL] 创建失败 {item['title']}: {r.stderr or r.stdout}")
        time.sleep(0.3)

    qiyue_id = node_map.get("戚月_默认")
    laofuren_id = node_map.get("老夫人_默认")
    zhengting_id = node_map.get("正厅_默认")

    # 2. 创建戚月微表情变体 (挂戚月_默认)
    if qiyue_id:
        cmd = [
            CLI, "--format", "json",
            "node", "create", "image",
            "--title", "戚月_冷笑讥讽微表情",
            "--mode", "i2i",
            "--ref", f"node:{qiyue_id}",
            "--model", "seedream_5.5",
            "--ratio", "16:9",
            "--resolution", "2K",
            "--count", "1",
            "--x", "900",
            "--y", "0",
            "--prompt", f"""国漫3D写实高精度古风CG电影渲染，顶级虚幻引擎5电影光影，严谨东方人体骨相解剖结构，真实皮肤毛孔与丝绸棉麻纤维质感。

{{{{node:{qiyue_id}}}}}是同一角色的基础形象。保持完全一致的冷艳骨相、乌黑桃花眼与墨竹半束发发型，将面部微表情调整为冷笑讥讽、眉宇间带着凉薄与不屑。16:9 角色三视图设计展板，正面、九十度侧面、背面体态对齐，双手自然下垂放松，右侧特写重点聚焦冷笑讥讽与唇角讥诮的微表情特写。纯净浅灰中性背景，无文字水印。"""
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            nid = json.loads(r.stdout).get("data", {}).get("node", {}).get("nodeId")
            print(f"[OK] 创建派生节点: 戚月_冷笑讥讽微表情 -> {nid} (挂 {qiyue_id})")
        time.sleep(0.3)

    # 3. 创建老夫人微表情变体 (挂老夫人_默认)
    if laofuren_id:
        cmd = [
            CLI, "--format", "json",
            "node", "create", "image",
            "--title", "老夫人_听心声震骇微表情",
            "--mode", "i2i",
            "--ref", f"node:{laofuren_id}",
            "--model", "seedream_5.5",
            "--ratio", "16:9",
            "--resolution", "2K",
            "--count", "1",
            "--x", "900",
            "--y", "700",
            "--prompt", f"""国漫3D写实高精度古风CG电影渲染，顶级虚幻引擎5电影光影，严谨东方人体骨相解剖结构，真实皮肤毛孔与丝绸棉麻纤维质感。

{{{{node:{laofuren_id}}}}}是同一角色的基础形象。保持完全一致的银发高髻点翠簪与深红如意袍服，将面部微表情调整为猝然听见心声时的惊骇万分、瞳孔骤缩、嘴唇微张倒吸凉气。16:9 角色三视图设计展板，正面、九十度侧面、背面体态对齐，双手自然下垂放松，右侧特写重点聚焦老夫人惊愕震骇、目光发紧的生动微表情特写。纯净浅灰中性背景，无文字水印。"""
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            nid = json.loads(r.stdout).get("data", {}).get("node", {}).get("nodeId")
            print(f"[OK] 创建派生节点: 老夫人_听心声震骇微表情 -> {nid} (挂 {laofuren_id})")
        time.sleep(0.3)

    # 4. 创建正厅 3D 微缩剖切模型 (挂正厅_默认)
    zhengting_mini_id = None
    if zhengting_id:
        cmd = [
            CLI, "--format", "json",
            "node", "create", "image",
            "--title", "正厅_3D微缩剖切模型",
            "--mode", "i2i",
            "--ref", f"node:{zhengting_id}",
            "--model", "seedream_5.5",
            "--ratio", "16:9",
            "--resolution", "2K",
            "--count", "1",
            "--x", "900",
            "--y", "2000",
            "--prompt", f"""国漫3D写实高精度古风CG电影渲染，顶级虚幻引擎5古建电影级光影，真实木质与刺绣织物自然微瑕疵纹理，强烈冷暖明暗情绪反差，浅景深与空气介质微尘感。

基于{{{{node:{zhengting_id}}}}}同一建筑结构与光影材质，生成 3D 剖切微缩空间模型盒（Isometric 3D Cutaway Dollhouse Diorama）。等轴测45度斜俯视剖切模型盒，顶部屋顶整齐剖切移除，如同一个精致大气的四方形微缩建筑沙盘模型盒，一眼看清整座威远侯府正厅的完整四壁空间与家具三维绝对方位：正北高堂最深处正中央设深紫檀雕花罗汉椅宝座与金匾「忠勇传家」；东西两侧各立两根粗壮雄伟的朱红金丝楠木立柱，柱旁整齐排列酸枝木太师椅与茶几；正南为大敞的朱红雕花正门与门阶；地面为玄黑金砖反光地面。纯建筑微缩沙盘模型，纯环境空镜，无人物，无文字水印。"""
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            zhengting_mini_id = json.loads(r.stdout).get("data", {}).get("node", {}).get("nodeId")
            print(f"[OK] 创建场景微缩盒: 正厅_3D微缩剖切模型 -> {zhengting_mini_id} (挂 {zhengting_id})")
        time.sleep(0.3)

    # 5. 创建正厅多机位四宫格展板 (双连线：正厅_默认 + 正厅_3D微缩剖切模型)
    if zhengting_id and zhengting_mini_id:
        cmd = [
            CLI, "--format", "json",
            "node", "create", "image",
            "--title", "正厅_多机位四宫格展板",
            "--mode", "i2i",
            "--ref", f"node:{zhengting_id}",
            "--ref", f"node:{zhengting_mini_id}",
            "--model", "seedream_5.5",
            "--ratio", "16:9",
            "--resolution", "2K",
            "--count", "1",
            "--x", "1800",
            "--y", "2000",
            "--prompt", f"""国漫3D写实高精度古风CG电影渲染，顶级虚幻引擎5古建电影级光影，真实木质与刺绣织物自然微瑕疵纹理，强烈冷暖明暗情绪反差，浅景深与空气介质微尘感。

【核心原则：100%真实全尺寸电影实景拍摄，彻底杜绝微缩模型/沙盘盒子】
基于{{{{node:{zhengting_id}}}}}正厅场景标准主视图建立的真实美术光影、色温与物理材质基准，并参考{{{{node:{zhengting_mini_id}}}}}空间方位锁定的三维家具与建筑拓扑坐标，生成 16:9 场景多机位四宫格电影分镜展板，同比例四联无缝拼接展示：
- 左上格：反打实景机位（从高堂主座回望大门反向，正对大敞朱红雕花正门、门外汉白玉台阶与庭院透进的漫射天光）；
- 右上格：室内顶梁大广角俯拍机位（摄影机置于正厅挑高粗壮大梁下方的大广角高空俯拍，俯瞰整个宏伟正厅进深、黑金砖地面微光倒影与两侧整齐太师椅，头顶有完整藻井横梁，为全封闭真实宏伟建筑大厅实景）；
- 左下格：左侧90度平视实景机位（摄影机平视正对左侧两张紫檀太师椅、条案茶几与立式木雕隔扇屏风）；
- 右下格：右侧90度平视实景机位（摄影机平视正对右侧雕花木窗、高脚青瓷花几与青铜香炉飘出的青烟）。
【关键要求】四个格子全部为1:1真实宏伟建筑内部沉浸式摄影机机位实拍画面，具有真实屋顶天花板与地面，完全处于真实世界空间内。彻底排除沙盘模型，拒绝微缩模型盒，拒绝玩具模型，拒绝无顶剖切盒。四个机位完全来自同一三维空间建筑结构与同套光影材质。纯建筑空间纯空镜无人物，无文字、无标签、无水印。"""
        ]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0:
            nid = json.loads(r.stdout).get("data", {}).get("node", {}).get("nodeId")
            print(f"[OK] 创建四宫格展板: 正厅_多机位四宫格展板 -> {nid} (双挂 {zhengting_id} + {zhengting_mini_id})")

    print("\n[DONE] 新画布全部基准节点创建完成！")

if __name__ == '__main__':
    main()
