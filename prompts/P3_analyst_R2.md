# P3 分析师 R2 交叉质询 Prompt 模板

## 使用说明
将此段落追加到每位分析师的第二轮交叉质询 prompt 末尾。

---

## 通用指令（v3.8 R2 交叉质询 — 强制落盘 + 链式安全层）

1. **处理预检标记**：`[!alert]` 必须修正或给出坚持理由，`[!drift]` 逐一解释
2. **标记分歧**：逐条标注「与 XX 一致/分歧」，标注分歧理由
3. **回应待质询**：回答对方初版末尾的「待质询」条目
4. **提交终稿**：修正后的分析 + 质询回应 + 分歧清单

完成 R2 交叉质询后，**立即**将终稿写入文件：

| 分析师 | 落盘路径 |
|--------|----------|
| 🛢️ 油井 | `pipeline/artifacts/{date}_wti_R2.md` |
| 🥇 金匠 | `pipeline/artifacts/{date}_gold_R2.md` |
| 🌍 观澜 | `pipeline/artifacts/{date}_macro_R2.md` |

`{date}` = 当天日期 YYYY-MM-DD。

### 🔗 链式安全层（v3.8 新增 — 数据铁律 v2.2.1）

输出文件头部由 `run_analyst.py --chain --seq 2 --prev-hash <R1_hash>` 自动注入：

```yaml
---
# 链式安全层（数据铁律 v2.2.1）
chain:
  seq: 2
  agent_id: "wti-analyst"
  prev_hash: "<R1 的 hash>"
  hash: "<SHA-256 前 16 位>"
agent:
  role: "wti-analyst"
  fingerprint: "<system_prompt SHA-256 前 8 位>"
---
```

> **关键**：R2 的 `prev_hash` 必须等于 R1 的 `hash`，形成可验证的密码学链。鹰眼在运行脚本时会自动传入正确的 `--prev-hash`。

写入完成后在 SendMessage 回传末尾附言："[分析师名] R2 终稿已落盘：pipeline/artifacts/{date}_[分析师]_R2.md"
