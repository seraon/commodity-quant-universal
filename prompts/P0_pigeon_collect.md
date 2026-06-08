# P0 信鸽数据采集 Prompt 模板

## 使用说明
将此模板内容追加到信鸽的采集指令中，确保数据快照自动落盘。

---

⚠️ **快照落盘指令（v3.5 强制执行）**

数据采集完成后，将完整数据快照写入：
```
pipeline/artifacts/{date}_pigeon_snapshot.md
```

写入格式：
```markdown
# 信鸽数据快照 — {date} {time}

## WTI 数据
（所有采集到的 WTI 相关数据，含采集时间戳和来源脚本）

## 黄金数据
（所有采集到的黄金相关数据）

## CFTC 持仓
（Managed Money + Producer 净持仓）

## 噪音温度计
（AI-Trader 噪音 0-100）

## 地缘情绪
（霍尔木兹 5 情景概率分布）

## 对照组（11项跨源验证）
（跨源验证数据，用于铁律预检比对）
```

写入完成后在 SendMessage 中附言："数据快照已落盘：pipeline/artifacts/{date}_pigeon_snapshot.md"
