"""
通用分析师脚本 (v3.8.0)
替代 Agent spawn，直接调用配置的模型 API 进行异构辩论。
输入信鸽 v3.6 双引擎快照（三层标记 [!structured]/[!semantic]/[!gold_standard]），
脚本自动从快照中提取对应品类的结构化数据进行分析。

v3.8.0: 新增链式安全层（数据铁律 v2.2.1）—— --chain 模式下
  自动计算 agent_fingerprint（SHA-256 of system prompt）和
  content hash（SHA-256 of output），追加到输出文件头部。

用法:
  # P1 R1 — 从信鸽快照生成初版分析（含链式安全层）
  python run_analyst.py --type wti --phase r1 \
    --input pipeline/artifacts/2026-06-06_r001_pigeon_snapshot.md \
    --output pipeline/artifacts/2026-06-06_r001_wti_R1.md \
    --chain --seq 1 --prev-hash genesis

  # P3 R2 — 交叉质询终稿（含链式安全层，prev-hash 取自 R1 产物 hash）
  python run_analyst.py --type gold --phase r2 \
    --input pipeline/artifacts/2026-06-06_r001_gold_cross_exam.md \
    --output pipeline/artifacts/2026-06-06_r001_gold_R2.md \
    --chain --seq 2 --prev-hash a1b2c3d4e5f6a7b8

  # 自定义 system prompt
  python run_analyst.py --type macro --system "你是宏观策略师..." --input data.md

配置: 从 pipeline/config.yaml 读取各分析师 API 设置
"""

import argparse, hashlib, json, os, sys, yaml, requests
from pathlib import Path
from datetime import datetime

# ─── 链式安全层（v3.8.0 数据铁律 v2.2.1） ───
AGENT_ID_MAP = {"wti": "wti-analyst", "gold": "gold-analyst", "macro": "macro-strategist"}

def compute_fingerprint(system_prompt: str) -> str:
    """SHA-256(system_prompt_full_text) 取前 8 位 hex"""
    return hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()[:8]

def compute_hash(prev_hash: str, agent_id: str, seq: int, content: str) -> str:
    """SHA-256({prev_hash}|{agent_id}|{seq}|{content}) 取前 16 位 hex"""
    payload = f"{prev_hash}|{agent_id}|{seq}|{content}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

def build_chain_block(prev_hash: str, agent_id: str, seq: int,
                       fingerprint: str, content: str) -> str:
    """构建链式安全层 YAML 块，插入到输出文件头部"""
    content_hash = compute_hash(prev_hash, agent_id, seq, content)
    return (
        f"---\n"
        f"# 链式安全层（数据铁律 v2.2.1）\n"
        f"# 此块由 run_analyst.py 自动生成，不可手动编辑\n"
        f"chain:\n"
        f"  seq: {seq}\n"
        f"  agent_id: \"{agent_id}\"\n"
        f"  prev_hash: \"{prev_hash}\"\n"
        f"  hash: \"{content_hash}\"\n"
        f"agent:\n"
        f"  role: \"{agent_id}\"\n"
        f"  fingerprint: \"{fingerprint}\"\n"
        f"---\n\n"
    )

# ─── 配置加载 ───
BASE_DIR = Path(__file__).resolve().parent.parent

def load_analyst_config(analyst_type: str) -> dict:
    """加载特定分析师的 API 配置，未配时优雅跳过"""
    config_path = BASE_DIR / "pipeline" / "config.yaml"
    if not config_path.exists():
        print(f"SKIP|no_config|{analyst_type}|config.yaml 未找到", file=sys.stderr)
        sys.exit(0)
    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    analysts = cfg.get("analysts", {})
    if analyst_type not in analysts:
        print(f"SKIP|unknown_type|{analyst_type}|类型未在 config.yaml 中定义", file=sys.stderr)
        sys.exit(0)
    a = analysts[analyst_type]
    if not a.get("api_key") or not a.get("api_url"):
        print(f"SKIP|no_api|{analyst_type}|{a.get('name', analyst_type)} 未配 API — 鹰眼应回退到 Agent spawn", file=sys.stderr)
        sys.exit(0)
    return a

def load_agent_prompt(md_path: str) -> str:
    """加载 agent .md 文件作为 system prompt（带 frontmatter 剔除）"""
    full_path = BASE_DIR / md_path
    if not full_path.exists():
        print(f"[warn] Agent prompt 文件不存在: {full_path}，将使用默认 prompt", file=sys.stderr)
        return "你是一位专业的金融分析师。请基于给定数据生成结构化分析报告。只引用实际数据，不编造。"
    text = full_path.read_text(encoding="utf-8")
    return text.strip()

def load_agent_prompt_clean(md_path: str) -> str:
    """加载 agent .md 作为 system prompt（剔除 frontmatter，送 API）"""
    text = load_agent_prompt(md_path)
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            text = parts[2]
    return text.strip()

def call_api(analyst_cfg: dict, system_prompt: str, user_prompt: str) -> str:
    """调用分析师配置的模型 API"""
    api_url = analyst_cfg["api_url"]
    api_key = analyst_cfg["api_key"]
    model = analyst_cfg["model"]
    timeout = analyst_cfg.get("timeout_seconds", 120)
    max_tokens = analyst_cfg.get("max_tokens", 4000)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.7,
    }
    print(f"[analy] 调用 {model} ({analyst_cfg.get('name','?')})...", file=sys.stderr)
    r = requests.post(
        api_url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=timeout,
    )
    r.raise_for_status()
    body = r.json()
    if "choices" in body and body["choices"]:
        return body["choices"][0]["message"]["content"]
    elif "data" in body and "content" in body["data"]:
        return body["data"]["content"]
    else:
        raise RuntimeError(f"未知 API 响应格式: {json.dumps(body, ensure_ascii=False)[:500]}")

def build_r1_prompt(analyst_type: str, input_content: str) -> str:
    """构建 R1 初版分析的用户提示"""
    task_map = {
        "wti": "基于以下数据快照，撰写WTI原油量化多空评分R1初版分析报告。"
               "包含：多空因子逐项拆解、加权总分、方向判断、关键风险。严格引用数据来源，不编造数值。",
        "gold": "基于以下数据快照，撰写黄金+紫金矿业定量评分R1初版分析报告。"
                "包含：定价因子逐项拆解（美元/实际利率/避险/央行购金）、综合评分、方向判断。严格引用数据来源。",
        "macro": "基于以下数据快照，撰写宏观环境诊断R1初版分析报告。"
                 "包含：美债期限结构、通胀预期、美元走势、地缘风险、对大宗商品的影响传导。严格引用数据来源。",
    }
    task = task_map.get(analyst_type, "基于以下数据快照，撰写R1初版分析报告。严格引用数据来源。")
    return f"{task}\n\n---\n## 数据快照\n\n{input_content}\n\n---\n请输出结构化的R1分析报告，每条判断标注 [来源: XX]。"

def build_r2_prompt(input_content: str) -> str:
    """构建 R2 交叉质询终稿的用户提示"""
    return f"""你收到了鹰眼发来的交叉质询指令。请基于以下质询点，在R1基础上完成R2终稿。
要求：
1. 逐条回应每个质询点（接受/反驳/部分接受+证据）
2. 修正R1中的事实错误（如有）
3. 更新评分/判断（如质询引入新证据）
4. 最终给出方向判断和置信度
5. 所有声明必须有 [来源: XX] 标注

---
## 交叉质询内容

{input_content}

---
请输出结构化的R2终稿分析报告。"""

def main():
    parser = argparse.ArgumentParser(description="量化大宗分析师 — 异构模型 API 调用")
    parser.add_argument("--type", required=True, choices=["wti", "gold", "macro"],
                        help="分析师类型: wti(油井) / gold(金匠) / macro(观澜)")
    parser.add_argument("--phase", choices=["r1", "r2"], default="r1",
                        help="分析阶段: r1(初版) / r2(交叉质询终稿)")
    parser.add_argument("--input", required=True, help="输入文件路径（快照或质询指令）")
    parser.add_argument("--output", required=True, help="输出文件路径")
    parser.add_argument("--system", help="自定义 system prompt（覆盖 agent .md）")
    parser.add_argument("--config", help="自定义配置文件路径")
    parser.add_argument("--chain", action="store_true", help="启用链式安全层（数据铁律 v2.2.1）")
    parser.add_argument("--seq", type=int, default=1, help="链序列号（R1=1, R2=2, ...）")
    parser.add_argument("--prev-hash", type=str, default="genesis", help="前一输出的 hash（首轮默认为 genesis）")
    args = parser.parse_args()

    if args.config:
        cfg = yaml.safe_load(open(args.config, encoding="utf-8"))
        analyst_cfg = cfg["analysts"][args.type]
    else:
        analyst_cfg = load_analyst_config(args.type)

    agent_md_path = analyst_cfg.get("agent_md", f"agents/{args.type}-analyst.md")
    if args.system:
        system_prompt = args.system
        system_prompt_raw = args.system
    else:
        system_prompt = load_agent_prompt_clean(agent_md_path)
        system_prompt_raw = load_agent_prompt(agent_md_path)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[error] 输入文件不存在: {input_path}", file=sys.stderr)
        sys.exit(1)
    input_content = input_path.read_text(encoding="utf-8")

    if args.phase == "r1":
        user_prompt = build_r1_prompt(args.type, input_content)
    else:
        user_prompt = build_r2_prompt(input_content)

    try:
        result = call_api(analyst_cfg, system_prompt, user_prompt)
    except Exception as e:
        print(f"[error] API 调用失败: {e}", file=sys.stderr)
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            f"# {analyst_cfg.get('name', args.type)} {args.phase.upper()} 分析失败\n\n"
            f"错误: {e}\n"
            f"时间: {datetime.now().isoformat()}\n"
            f"模型: {analyst_cfg.get('model', '?')}\n",
            encoding="utf-8"
        )
        print(f"FAIL|{args.output}|error={e}", file=sys.stderr)
        sys.exit(1)

    agent_id = AGENT_ID_MAP[args.type]
    output_content = result

    if args.chain:
        fingerprint = compute_fingerprint(system_prompt_raw)
        chain_block = build_chain_block(
            prev_hash=args.prev_hash, agent_id=agent_id, seq=args.seq,
            fingerprint=fingerprint, content=output_content,
        )
        output_content = chain_block + output_content
        content_hash = compute_hash(args.prev_hash, agent_id, args.seq, result)
    else:
        content_hash = "N/A"

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(output_content, encoding="utf-8")

    if args.chain:
        print(f"OK|{args.output}|{len(result)} chars|model={analyst_cfg['model']}|chain=yes|hash={content_hash}|fingerprint={compute_fingerprint(system_prompt_raw)}")
    else:
        print(f"OK|{args.output}|{len(result)} chars|model={analyst_cfg['model']}")
    return 0

if __name__ == "__main__":
    main()
