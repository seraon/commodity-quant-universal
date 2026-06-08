#!/usr/bin/env python3
"""
Commodity Quant 专家团 — 一键配置向导 (v3.8.0)
======================================================
用法: python setup_wizard.py
交互式填写各分析师的 API Key 和模型名称，生成 config.yaml。
所有 API 均为可选——不配也能跑。
"""

import os, sys, yaml
from pathlib import Path

_C = {'bold': '\033[1m', 'dim': '\033[2m', 'R': '\033[31m', 'G': '\033[32m', 'Y': '\033[33m', 'C': '\033[36m', 'W': '\033[37m', 'reset': '\033[0m'}
def _color(code, text): return f"{code}{text}{_C['reset']}" if sys.stdout.isatty() else text
def _input(prompt, default=""):
    d = f" [{default}]" if default else ""
    val = input(f"{prompt}{d}: ").strip()
    return val if val else default

def main():
    BASE = Path(__file__).resolve().parent.parent
    config_path = BASE / "pipeline" / "config.yaml"
    template_path = BASE / "pipeline" / "config_template.yaml"
    print(f"\n{_color(_C['bold']+_C['W'], 'Commodity Quant 专家团 — v3.8.0 配置向导')}")
    print(f"{_color(_C['dim'], '所有 API 均为可选 — 不配也能跑！')}\n")
    if config_path.exists():
        if _input(f"{_color(_C['Y'], 'config.yaml 已存在，覆盖？')} (y/n)", "n").lower() != 'y':
            print("取消。"); return
    cfg = yaml.safe_load(template_path.read_text(encoding="utf-8")) if template_path.exists() else {}
    print(f"\n{_color(_C['bold']+_C['C'], '── 信鸽 LongCat API ──')}")
    cfg['pigeon']['longcat_api_key'] = _input("LongCat API Key", cfg.get('pigeon',{}).get('longcat_api_key',''))
    cfg['pigeon']['longcat_api_url'] = _input("LongCat API URL", cfg.get('pigeon',{}).get('longcat_api_url','https://api.longcat.chat/v1/chat/completions'))
    for key in ['wti','gold','macro']:
        a = cfg.setdefault('analysts',{}).setdefault(key,{})
        print(f"\n{_color(_C['bold']+_C['C'], f'── {a.get(\"name\",key)} API ──')}")
        a['api_url'] = _input("API URL (OpenAI 兼容)", a.get('api_url',''))
        a['api_key'] = _input("API Key", a.get('api_key',''))
        a['model'] = _input("模型名称", a.get('model',''))
        a['agent_md'] = a.get('agent_md', f'agents/{key}-analyst.md')
        a['max_tokens'] = a.get('max_tokens', 4000)
        a['timeout_seconds'] = a.get('timeout_seconds', 120)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print(f"\n{_color(_C['G'], 'config.yaml 已生成！')}\n   路径: {config_path}\n   API Key 不会泄露。")

if __name__ == "__main__": main()
