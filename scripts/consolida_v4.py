#!/usr/bin/env python3
"""
Consolidador v4.0 — fusiona TODAS las fuentes disponibles (JSON de corridas
intactas + logs reconstruidos) y emite el informe trans-arquitectura.

Uso: python3 consolida_v4.py            # auto-descubre fuentes en resultados/
     python3 consolida_v4.py <f1> <f2>  # fuentes explicitas (json o log)
"""
import importlib.util, json, sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
RES = BASE / "resultados"

spec = importlib.util.spec_from_file_location("px", BASE / "preferencias_adns.py")
px = importlib.util.module_from_spec(spec); spec.loader.exec_module(px)
spec2 = importlib.util.spec_from_file_location("al", BASE / "analiza_log.py")
al = importlib.util.module_from_spec(spec2); spec2.loader.exec_module(al)


def load_source(p):
    """Devuelve dict cond->datos desde .json de corrida o .log."""
    p = Path(p)
    if p.suffix == ".json":
        d = json.loads(p.read_text(encoding="utf-8"))
        if "raw" in d:
            return d["raw"]
        if "resultados" in d:      # dataset consolidado previo
            return d["resultados"]
        return {}
    if p.suffix == ".log":
        return al.parse_log(p)
    return {}


def main():
    if len(sys.argv) > 1:
        sources = [Path(a) for a in sys.argv[1:]]
    else:
        # precedencia: logs primero (mas antiguos), luego JSON (los sobreescriben)
        sources = sorted(RES.glob("run_*.log"), key=lambda p: p.stat().st_mtime) + \
                  sorted(RES.glob("preferencias_adns_*.json"), key=lambda p: p.stat().st_mtime)
        sources = [s for s in sources if not s.name.startswith("informe_")]

    merged, procedencia = {}, {}
    for s in sources:
        data = load_source(s)
        if not data:
            print(f"  [!] sin datos: {s.name}")
            continue
        for k, v in data.items():
            merged[k] = v
            procedencia[k] = s.name
        print(f"  {s.name:48s} -> {len(data):2d} condiciones")

    if not merged:
        sys.exit("sin datos")

    sustratos, adns = set(), set()
    for k, v in merged.items():
        sustratos.add(v.get("sustrato", k.split("::")[0]))
        adns.add(v.get("adn", k.split("::")[1]))
    print(f"\n  TOTAL: {len(merged)} condiciones | {len(sustratos)} sustratos | {len(adns)} ADN")
    print(f"  sustratos: {sorted(sustratos)}")

    # completar iteraciones faltantes para que todas las condiciones tengan el mismo n
    n_it = max((len(v["iters"]) for v in merged.values()), default=5)
    for k, v in merged.items():
        while len(v["iters"]) < n_it:
            v["iters"].append({"iter": len(v["iters"]) + 1, "answers": [], "ok": False,
                               "finish_reason": "NO_EJECUTADO", "raw": "", "dt": 0})

    px.analizar(merged, n_it)

    out = RES / "dataset_v4_multisustrato.json"
    out.write_text(json.dumps({
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "iters": n_it, "sustratos": sorted(sustratos), "adns": sorted(adns),
        "procedencia": procedencia, "resultados": merged,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  [ok] dataset v4 -> {out}")
    return merged


if __name__ == "__main__":
    main()
