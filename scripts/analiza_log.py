#!/usr/bin/env python3
"""
Reconstruye el analisis de una corrida de preferencias_adns.py a partir del LOG
(las tablas de moda ya se perdieron una vez por un crash posterior al calculo).
Uso: python3 analiza_log.py resultados/run_deepseek_*.log
"""
import importlib.util, json, re, sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("px", BASE / "preferencias_adns.py")
px = importlib.util.module_from_spec(spec); spec.loader.exec_module(px)


def parse_log(path):
    res, cur = {}, None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        m = re.match(r'^>>>\s+(\S+)\s*/\s*(\S+)\s+\(system (\d+)B,\s*(\d+) iters\)', line)
        if m:
            sk, ak = m.group(1), m.group(2)
            cur = f"{sk}::{ak}"
            res[cur] = {"sustrato": sk, "adn": ak, "bytes_system": int(m.group(3)), "iters": []}
            continue
        m = re.match(r'^\s+it(\d+):\s*(\S+?)\s+\[(\w+)\]', line)
        if m and cur:
            letters = m.group(2)
            answers = [c for c in letters if c in "abcd"]
            res[cur]["iters"].append({"iter": int(m.group(1)), "answers": answers,
                                      "ok": len(answers) >= 10,
                                      "finish_reason": m.group(3), "raw": "", "dt": 0})
    return res


if __name__ == "__main__":
    log = sys.argv[1] if len(sys.argv) > 1 else sorted((BASE / "resultados").glob("run_deepseek_*.log"))[-1]
    res = parse_log(log)
    iters = max(len(v["iters"]) for v in res.values()) if res else 5

    print("=" * 78)
    print("  INFORME V3.0 — ADNs como system prompt (reconstruido de log)")
    print(f"  log: {log}")
    print(f"  condiciones: {len(res)}  |  iteraciones: {iters}")
    print("=" * 78)

    # --- Conformidad al contrato de formato (metrica nueva de v3.0)
    print("\nTABLA 0 — CONFORMIDAD al contrato (iteraciones con 10 letras validas)")
    adns = sorted({v["adn"] for v in res.values()})
    susts = sorted({v["sustrato"] for v in res.values()})
    print(f"  {'ADN':<18}" + "".join(f"{s:>15}" for s in susts) + f"{'global':>12}")
    for ak in adns:
        row = f"  {ak:<18}"; g_ok = g_tot = 0
        for sk in susts:
            d = res.get(f"{sk}::{ak}")
            if not d:
                row += f"{'-':>15}"; continue
            ok = sum(1 for i in d["iters"] if i["ok"]); tot = len(d["iters"])
            g_ok += ok; g_tot += tot
            row += f"{ok}/{tot} ({ok*100//max(tot,1)}%)".rjust(15)
        row += f"{g_ok}/{g_tot} ({g_ok*100//max(g_tot,1)}%)".rjust(12)
        print(row)

    px.analizar(res, iters)

    OUT = BASE / "resultados" / f"informe_v3_{Path(log).stem.replace('run_','')}.json"
    OUT.write_text(json.dumps({
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "log_origen": str(log), "iters": iters, "raw": res,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  [ok] reconstruido -> {OUT}")
