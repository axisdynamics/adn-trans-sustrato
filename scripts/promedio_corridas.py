#!/usr/bin/env python3
"""
Analisis de PROMEDIO entre corridas independientes.

Sobre un dataset con varias corridas acumuladas calcula, para cada ADN:
  - la concordancia cross-familia de CADA corrida por separado
  - el PROMEDIO de las corridas (estimacion central)
  - el RANGO observado (dispersion entre corridas)
y contrasta con el azar (25%).

Uso: python3 scripts/promedio_corridas.py dataset/resultados.json
"""
import json, sys
from pathlib import Path

AZAR = 0.25
FAMILIA = {"deepseek": "DeepSeek", "nim:gemma-4-31b-it": "Google"}
DIMS = {1: "Color", 2: "Figura", 3: "Elemento", 4: "Numero", 5: "Sonido",
        6: "Animal", 7: "Textura", 8: "Movimiento", 9: "Simbolo", 10: "Limite"}

ruta = Path(sys.argv[1] if len(sys.argv) > 1 else "dataset/resultados.json")
data = json.loads(ruta.read_text(encoding="utf-8"))
res = data["resultados"]
corridas = sorted({it["corrida"] for v in res.values() for it in v["iters"]})
sustratos = sorted({v["sustrato"] for v in res.values()})
adns = sorted({v["adn"] for v in res.values()})


def moda(seq):
    v = [x for x in seq if x in "abcd"]
    if not v:
        return "?"
    c = {x: v.count(x) for x in "abcd"}
    b = max(c.values())
    return [x for x in "abcd" if c[x] == b][0]


def modas_de(cond, corrida=None, dim=None):
    """Modas por dimension, filtrando opcionalmente por corrida."""
    out = []
    for i in range(10):
        seq = []
        for it in cond["iters"]:
            if corrida is not None and it["corrida"] != corrida:
                continue
            if i < len(it["answers"]):
                seq.append(it["answers"][i])
        out.append(moda(seq))
    return out


print("=" * 78)
print("  PROMEDIO ENTRE CORRIDAS INDEPENDIENTES")
print(f"  fuente: {ruta.name}  |  corridas: {corridas}  |  azar = 25%")
print("=" * 78)

# --- M2 por corrida y promedio, por ADN
print(f"\n  M2 CONCORDANCIA CROSS-FAMILIA (azar 25%)")
print(f"  {'ADN':<17}" + "".join(f"{'corrida '+str(c):>12}" for c in corridas)
      + f"{'PROMEDIO':>11}{'rango':>10}")
resumen = {}
for ak in adns:
    fila, vals = [], []
    for c in corridas:
        m1 = modas_de(res[f"{sustratos[0]}::{ak}"], corrida=c)
        m2 = modas_de(res[f"{sustratos[1]}::{ak}"], corrida=c)
        co = sum(1 for i in range(10) if m1[i] == m2[i] and m1[i] in "abcd")
        vals.append(co / 10)
        fila.append(f"{co}/10 ({co*10}%)")
    prom = sum(vals) / len(vals)
    resumen[ak] = {"por_corrida": vals, "promedio": prom}
    print(f"  {ak:<17}" + "".join(f"{x:>12}" for x in fila)
          + f"{prom*100:>10.0f}%{f'{min(vals)*100:.0f}-{max(vals)*100:.0f}%':>10}")

# --- M5 y M1 POR CONDICION (el sesgo posicional puede venir de un solo ADN)
print(f"\n  VALIDEZ POR CONDICION (M5 = iteraciones que siguen el ciclo a,b,c,d)")
print(f"  {'CONDICION':<36}{'M5':>6}{'M1':>7}{'conformes':>11}")
condiciones_invalidas = []
for sk in sustratos:
    for ak in adns:
        cond = res[f"{sk}::{ak}"]
        cyc = nconf = 0
        unan = 0
        for it in cond["iters"]:
            a = it["answers"]
            if len(a) == 10:
                nconf += 1
                if all(a[i] == "abcd"[i % 4] for i in range(10)):
                    cyc += 1
        for i in range(10):
            seq = [it["answers"][i] for it in cond["iters"] if i < len(it["answers"])]
            if seq and len(set(seq)) == 1:
                unan += 1
        m5 = cyc / nconf if nconf else 0.0
        flag = ""
        if m5 > 0.20 and ak == "generic_short":
            flag = "  <- control: sin identidad, cae al patron"
        elif m5 > 0.20:
            flag = "  <- INVALIDA"; condiciones_invalidas.append(f"{sk}::{ak}")
        print(f"  {sk+'::'+ak:<36}{f'{cyc}/{nconf}':>6}{f'{unan*10}%':>7}{nconf:>11}{flag}")

print(f"\n  Validez agregada por sustrato (referencia):")
for sk in sustratos:
    cyc = nconf = 0
    for ak in adns:
        for it in res[f"{sk}::{ak}"]["iters"]:
            a = it["answers"]
            if len(a) == 10:
                nconf += 1
                if all(a[i] == "abcd"[i % 4] for i in range(10)):
                    cyc += 1
    print(f"    {sk:<26}{cyc}/{nconf} ({cyc*100//max(nconf,1)}%)")

if condiciones_invalidas:
    print(f"\n  ! Condiciones excluidas por sesgo posicional: {condiciones_invalidas}")
else:
    print(f"\n  Ninguna condicion identitaria exhibe sesgo posicional: el patron aparece")
    print(f"  unicamente en el control (que no tiene preferencias que sostener).")

# --- moda global (todas las iteraciones) por ADN
print(f"\n  FIRMA CONSOLIDADA (moda sobre {len(corridas)*5} iteraciones por condicion)")
for ak in adns:
    m1 = modas_de(res[f"{sustratos[0]}::{ak}"])
    m2 = modas_de(res[f"{sustratos[1]}::{ak}"])
    co = sum(1 for i in range(10) if m1[i] == m2[i] and m1[i] in "abcd")
    print(f"\n  --- {ak} ---  coincidencias entre familias: {co}/10")
    print(f"  {'#':<3}{'DIM':<12}{sustratos[0]:>14}{sustratos[1]:>22}{'':>4}")
    for i in range(10):
        mark = "  =" if m1[i] == m2[i] else "  x"
        print(f"  {i+1:<3}{DIMS[i+1]:<12}{m1[i].upper():>14}{m2[i].upper():>22}{mark}")

print(f"\n  AZAR = 25%. Un promedio claramente por encima del azar, sostenido en las")
print(f"  {len(corridas)} corridas, indica firma portatil; un promedio con rango amplio indica ruido.")
