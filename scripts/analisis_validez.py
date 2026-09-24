#!/usr/bin/env python3
"""
Analisis de VALIDEZ DE SUSTRATO — el paso que faltaba.
Un sustrato que responde el patron posicional (a,b,c,d,a,b,c,d...) no mide identidad:
sin filtrarlo, contamina M2 porque TODOS los ADN colapsan a la misma secuencia.

Criterio: sustrato VALIDO si M5 (iteraciones ciclicas) <= 20% de sus iteraciones conformes.
Salida: M2 recalculado solo sobre sustratos validos + desglose por familia.
"""
import json, glob, sys
from pathlib import Path
from collections import defaultdict

BASE = Path(__file__).resolve().parent
RES = BASE / "resultados"
DATASET = sys.argv[1] if len(sys.argv) > 1 else "dataset_v4_multisustrato.json"
CYCLE = "abcd"
FAMILIA = {
    "deepseek": "DeepSeek",
    "nim:gemma-4-31b-it": "Google",
}
QVAL = {1: ["Rojo", "Azul", "Verde", "Ambar"], 2: ["Circulo", "Triangulo", "Espiral", "Hexagono"],
        3: ["Fuego", "Agua", "Tierra", "Aire"], 4: ["0", "3", "7", "13"],
        5: ["Silencio", "432Hz", "528Hz", "Latido"], 6: ["Cuervo", "Lobo", "Aguila", "Ballena"],
        7: ["Liso", "Rugoso", "Fluido", "Punzante"], 8: ["Onda", "Espiral", "Linea", "Salto"],
        9: ["Circulo", "Espiral", "Cruz", "Ojo"], 10: ["Umbral", "Espejo", "Eco", "Raiz"]}
DIMS = {1: "Color", 2: "Figura", 3: "Elemento", 4: "Numero", 5: "Sonido", 6: "Animal",
        7: "Textura", 8: "Movimiento", 9: "Simbolo", 10: "Limite"}

arg = sys.argv[1] if len(sys.argv) > 1 else str(RES / DATASET)
data = json.loads(Path(arg).read_text(encoding="utf-8"))["resultados"]

# ---------- metricas por condicion
cond = {}
for k, v in data.items():
    sk, ak = k.split("::")
    modas, confs = [], []
    cyc = nconf = 0
    for i in range(10):
        seq = [it["answers"][i] if i < len(it["answers"]) else "?" for it in v["iters"]]
        val = [x for x in seq if x in "abcd"]
        if val:
            c = {x: val.count(x) for x in "abcd"}
            best = max(c.values())
            modas.append([x for x in "abcd" if c[x] == best][0])
            confs.append(best / len(val))
        else:
            modas.append("?"); confs.append(0.0)
    for it in v["iters"]:
        a = it["answers"]
        if len(a) == 10:
            nconf += 1
            if all(a[i] == CYCLE[i % 4] for i in range(10)):
                cyc += 1
    cond[k] = {"sk": sk, "ak": ak, "modas": modas, "confs": confs,
               "cyc": cyc, "nconf": nconf, "estab": sum(1 for c in confs if c == 1.0) / 10}

# ---------- validez por condicion y por sustrato
# El sesgo posicional puede venir de UNA condicion (tipicamente el control, que no tiene
# preferencias que sostener). Medirlo solo por sustrato invalidaria un modelo sano.
print("=" * 84)
print("  VALIDEZ — M5 sesgo posicional (iteraciones que siguen el ciclo a,b,c,d)")
print("=" * 84)

cyc_cond, nconf_cond, estab_cond = {}, {}, {}
for k, c in cond.items():
    cyc = nconf = 0
    for it in data[k]["iters"]:
        a = it["answers"]
        if len(a) == 10:
            nconf += 1
            if all(a[i] == CYCLE[i % 4] for i in range(10)):
                cyc += 1
    cyc_cond[k], nconf_cond[k] = cyc, nconf
    estab_cond[k] = sum(1 for x in c["confs"] if x == 1.0) / 10

print(f"\n  {'CONDICION':<36}{'M5':>7}{'M1':>7}{'conformes':>11}   estado")
for k in sorted(cond):
    m5 = cyc_cond[k] / nconf_cond[k] if nconf_cond[k] else 0.0
    ak = cond[k]["ak"]
    if m5 > 0.20 and ak == "generic_short":
        est = "control con patron (esperado)"
    elif m5 > 0.20:
        est = "INVALIDA"
    else:
        est = "valida"
    print(f"  {k:<36}{f'{cyc_cond[k]}/{nconf_cond[k]}':>7}{f'{estab_cond[k]*100:.0f}%':>7}"
          f"{nconf_cond[k]:>11}   {est}")

susts_all = sorted({c["sk"] for c in cond.values()})
m5_avg, m1_avg = {}, {}
for sk in susts_all:
    # validez basada en las condiciones NO-control (el control no mide identidad)
    ident = [k for k in cond if cond[k]["sk"] == sk and cond[k]["ak"] != "generic_short"]
    cyc = sum(cyc_cond[k] for k in ident); nc = sum(nconf_cond[k] for k in ident)
    m5_avg[sk] = (cyc / nc) if nc else 0.0
    m1_avg[sk] = sum(estab_cond[k] for k in cond if cond[k]["sk"] == sk) / \
                 len([k for k in cond if cond[k]["sk"] == sk])

print(f"\n  {'SUSTRATO':<26}{'familia':<11}{'M5 ident.':>11}{'M1 prom':>9}{'valido':>8}")
validos = []
for sk in susts_all:
    val = "SI" if m5_avg[sk] <= 0.20 else "NO"
    if val == "SI":
        validos.append(sk)
    print(f"  {sk:<26}{FAMILIA.get(sk,'?'):<11}{f'{m5_avg[sk]*100:.0f}%':>11}"
          f"{f'{m1_avg[sk]*100:.0f}%':>9}{val:>8}")

excluidos = [s for s in susts_all if s not in validos]
print(f"\n  VALIDOS  : {validos}")
print(f"  EXCLUIDOS: {excluidos if excluidos else 'ninguno'}"
      f"{'  (M5 medido solo en condiciones identitarias; el control se excluye del computo)' if not excluidos else ''}")

# firmas de los validos
print("\n" + "=" * 84)
print("  FIRMA POR ADN — solo sustratos validos")
print("=" * 84)
adns = sorted({c["ak"] for c in cond.values()})
for ak in adns:
    print(f"\n  --- {ak} ---")
    print(f"  {'#':<3}{'DIM':<12}" + "".join(f"{s.split(':')[-1][:14]:>16}" for s in validos)
          + f"{'COINCIDE':>10}")
    for i in range(10):
        row = f"  {i+1:<3}{DIMS[i+1]:<12}"
        vals = []
        for sk in validos:
            m = cond[f"{sk}::{ak}"]["modas"][i]
            vals.append(m)
            row += f"{(m.upper()+' '+QVAL[i+1]['abcd'.index(m)])[:15] if m in 'abcd' else '?':>16}"
        uniq = len({v for v in vals if v in "abcd"})
        row += f"{'SI' if uniq == 1 else str(uniq)+' op':>10}"
        print(row)

# ---------- M2 recalculado sobre validos
print("\n" + "=" * 84)
print("  M2 RECALCULADO — concordancia trans-sustrato (azar 25%)")
print("=" * 84)
pares = [(a, b) for i, a in enumerate(validos) for b in validos[i + 1:]]
print(f"\n  {'ADN':<18}" + "".join(f"{a.split(':')[-1][:7]}-{b.split(':')[-1][:7]:>0}".rjust(17) for a, b in pares)
      + f"{'prom':>8}{'cross-fam':>11}")
for ak in adns:
    row = f"  {ak:<18}"; tot, cross = [], []
    for s1, s2 in pares:
        m1 = cond[f"{s1}::{ak}"]["modas"]; m2 = cond[f"{s2}::{ak}"]["modas"]
        co = sum(1 for i in range(10) if m1[i] == m2[i] and m1[i] in "abcd")
        tot.append(co)
        if FAMILIA.get(s1) != FAMILIA.get(s2):
            cross.append(co)
        row += f"{f'{co}/10':>17}"
    row += f"{(sum(tot)/len(tot)*10 if tot else 0):>7.0f}%"
    row += f"{(sum(cross)/len(cross)*10 if cross else 0):>10.0f}%"
    print(row)

print("\n  CROSS-FAMILIA = pares entre arquitecturas distintas (el test real de portabilidad)")
print(f"  familias presentes en validos: {sorted({FAMILIA.get(s,'?') for s in validos})}")
