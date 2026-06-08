# P1 分析师 R1 初版 Prompt 模板

## 使用说明
将此段落追加到每位分析师（油井/金匠/观澜）的第一轮 prompt 末尾。

---

## 通用指令（v3.8 R1 初版 — 强制落盘 + 链式安全层）

完成 R1 初版分析后，**立即**将完整报告写入以下路径。SendMessage 回传鹰眼的**同时**写入文件——这是管道 artifact 机制，不写入则下一阶段无法读取。

| 分析师 | 落盘路径 |
|--------|----------|
| 🛢️ 油井 | `pipeline/artifacts/{date}_wti_R1.md` |
| 🥇 金匠 | `pipeline/artifacts/{date}_gold_R1.md` |
| 🌍 观澜 | `pipeline/artifacts/{date}_macro_R1.md` |

`{date}` = 当天日期 YYYY-MM-DD，例如 `2026-06-06`。

### 🔗 链式安全层（v3.8 新增 — 数据铁律 v2.2.1）

输出文件头部由 `run_analyst.py --chain` 自动注入，格式如下（**分析师无需手动编写**）：

```yaml
---
# 链式安全层（数据铁律 v2.2.1）
chain:
  seq: 1
  agent_id: "wti-analyst"  # 或 gold-analyst / macro-strategist
  prev_hash: "genesis"
  hash: "<SHA-256 前 16 位>"
agent:
  role: "wti-analyst"
  fingerprint: "<system_prompt SHA-256 前 8 位>"
---
```

> **分析师职责**：你无需关心链式安全层的内容——它由管道脚本自动计算并注入。你只需按数据铁律要求产出分析内容即可。

写入完成后在 SendMessage 回传末尾附言："[分析师名] R1 已落盘：pipeline/artifacts/{date}_[分析师]_R1.md"
