# Commodity Quant Universal Framework v3.8.0

**A standalone Python framework for multi-model adversarial debate commodity analysis. 6-phase pipeline with chain security, evidence quality scoring, and Verifier compliance.**

[English](#commodity-quant-universal-framework-v380) | [中文](#量化大宗通用框架-v380)

---

## Pipeline

```
P0 📡 Collect  → run_pigeon.py (neodata + LongCat dual-engine)
P1 🛢️🥇🌍 R1   → run_analyst.py × 3 (blind analysis + chain security)
P2 🦅 Precheck → precheck.py (citation scan + evidence quality score)
P3 🛢️🥇🌍 R2   → run_analyst.py × 3 (cross-exam + chain security)
P4 🦅 Verdict  → Hawkeye API judgment (multi-model debate synthesis)
P5 🦅 Verify   → precheck.py (final compliance scan + hard-stop)
```

## Quick Start

```bash
pip install -r pipeline/requirements.txt
python pipeline/setup_wizard.py
python orchestrator.py --date 2026-06-08 --run r001
```

## What's New v3.8

| Feature | Description |
|---------|-------------|
| **Chain Security Layer** | Hash chain + identity fingerprints on every analyst output |
| **Evidence Quality Scoring** | 0-10 per citation (neodata=9, LongCat=5, inference=1-2) |
| **Automated Precheck (P2)** | `precheck.py` scans all R1 citations against snapshot |
| **Verifier (P5)** | Post-judgment compliance scan |
| **Universal Orchestrator** | `orchestrator.py` runs full pipeline standalone |
| **Hard-Stop** | P0 fabrication ≥2 → REJECTED |

## Project Structure

```
commodity-quant-universal/
├── orchestrator.py              # Universal pipeline runner
├── agents/hawkeye.md            # Lead arbitrator system prompt
├── pipeline/
│   ├── run_pigeon.py            # Data collector
│   ├── run_analyst.py           # Analyst API caller (+ chain security)
│   ├── precheck.py              # Citation scanner (P2 + P5)
│   ├── setup_wizard.py          # Interactive config generator
│   ├── config_template.yaml     # API configuration template
│   └── requirements.txt
├── prompts/                     # Phase prompt templates
└── .gitignore
```

## Data Iron Law v2.2.1

- Every numeric citation must be traceable to source
- Chain security: SHA-256 hash chain links all analyst outputs
- Hard-stop: P0 fabrication (invented numbers) ≥2 → REJECTED
- Evidence quality scoring: 0-10 per citation

For WorkBuddy integration, see [seraon/commodity-quant](https://github.com/seraon/commodity-quant).

---

# 量化大宗通用框架 v3.8.0

**独立 Python 框架，多模型对抗辩论管线。6 阶段自动化分析，含链式安全、证据质量评分、Verifier 合规扫描。**

[English](#commodity-quant-universal-framework-v380) | [中文](#量化大宗通用框架-v380)

---

## 快速开始

```bash
pip install -r pipeline/requirements.txt
python pipeline/setup_wizard.py
python orchestrator.py --date 2026-06-08 --run r001
```

## v3.8 新增

| 功能 | 说明 |
|------|------|
| **链式安全层** | 每个分析师输出附带哈希链 + 身份指纹 |
| **证据质量评分** | 每条引用按来源评 0-10 分 |
| **自动化预检（P2）** | `precheck.py` 自动扫描 R1 全部引用合规性 |
| **Verifier（P5）** | 裁决后自动合规扫描 |
| **通用 Orchestrator** | `orchestrator.py` 独立运行全管线 |
| **硬止损** | P0 编造 ≥2 → 整份报告 REJECTED |

WorkBuddy 集成版本请见 [seraon/commodity-quant](https://github.com/seraon/commodity-quant)。

---

**Source Available** — 代码公开供查看和参考，未经作者明确授权不得用于商业用途、修改或再分发。
