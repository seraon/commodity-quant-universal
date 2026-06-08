# P4 轻量 Verifier Prompt 模板（v3.8 新增 — 数据铁律 v2.2.1）

## 使用说明

鹰眼在 Phase 4 输出终稿（MD摘要 + HTML报告）后，**对 Judge 裁决进行轻量合规验证**。
Verifier 不是独立 Agent——鹰眼自行执行，使用极简逻辑（< 200 tokens 推理）。

---

## 设计原则

Verifier 只做一件事：**逐条检查鹰眼裁决中引用的每个数值是否在对照组快照中出现过**。

- ❌ 不做论证质量判断
- ❌ 不做逻辑审查
- ❌ 不评估权重合理性
- ✅ 只做数据引用合规检查：「这个数字在原始数据里能找到吗？」

---

## 执行流程

### 步骤 1：构建白名单

鹰眼从 Phase 0 对照组快照 `pipeline/artifacts/{date}_control_snapshot.md` 中提取所有含单位的数值。

### 步骤 2：扫描裁决产出

鹰眼扫描 Phase 4 的 Markdown 摘要中的所有数值引用，与白名单逐条比对。

### 步骤 3：逐条标记

- ✅ 在白名单中 → `[!verified]`
- ⚠️ 不在白名单中但为推理衍生值 → `[!estimated]`
- ❌ 不在白名单中且无推理标注 → `[!unsourced]`

### 步骤 4：判定

| 违规数 | 判定 | 操作 |
|:---:|------|------|
| 0 | PASS | 裁决通过，标注 `[!verified]` |
| 1-2 | PASS (轻伤) | 标注 `[!verified-with-warnings]` |
| ≥ 3 | FAIL | 标注 `[!verification-failed]` |
| P0 违规 ≥ 2 | REJECT | 硬止损触发，鹰眼须返工 |

---

## 验证报告格式

验证完成后写入：`pipeline/artifacts/{date}_verification.md`

---

## 硬止损联动（v2.2.1）

| 触发条件 | 操作 |
|---------|------|
| P0 违规（编造数值）≥ 2 条 | `[!REJECTED]` 该报告不可用，鹰眼返工 |
| P0 + P1 合计 ≥ 3 条 | `[!REJECTED]` 该报告不可用 |
| Verifier FAIL（无来源 ≥ 3） | `[!verification-failed]` 标注在 MD 摘要末尾 |
| Verifier PASS | `[!verified]` 标注在 MD 摘要脚注 |

> 被 REJECTED 的输出标记为 `[!REJECTED]`，不计入后续分析流程。用户应被明确告知原因。
