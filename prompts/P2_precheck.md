# P2 铁律预检 Prompt 模板

## 使用说明
鹰眼自行比对（v3.5.1 起合入鹰眼主线程）：本轮产出 vs 对照组快照，输出三级标记。完成后落盘预检报告。

v3.8 新增：证据质量评分——每个数值引用不仅标注来源，还按来源类型评估可信度 0-10 分。

---

## 证据质量评分（v3.8 新增 — 数据铁律 v2.2.1）

预检时，除了三级标记（[!alert]/[!drift]/[!unsourced]），**必须为每个数值引用标注质量分**：

| 质量分 | 来源类型 | 示例 |
|:---:|------|------|
| 9-10 | neodata API 结构化返回 / 原始快照 | `neodata API`, `EIA API`, `yfinance 直接返回值` |
| 7-8 | 编译知识库 / 已验证数据 | `wiki/XX`, `pipeline R1 产物`, 多源交叉验证通过 |
| 5-6 | 信鸽 LongCat 语义搜索 / 单次采集 | `longcat`, `pigeon_snapshot [来源: longcat]` |
| 3-4 | 非结构化语义返回 | `LongCat 语义搜索结果`, `AI-Trader 噪音温度计` |
| 1-2 | 推理 / 估算（显式标注） | `[来源: 推理]`, `[!estimated]` |
| 0 | 无来源 | `[!unsourced]` → 直接标记编造 |

### 质量加权规则

- 每个数值 `confidence = raw_confidence × (quality_score / 10)`
- 质量分 ≤ 2 的数值在辩论中**可被对方直接质疑而不需要反向证据**
- 最终报告的**全局质量分** = 所有引用数值的质量分均值
- 全局质量分 < 4 的报告标注 `[!low-quality]`，提示用户交叉验证

### 预检报告中的质量分格式

```markdown
| 数值 | 来源 | 质量分 | 标记 |
|------|------|:---:|------|
| 68.47 | neodata API | 9 | [!match] |
| 4.25% | control_snapshot | 8 | [!match] |
| "央行购金强劲" | longcat | 5 | [!semantic] |
| PE 9.81x → EPS ¥3.02 | 推理 | 2 | [!estimated] |
```

---

⚠️ **预检报告落盘指令（v3.5 强制）**

预检完成后，将三级标记表 + 逐条标记详情 + **证据质量评分表**写入：
```
pipeline/artifacts/{date}_precheck_R{round}.md
```

`{round}` = 1, 2, 或 3（辩论轮次）。

写入完成后在 SendMessage 中附言："预检 R{round} 已落盘：pipeline/artifacts/{date}_precheck_R{round}.md"
