import os
import sys
import json
import time
import subprocess

CLI_PATH = r"C:\Users\Administrator\bin\dreamina-canvas.exe"

def run_cmd(cmd):
    res = subprocess.run(cmd, capture_output=True, text=True)
    try:
        data = json.loads(res.stdout) if res.stdout else {}
    except Exception:
        data = {}
    return res.returncode, data, res.stderr or res.stdout

def get_all_nodes():
    nodes = []
    offset = 0
    while True:
        # 翻页读取所有节点
        cmd = [CLI_PATH, "--format", "json", "node", "find"]
        # schema for node find
        code, data, err = run_cmd(cmd)
        if code != 0:
            print("读取节点失败:", err)
            break
        items = data.get("data", {}).get("items", [])
        nodes.extend(items)
        if not data.get("data", {}).get("hasMore", False):
            break
        break  # single page if hasMore not supported with offset flag
    return nodes

def run_single_node(node_id, title):
    print(f"\n>>> 开始触发生成: 【{title}】 (ID: {node_id}) ...")
    cmd = [CLI_PATH, "--format", "json", "node", "run", "--node-id", node_id]
    code, data, err = run_cmd(cmd)
    
    if code != 0:
        error_info = data.get("error", {})
        print(f"[FAIL] 提交失败 【{title}】: {error_info.get('message', err)}")
        return False, None
    
    items = data.get("data", {}).get("items", [])
    if not items:
        print(f"[WARN] 提交无返回项: {data}")
        return False, None
    
    submit_id = items[0].get("submitId")
    print(f"[SUBMITTED] 提交成功，任务ID: {submit_id}，正在轮询生成进度...")
    
    # 轮询状态
    start_time = time.time()
    while time.time() - start_time < 90:
        time.sleep(4)
        status_cmd = [CLI_PATH, "--format", "json", "operation", "status", submit_id]
        s_code, s_data, s_err = run_cmd(status_cmd)
        if s_code == 0:
            state = s_data.get("data", {}).get("state")
            if state == "succeeded":
                res = s_data.get("data", {}).get("resources", [{}])[0]
                res_id = res.get("resourceId", "unknown")
                w = res.get("width", 0)
                h = res.get("height", 0)
                print(f"[DONE] 生成完成: 【{title}】 尺寸: {w}x{h}, 资源ID: {res_id}")
                return True, res_id
            elif state in ["failed", "canceled"]:
                print(f"[FAILED] 生成失败: 【{title}】 状态: {state}")
                return False, None
            else:
                print(f"  ... 排队/生成中 ({int(time.time() - start_time)}s)")
        else:
            print(f"  ... 查询状态异常: {s_err[:100]}")
    
    print(f"[TIMEOUT] 【{title}】 等待超时，进入下一项")
    return False, None

def main():
    print("=== 开始通过 CLI 批量顺序出图 ===")
    
    # 获取待生成列表
    nodes = get_all_nodes()
    empty_nodes = [n for n in nodes if n.get("status") == "empty"]
    print(f"当前画布中共有 {len(empty_nodes)} 个节点待生成出图。")
    
    # 排序：优先主角与第一集高频资产
    priority_keywords = ["默认", "萧云稷", "老夫人", "戚雪", "戚北捷", "正厅", "墨竹发簪", "紫檀佛珠"]
    
    def sort_key(n):
        title = n.get("title", "")
        for idx, kw in enumerate(priority_keywords):
            if kw in title:
                return (idx, title)
        return (99, title)
    
    empty_nodes.sort(key=sort_key)
    
    success_count = 0
    fail_count = 0
    
    for idx, node in enumerate(empty_nodes):
        nid = node.get("nodeId")
        title = node.get("title")
        print(f"\n进度 [{idx+1}/{len(empty_nodes)}]")
        ok, res_id = run_single_node(nid, title)
        if ok:
            success_count += 1
        else:
            fail_count += 1
        
        # 节点间平滑间隔 2 秒
        time.sleep(2)
        
    print(f"\n=== 全部执行完毕！成功: {success_count} 项，失败/跳过: {fail_count} 项 ===")

if __name__ == '__main__':
    main()
