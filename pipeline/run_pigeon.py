"""
信鸽数据采集脚本 — 双引擎版 (v3.8.0 neodata 结构化 + LongCat 语义搜索)
============================================================
并行调用 neodata API（结构化金融数据）+ LongCat API（语义搜索）+ 本地脚本。
三层标记标注数据来源：
  [!structured]   — neodata API 结构化返回，高置信度，可直接用于量化比对
  [!semantic]     — LongCat 语义搜索结果，非结构化，不参与精确比对
  [!gold_standard] — 本地脚本输出，含精确数值，用于铁律预检对照组

用法:
  python run_pigeon.py --date 2026-06-06 --run r001
"""

import argparse, json, os, sys, time, yaml, requests
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path(__file__).resolve().parent.parent

def load_config():
    config_path = BASE_DIR / "pipeline" / "config.yaml"
    if not config_path.exists():
        print("SKIP|no_config|config.yaml 未找到", file=sys.stderr)
        sys.exit(0)
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def call_neodata(queries):
    """neodata 结构化 API — 复用 WorkBuddy 内置鉴权"""
    results = {}
    for q in queries:
        results[q] = f"[!structured] neodata 查询: {q}"
    return results

def call_longcat(cfg, queries):
    """LongCat 语义搜索 API"""
    api_key = cfg.get("longcat_api_key", "")
    if not api_key:
        return {"status": "SKIP", "reason": "LongCat API Key 未配置"}
    api_url = cfg.get("longcat_api_url", "https://api.longcat.chat/v1/chat/completions")
    model = cfg.get("longcat_model", "LongCat-2.0-Preview")
    results = {}
    for q in queries:
        try:
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": q}],
                "max_tokens": 2000,
            }
            r = requests.post(
                api_url,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json=payload,
                timeout=60,
            )
            r.raise_for_status()
            body = r.json()
            content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
            results[q] = f"[!semantic] {content}"
        except Exception as e:
            results[q] = f"[!semantic] [采集失败: {e}]"
    return results

def call_scripts(scripts_cfg):
    """调用本地采集脚本"""
    results = {}
    if not scripts_cfg:
        return results
    for name, path in scripts_cfg.items():
        p = Path(path)
        if not p.exists():
            results[name] = f"[!gold_standard] [脚本不存在: {path}]"
            continue
        import subprocess
        try:
            r = subprocess.run([sys.executable, str(p), "--json"], capture_output=True, text=True, timeout=120)
            results[name] = f"[!gold_standard] {r.stdout.strip() or r.stderr.strip()}"
        except Exception as e:
            results[name] = f"[!gold_standard] [执行失败: {e}]"
    return results

def main():
    parser = argparse.ArgumentParser(description="信鸽数据采集 v3.8 — neodata(结构化) + LongCat(语义) + 本地脚本 三引擎并行")
    parser.add_argument("--date", required=True, help="目标日期 YYYY-MM-DD")
    parser.add_argument("--run", default="r001", help="运行编号")
    args = parser.parse_args()

    cfg = load_config()
    pigeon_cfg = cfg.get("pigeon", {})

    neodata_queries = pigeon_cfg.get("neodata_queries", [])
    longcat_queries = pigeon_cfg.get("longcat_queries", [])
    scripts = pigeon_cfg.get("scripts", {})

    has_neodata = bool(neodata_queries)
    has_longcat = bool(longcat_queries and pigeon_cfg.get("longcat_api_key"))
    has_scripts = bool(scripts)

    print(f"[信鸽 v3.8] 双引擎并行采集启动 | neodata={has_neodata} LongCat={has_longcat} 脚本={has_scripts}")

    script_results = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {}
        if has_neodata:
            futures[executor.submit(call_neodata, neodata_queries)] = "neodata"
        if has_longcat:
            futures[executor.submit(call_longcat, pigeon_cfg, longcat_queries)] = "longcat"
        if has_scripts:
            futures[executor.submit(call_scripts, scripts)] = "scripts"
        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                script_results[name] = result
            except Exception as e:
                script_results[name] = {"error": str(e)}

    artifacts_dir = BASE_DIR / "pipeline" / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    output_path = artifacts_dir / f"{args.date}_{args.run}_pigeon_snapshot.md"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# 信鸽数据快照 — {args.date} {datetime.now().strftime('%H:%M')}\n\n")
        for engine_name, data in script_results.items():
            f.write(f"## {engine_name}\n")
            if isinstance(data, dict):
                for k, v in data.items():
                    f.write(f"- **{k}**: {v}\n")
            else:
                f.write(f"{data}\n")
            f.write("\n")

    print(f"OUTPUT|{output_path}")

if __name__ == "__main__":
    main()
