#!/usr/bin/env python3
import hashlib, json, os, re, shutil, subprocess, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
RESULTS.mkdir(exist_ok=True)

FIXTURES = {
"seed": r'''#include <stdio.h>
static int mix(int x) { return (x * 3 + 7) ^ (x >> 1); }
int main(void) {
  int s = 0;
  for (int i = 0; i < 32; ++i) {
    if (i & 1) s += mix(i); else s -= mix(i);
  }
  printf("%d\n", s);
  return 0;
}
''',
"rcl": r'''#include <stdio.h>
static int mix(int x) {
  int t0 = x * 3;
  int t1 = t0 + 7;
  int t2 = x >> 1;
  int t3 = t1 ^ t2;
  return t3;
}
int main(void) {
  int s = 0;
  int i = 0;
loop_head: ;
  if (!(i < 32)) goto loop_done;
  int m = mix(i);
  int odd = i & 1;
  if (odd) goto odd_path;
  s -= m;
  goto join_path;
odd_path: ;
  s += m;
join_path: ;
  ++i;
  goto loop_head;
loop_done: ;
  printf("%d\n", s);
  return 0;
}
''',
"ocp": r'''#include <stdio.h>
#line 173 "generated_alpha.c"
static int mix(int x) { return (x * 3 + 7) ^ (x >> 1); }
#line 907 "generated_beta.c"
int main(void) {
  int s = 0;
#line 41 "generated_loop.c"
  for (int i = 0; i < 32; ++i) {
    if (i & 1) s += mix(i); else s -= mix(i);
  }
#line 811 "generated_exit.c"
  printf("%d\n", s);
  return 0;
}
''',
"fco": r'''#include <stdio.h>
static __attribute__((noinline, hot, aligned(32))) int mix(int x) {
  return (x * 3 + 7) ^ (x >> 1);
}
int main(void) {
  int s __attribute__((aligned(16))) = 0;
  for (int i = 0; i < 32; ++i) {
    if (i & 1) s += mix(i); else s -= mix(i);
  }
  printf("%d\n", s);
  return 0;
}
''',
"combined": r'''#include <stdio.h>
#line 173 "generated_alpha.c"
static __attribute__((noinline, hot, aligned(32))) int mix(int x) {
  int t0 = x * 3;
  int t1 = t0 + 7;
  int t2 = x >> 1;
  int t3 = t1 ^ t2;
  return t3;
}
#line 907 "generated_beta.c"
int main(void) {
  int s __attribute__((aligned(16))) = 0;
  int i = 0;
#line 41 "generated_loop.c"
loop_head: ;
  if (!(i < 32)) goto loop_done;
  int m = mix(i);
  int odd = i & 1;
  if (odd) goto odd_path;
  s -= m;
  goto join_path;
odd_path: ;
  s += m;
join_path: ;
  ++i;
  goto loop_head;
loop_done: ;
#line 811 "generated_exit.c"
  printf("%d\n", s);
  return 0;
}
'''
}

DIE_START = re.compile(r"^\s*<\d+><[0-9a-f]+>: Abbrev Number: \d+ \((DW_TAG_[^)]+)\)")
ATTR = re.compile(r"\b(DW_AT_[A-Za-z0-9_]+)\b")
DEBUG_SEC = re.compile(r"\[\s*\d+\]\s+(\.debug\S*)\s+\S+\s+[0-9a-fA-F]+\s+[0-9a-fA-F]+\s+([0-9a-fA-F]+)\b")

def run(cmd, **kw):
    return subprocess.run(cmd, text=True, capture_output=True, check=True, **kw)

def sha256(path):
    h=hashlib.sha256(); h.update(Path(path).read_bytes()); return h.hexdigest()

def extract_text(exe, out):
    run(["objcopy", "--dump-section", f".text={out}", str(exe)])

def dwarf_metrics(exe):
    info = run(["readelf", "--debug-dump=info", "--wide", str(exe)]).stdout
    dies=[]; current=None
    for line in info.splitlines():
        m=DIE_START.match(line)
        if m:
            if current: dies.append(current)
            current=[m.group(1), set()]
            continue
        if current:
            a=ATTR.search(line)
            if a: current[1].add(a.group(1))
    if current: dies.append(current)
    types={(tag, tuple(sorted(attrs))) for tag,attrs in dies}
    sections=run(["readelf","-SW",str(exe)]).stdout
    debug_bytes=0
    by_section={}
    for line in sections.splitlines():
        m=DEBUG_SEC.search(line)
        if m:
            size=int(m.group(2),16); by_section[m.group(1)]=size; debug_bytes += size
    return {"die_count":len(dies),"distinct_die_types":len(types),"debug_section_bytes":debug_bytes,"debug_sections":by_section}

def compiler_version(cc):
    p=run([cc,"--version"]).stdout.splitlines()
    return p[0] if p else cc

def compile_pair(cc,opt,src,work):
    nog=work/f"{cc}-{opt}-nog"; dbg=work/f"{cc}-{opt}-g"
    common=[cc,"-std=gnu11",f"-{opt}","-fno-ident",str(src)]
    run(common+["-o",str(nog)])
    run(common+["-g3","-o",str(dbg)])
    out_nog=run([str(nog)]).stdout
    out_dbg=run([str(dbg)]).stdout
    text_nog=work/f"{cc}-{opt}-nog.text"; text_dbg=work/f"{cc}-{opt}-g.text"
    extract_text(nog,text_nog); extract_text(dbg,text_dbg)
    return {
      "stdout_equal":out_nog==out_dbg,
      "stdout":out_dbg.strip(),
      "text_equal":Path(text_nog).read_bytes()==Path(text_dbg).read_bytes(),
      "text_sha256_nog":sha256(text_nog),"text_sha256_g":sha256(text_dbg),
      "text_bytes":text_dbg.stat().st_size,
      **dwarf_metrics(dbg)
    }

def main():
    compilers=[c for c in ("gcc","clang") if shutil.which(c)]
    missing=[x for x in ("objcopy","readelf") if not shutil.which(x)]
    if not compilers or missing:
        raise SystemExit(f"missing tools: compilers={compilers}, missing={missing}")
    data={"method":"fresh scoped CCMD probe; not official Dfusor artifact","compilers":{},"cases":[]}
    for cc in compilers: data["compilers"][cc]=compiler_version(cc)
    with tempfile.TemporaryDirectory(prefix="ccmd-") as td:
      work=Path(td)
      # Semantic equivalence is checked via the observable stdout of each fixture.
      outputs={}
      for name,code in FIXTURES.items():
        src=work/f"{name}.c"; src.write_text(code)
        for cc in compilers:
          for opt in ("O0","O2"):
            r=compile_pair(cc,opt,src,work)
            r.update({"fixture":name,"compiler":cc,"opt":opt})
            data["cases"].append(r)
            outputs.setdefault((cc,opt),set()).add(r["stdout"])
      data["semantic_equivalence"]={f"{cc}-{opt}":len(v)==1 for (cc,opt),v in outputs.items()}
    data["all_ccmd_pairs_pass"] = all(c["text_equal"] and c["stdout_equal"] for c in data["cases"])
    data["all_fixtures_semantically_equal"] = all(data["semantic_equivalence"].values())
    # Debug-information amplification: compare seed vs transformations, separately by compiler/opt.
    amps=[]
    for cc in compilers:
      for opt in ("O0","O2"):
        rows=[c for c in data["cases"] if c["compiler"]==cc and c["opt"]==opt]
        seed=next(c for c in rows if c["fixture"]=="seed")
        for c in rows:
          if c["fixture"]=="seed": continue
          amps.append({"compiler":cc,"opt":opt,"fixture":c["fixture"],
            "die_ratio": c["die_count"]/seed["die_count"] if seed["die_count"] else None,
            "distinct_type_ratio": c["distinct_die_types"]/seed["distinct_die_types"] if seed["distinct_die_types"] else None,
            "debug_bytes_ratio": c["debug_section_bytes"]/seed["debug_section_bytes"] if seed["debug_section_bytes"] else None})
    data["amplification_vs_seed"]=amps
    out=RESULTS/"summary.json"; out.write_text(json.dumps(data,indent=2)+"\n")
    # concise text report for CI logs
    print(json.dumps({
      "all_ccmd_pairs_pass":data["all_ccmd_pairs_pass"],
      "all_fixtures_semantically_equal":data["all_fixtures_semantically_equal"],
      "pairs":len(data["cases"]),
      "compilers":data["compilers"],
      "combined_amplification":[x for x in amps if x["fixture"]=="combined"]
    }, indent=2))
    if not data["all_ccmd_pairs_pass"] or not data["all_fixtures_semantically_equal"]:
      raise SystemExit(1)

if __name__=="__main__": main()
