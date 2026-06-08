"""
Automated Iron Law Precheck & Verifier (Phase 2 & 5) — v3.8.0
Builds a numerical whitelist from control snapshot, scans analyst/judgment
outputs for citations, generates precheck/verification reports.

Usage:
  python pipeline/precheck.py --snapshot X.md --r1 A.md B.md C.md --output report.md
"""
import argparse, re, sys
from pathlib import Path

QUALITY = {"neodata":9,"control_snapshot":8,"wiki":8,"longcat":5,"推理":2,"inference":2}
NAMES = {"wti":"油井","gold":"金匠","macro":"观澜"}
PATTERNS = [
    re.compile(r'(\d+\.?\d*)\s*(?:美元/桶|美元/吨|美元/磅|美元/盎司|万元|亿元|万吨|万张|mbpd|bp|吨|张|美元|%|x|X)'),
    re.compile(r'(\d{2,4})\.?\d*\s*%'),
    re.compile(r'(?:score|评分|价格|price|yield|rate)\s*[：:]\s*(\d+\.?\d*)', re.I),
]

def wl(text):
    d={}
    for p in PATTERNS:
        for m in p.finditer(text):
            v=m.group(1)if m.lastindex else m.group(0)
            c=text[max(0,m.start()-50):min(len(text),m.end()+50)].replace('\n',' ').strip()
            d.setdefault(v,[]).append(c[:80])
    return d

def scan(text, wl):
    r,s=[],set()
    for p in PATTERNS:
        for m in p.finditer(text):
            v=m.group(1)if m.lastindex else m.group(0)
            c=text[max(0,m.start()-40):min(len(text),m.end()+40)].replace('\n',' ').strip()
            d=(v,c[:40])
            if d in s: continue
            s.add(d)
            if v in wl: r.append({"v":v,"c":c,"s":"match","src":wl[v][0]}); continue
            mt=False
            try:
                vi=int(float(v))
                for wk in wl:
                    try:
                        if int(float(wk))==vi: r.append({"v":v,"c":c,"s":"drift","exp":wk,"src":wl[wk][0]}); mt=True; break
                    except: pass
            except: pass
            if not mt: r.append({"v":v,"c":c,"s":"unsourced"})
    return r

def qs(t):
    for k,v in QUALITY.items():
        if k in t.lower(): return v
    return 5

def analyze(nm, path, wl):
    c=scan(Path(path).read_text(encoding="utf-8"),wl)
    a=d=u=0
    sq=[]
    for x in c:
        sq.append(qs(x["c"]if x["s"]!="match"else x.get("src","")))
        if x["s"]=="unsourced":u+=1
        elif x["s"]=="drift":d+=1
    gq=sum(sq)/len(sq)if sq else 0
    return {"name":NAMES.get(nm,nm),"total":len(c),"alerts":a,"drifts":d,"unsourced":u,"quality":round(gq,1),"details":c}

def report(rs, out):
    l=["# Precheck Report\n","| Analyst | Refs | Drifts | Unsourced | Quality |\n|---------|:---:|:---:|:---:|:---:|"]
    for r in rs:
        l.append(f"| {r['name']} | {r['total']} | {r['drifts']} | {r['unsourced']} | {r['quality']}/10 |")
    for r in rs:
        for x in r["details"]:
            if x["s"]!="match": l.append(f"- {x['s']}: `{x['v']}` — {x['c'][:60]}")
    Path(out).parent.mkdir(parents=True,exist_ok=True)
    Path(out).write_text("\n".join(l),encoding="utf-8")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--snapshot",required=True)
    p.add_argument("--r1",nargs="+",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    w=wl(Path(a.snapshot).read_text(encoding="utf-8"))
    print(f"[precheck] {len(w)} values in whitelist")
    ns=["wti","gold","macro"]if len(a.r1)==3 else["verdict"]
    rs=[]
    for n,rp in zip(ns,a.r1):
        r=analyze(n,rp,w); rs.append(r)
        print(f"[precheck] {r['name']}: {r['total']}R D={r['drifts']} U={r['unsourced']} Q={r['quality']}")
    report(rs,a.output)
    print(f"[precheck] → {a.output}")

if __name__=="__main__": main()
