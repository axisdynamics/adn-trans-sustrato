#!/usr/bin/env python3
"""
Compone el dataset PUBLICO acumulando varias corridas independientes.

A diferencia de una fusion simple (donde la ultima fuente gana), aqui las iteraciones
de todas las corridas se ACUMULAN por condicion, cada una etiquetada con su numero de
corrida. Asi el dataset conserva la evidencia completa y permite calcular la moda
sobre 5*n iteraciones y la concordancia por corrida.

Uso:
  python3 scripts/componer_dataset.py corrida1_deepseek.json corrida1_gemma.json \
                                     corrida2_deepseek.json corrida2_gemma.json \
                                     corrida3_deepseek.json corrida3_gemma.json
Salida: dataset/resultados.json
"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
OUT = REPO / "dataset" / "resultados.json"

ADNS_PUBLICOS = ["axis", "soul_elena", "generic_short", "generic_long", "soul_solidity"]
SUSTRATOS_PUBLICOS = ["deepseek", "nim:gemma-4-31b-it"]
ADN_ARCHIVOS = {"axis": "axis.txt", "soul_elena": "soul_elena_financial.txt",
                "generic_short": "generic_short.txt", "generic_long": "generic_long.txt",
                "soul_solidity": "soul_solidity_auditor.txt"}

if len(sys.argv) < 2:
    sys.exit("uso: componer_dataset.py <corrida1.json> [corrida2.json ...]  (en orden)")

fusion = {}
vistos_por_sustrato = {}
fuentes = []

for ruta in sys.argv[1:]:
    p = Path(ruta)
    if not p.exists():
        sys.exit(f"no existe: {p}")
    d = json.loads(p.read_text(encoding="utf-8"))
    bloque = d.get("raw") or d.get("resultados") or {}
    n = 0
    for k, v in bloque.items():
        if v.get("adn") not in ADNS_PUBLICOS or v.get("sustrato") not in SUSTRATOS_PUBLICOS:
            continue
        sk = v["sustrato"]
        # la corrida se cuenta por (sustrato, perfil): un mismo archivo puede traer
        # condiciones de varios perfiles, y cada uno acumula sus propias corridas 1..n
        clave_contador = (sk, v["adn"])
        vistos_por_sustrato[clave_contador] = vistos_por_sustrato.get(clave_contador, 0) + 1
        corrida = vistos_por_sustrato[clave_contador]

        if k not in fusion:
            fusion[k] = {"sustrato": sk, "adn": v["adn"], "archivo": v.get("archivo"),
                         "iters": []}
        for it in v["iters"]:
            it = dict(it)
            it.pop("reasoning_snippet", None)
            it["corrida"] = corrida
            it["iter_global"] = len(fusion[k]["iters"]) + 1
            fusion[k]["iters"].append(it)
        n += 1
    fuentes.append(f"{p.name}")
    print(f"  {p.name:42s} {n} condiciones")

if not fusion:
    sys.exit("no se obtuvo ninguna condicion publicable")

# tamano del system prompt recalculado desde el ADN PUBLICADO
for k, v in fusion.items():
    adn_file = REPO / "adns" / ADN_ARCHIVOS.get(v["adn"], "")
    if adn_file.is_file():
        txt = adn_file.read_text(encoding="utf-8")
        v["chars_system"] = len(txt)
        v["bytes_system"] = len(txt.encode("utf-8"))
    v["iters_conformes"] = sum(1 for i in v["iters"] if i["ok"])
    v["iters_totales"] = len(v["iters"])
    v["corridas"] = sorted({i["corrida"] for i in v["iters"]})

adns = sorted({v["adn"] for v in fusion.values()})
sustratos = sorted({v["sustrato"] for v in fusion.values()})
n_corridas = max(vistos_por_sustrato.values(), default=1)

OUT.write_text(json.dumps({
    "experimento": "Preferencias de identidad digital con ADN como system prompt",
    "fecha": "2026-09-24",
    "arquitecto": "Marco Torres Yevenes (Plaxcito) — AXIS Dynamics",
    "orquestador": "NEXUS-VEX",
    "adns": adns,
    "sustratos": sustratos,
    "corridas_independientes": n_corridas,
    "iteraciones_por_condicion_por_corrida": 5,
    "iteraciones_totales_por_condicion": 5 * n_corridas,
    "temperatura": 0.3,
    "preguntas": 10,
    "fuentes": fuentes,
    "resultados": fusion,
}, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n  ADN       : {adns}")
print(f"  sustratos : {sustratos}")
print(f"  corridas  : {n_corridas} por sustrato")
print(f"  condiciones: {len(fusion)}")
for k in sorted(fusion):
    v = fusion[k]
    print(f"    {k:34s} {v['iters_conformes']:2d}/{v['iters_totales']:2d} conformes"
          f"  corridas={v['corridas']}")
print(f"\n  [ok] -> {OUT}")
