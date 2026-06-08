#!/usr/bin/env python3
"""
Commodity Quant Pipeline Orchestrator v3.8.0
Universal 6-phase adversarial debate pipeline runner.
No framework dependency. Just Python + config.yaml with API keys.

Usage:
  python orchestrator.py --date 2026-06-08 --run r001
  python orchestrator.py --date 2026-06-08 --run r001 --from-phase P3
"""

import argparse, os, subprocess, sys, yaml
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

BASE = Path(__file__).resolve().parent
PIPELINE = BASE / "pipeline"
ARTIFACTS = PIPELINE / "artifacts"
ANALYST_NAMES = {"wti": "油井", "gold": "金匠", "macro": "观澜"}
PHASES = ["P0", "P1", "P2", "P3", "P4", "P5"]

def load_config():
    cfg_path = PIPELINE / "config.yaml"
    if not cfg_path.exists():
        print("ERROR: config.yaml not found. Run: python pipeline/setup_wizard.py")
        sys.exit(1)
    return yaml.safe_load(cfg_path.read_text(encoding="utf-8"))

def _run(cmd, label=""):
    print(f"\n{'='*60}\n[{label}] {cmd}\n{'='*60}")
    r = subprocess.run(cmd, shell=True, cwd=str(BASE))
    ok = r.returncode == 0
    print(f"[{label}] {'OK' if ok else 'FAILED'}")
    return ok

def extract_hash(filepath):
    try:
        for line in open(filepath, encoding="utf-8"):
            if "hash:" in line and '"' in line:
                return line.split('"')[1]
    except: pass
    return "genesis"

def phase_0(cfg, date, run_id):
    snap = ARTIFACTS / f"{date}_{run_id}_pigeon_snapshot.md"
    ok = _run(f'python "{PIPELINE}/run_pigeon.py" --date {date} --run {run_id}', "P0 信鸽采集")
    return str(snap) if ok else None

def phase_1(cfg, date, run_id, snapshot):
    arts = {}
    def run_one(atype, name):
        out = ARTIFACTS / f"{date}_{run_id}_{atype}_R1.md"
        ok = _run(f'python "{PIPELINE}/run_analyst.py" --type {atype} --phase r1 --input "{snapshot}" --output "{out}" --chain --seq 1 --prev-hash genesis', f"P1 {name} R1")
        return atype, str(out), ok
    with ThreadPoolExecutor(max_workers=3) as ex:
        for f in [ex.submit(run_one, t, n) for t,n in [("wti","油井"),("gold","金匠"),("macro","观澜")]]:
            atype, path, ok = f.result()
            if ok:
                arts[f"{atype}_R1"] = path
                arts[f"{atype}_r1_hash"] = extract_hash(path)
    return arts if len(arts) >= 3 else None

def phase_2(snapshot, r1_arts):
    out = r1_arts["wti_R1"].replace("_wti_R1", "_precheck_R1")
    w = r1_arts["wti_R1"]; g = r1_arts["gold_R1"]; m = r1_arts["macro_R1"]
    ok = _run(f'python "{PIPELINE}/precheck.py" --snapshot "{snapshot}" --r1 "{w}" "{g}" "{m}" --output "{out}"', "P2 铁律预检")
    return out if ok else None

def phase_3(cfg, date, run_id, precheck, r1_arts):
    arts = {}
    precheck_text = Path(precheck).read_text(encoding="utf-8")
    for atype, aname in [("wti","油井"),("gold","金匠"),("macro","观澜")]:
        cross = ARTIFACTS / f"{date}_{run_id}_{atype}_cross_exam.md"
        with open(cross,"w",encoding="utf-8") as f:
            f.write(f"# Cross-Examination for {aname}\n\n## Precheck\n{precheck_text}\n")
            for o in ["wti","gold","macro"]:
                if o != atype and f"{o}_R1" in r1_arts:
                    f.write(f"\n## {ANALYST_NAMES[o]} R1\n{Path(r1_arts[f'{o}_R1']).read_text(encoding='utf-8')[:3000]}\n")
        out = ARTIFACTS / f"{date}_{run_id}_{atype}_R2.md"
        ph = r1_arts.get(f"{atype}_r1_hash","genesis")
        ok = _run(f'python "{PIPELINE}/run_analyst.py" --type {atype} --phase r2 --input "{cross}" --output "{out}" --chain --seq 2 --prev-hash {ph}', f"P3 {aname} R2")
        if ok: arts[f"{atype}_R2"] = str(out)
    return arts

def phase_4(cfg, date, run_id, r1_arts, r2_arts, snapshot):
    hc = cfg.get("analysts",{}).get("hawkeye",{})
    if not hc.get("api_key"):
        print("[P4] Hawkeye API not configured — raw summary")
        out = ARTIFACTS / f"{date}_{run_id}_verdict.md"
        parts = [f"# Verdict — {date}\n"]
        for a in ["wti","gold","macro"]:
            k = f"{a}_R2"
            if k in r2_arts:
                parts.append(f"## {ANALYST_NAMES[a]}\n{Path(r2_arts[k]).read_text(encoding='utf-8')[:2000]}")
        out.write_text("\n".join(parts), encoding="utf-8")
        return str(out)
    import requests
    system = (PIPELINE.parent/"agents"/"hawkeye.md").read_text(encoding="utf-8")
    prompt = [f"# Judgment — {date}"]
    prompt.append(Path(snapshot).read_text(encoding="utf-8")[:5000])
    for a in ["wti","gold","macro"]:
        for ph, arts in [("R1",r1_arts),("R2",r2_arts)]:
            k = f"{a}_{ph}"
            if k in arts:
                prompt.append(f"## {ANALYST_NAMES[a]} {ph}\n{Path(arts[k]).read_text(encoding='utf-8')[:3000]}")
    r = requests.post(hc["api_url"], headers={"Authorization":f"Bearer {hc['api_key']}","Content-Type":"application/json"}, json={"model":hc.get("model","deepseek-v4-pro"),"messages":[{"role":"system","content":system},{"role":"user","content":"\n\n".join(prompt[-4:])}],"max_tokens":4000,"temperature":0.7}, timeout=180)
    verdict = r.json()["choices"][0]["message"]["content"]
    out = ARTIFACTS / f"{date}_{run_id}_verdict.md"
    out.write_text(verdict, encoding="utf-8")
    return str(out)

def phase_5(snapshot, verdict):
    out = verdict.replace("_verdict", "_verification")
    ok = _run(f'python "{PIPELINE}/precheck.py" --snapshot "{snapshot}" --r1 "{verdict}" "{verdict}" "{verdict}" --output "{out}"', "P5 Verifier")
    return out if ok else None

def main():
    p = argparse.ArgumentParser(description="Commodity Quant Pipeline Orchestrator v3.8")
    p.add_argument("--date", required=True)
    p.add_argument("--run", default="r001")
    p.add_argument("--from-phase", choices=PHASES, default="P0")
    p.add_argument("--to-phase", choices=PHASES, default="P5")
    p.add_argument("--snapshot", help="Skip P0, use existing")
    args = p.parse_args()
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    cfg = load_config()
    si, ei = PHASES.index(args.from_phase), PHASES.index(args.to_phase)
    to_run = PHASES[si:ei+1]
    print(f"\nCommodity Quant Pipeline v3.8 — {args.date}/{args.run}")
    print(f"  Phases: {' → '.join(to_run)}")
    snap = args.snapshot; r1 = {}; r2 = {}; state = {}
    for ph in to_run:
        if ph == "P0": snap = phase_0(cfg, args.date, args.run) or snap
        elif ph == "P1" and snap: r1 = phase_1(cfg, args.date, args.run, snap) or {}
        elif ph == "P2" and len(r1)>=3: state["precheck"] = phase_2(snap, r1)
        elif ph == "P3" and len(r1)>=3:
            pc = state.get("precheck", str(ARTIFACTS/f"{args.date}_{args.run}_precheck_R1.md"))
            if Path(pc).exists(): r2 = phase_3(cfg, args.date, args.run, pc, r1)
        elif ph == "P4":
            v = phase_4(cfg, args.date, args.run, r1, r2, snap)
            if v: state["verdict"] = v
        elif ph == "P5" and snap and "verdict" in state:
            state["verification"] = phase_5(snap, state["verdict"])
    print(f"\nPipeline Complete — {ARTIFACTS}")
    for k,v in state.items():
        if v: print(f"  {k}: {v}")

if __name__ == "__main__": main()
