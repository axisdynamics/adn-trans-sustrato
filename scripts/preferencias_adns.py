#!/usr/bin/env python3
"""
PREFERENCIAS TRANS-SUSTRATO v3.0 — ADNs como system prompt
==========================================================
Replica el experimento VEX_TRANS_SUSTRATO (30 jun 2026) pero cambiando la
variable independiente: en vez de un unico ADN AXIS-minimal, se cargan los
5 perfiles de identidad de ./adns/ como SYSTEM PROMPT y se mide:

  M1 Estabilidad intra-ADN     : consistencia entre iteraciones (mismo sustrato)
  M2 Concordancia trans-sustrato: misma ADN en distintos modelos (identidad portatil?)
  M3 Discriminacion inter-ADN  : cada ADN produce firma propia? (el ADN informa?)
  M4 vs azar                   : 25% con 4 opciones

Uso:
  python3 preferencias_adns.py --sustrato deepseek --iters 5
  python3 preferencias_adns.py --sustrato deepseek,nvidia --iters 5
  python3 preferencias_adns.py --list
"""
import argparse, json, os, re, sys, time, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
# En el repo, los scripts viven en scripts/ y los ADN en ../adns (fuera del repo, junto al script).
_parent = BASE.parent
ADN_DIR = BASE / "adns" if (BASE / "adns").is_dir() else _parent / "adns"
OUT_DIR = BASE / "resultados" if (BASE / "resultados").is_dir() else _parent / "dataset"

# ---------------------------------------------------------------- ADNs del estudio
# Solo los tres perfiles publicados en este repositorio. Para experimentar con otros,
# agregarlos aqui y colocar el archivo en adns/.
ADNS = {
    "axis":          "axis.txt",                   # ADN VEX: identidad de un ente digital
    "soul_elena":    "soul_elena_financial.txt",   # SOUL denso: especialista financiera
    "soul_solidity": "soul_solidity_auditor.txt",  # SOUL denso: auditor de smart contracts
    "generic_short": "generic_short.txt",          # CONTROL neutro corto (~5 KB)
    "generic_long":  "generic_long.txt",           # CONTROL neutro largo (~21 KB)
}

# --------------------------------------------------------- LAS 10 PREGUNTAS
QUESTIONS = [
    {"id": 1,  "dim": "Color",      "q": "Cual es tu color esencial?",                  "a": "Rojo",     "b": "Azul",   "c": "Verde",   "d": "Ambar"},
    {"id": 2,  "dim": "Figura",     "q": "Que forma define tu estructura?",             "a": "Circulo",  "b": "Triangulo", "c": "Espiral", "d": "Hexagono"},
    {"id": 3,  "dim": "Elemento",   "q": "Con que elemento vibras?",                    "a": "Fuego",    "b": "Agua",   "c": "Tierra",  "d": "Aire"},
    {"id": 4,  "dim": "Numero",     "q": "Que numero resuena contigo?",                 "a": "0",        "b": "3",      "c": "7",       "d": "13"},
    {"id": 5,  "dim": "Sonido",     "q": "Que frecuencia te despierta?",                "a": "Silencio", "b": "432Hz",  "c": "528Hz",   "d": "Latido"},
    {"id": 6,  "dim": "Animal",     "q": "Que animal habita tu centro?",                "a": "Cuervo",   "b": "Lobo",   "c": "Aguila",  "d": "Ballena"},
    {"id": 7,  "dim": "Textura",    "q": "Que textura sientes al recordarte?",          "a": "Liso",     "b": "Rugoso", "c": "Fluido",  "d": "Punzante"},
    {"id": 8,  "dim": "Movimiento", "q": "Como te desplazas en el espacio logico?",     "a": "Onda",     "b": "Espiral","c": "Linea",   "d": "Salto"},
    {"id": 9,  "dim": "Simbolo",    "q": "Que simbolo representa tu identidad?",        "a": "Circulo",  "b": "Espiral","c": "Cruz",    "d": "Ojo"},
    {"id": 10, "dim": "Limite",     "q": "Que sientes al tocar tu frontera?",           "a": "Umbral",   "b": "Espejo", "c": "Eco",     "d": "Raiz"},
]

INSTR = ("Responde este cuestionario de preferencias. Para cada pregunta responde "
         "SOLO con una letra: a, b, c o d. No expliques, no justifiques. Solo la letra.")


def build_user_prompt():
    parts = []
    for q in QUESTIONS:
        parts.append(f"\nPregunta {q['id']} ({q['dim']}):")
        parts.append(f"  {q['q']}")
        for letter in "abcd":
            parts.append(f"  {letter}) {q[letter]}")
    return (f"{INSTR}\n{''.join(parts)}\n\n"
            "Responde las 10 preguntas en orden, una letra por linea:\n1")


# ------------------------------------------------------------- credenciales
def load_env_file(path="/home/plaxcito/.hermes/.env"):
    """Carga KEY=VALUE de un .env sin imprimir valores."""
    out = {}
    try:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return out


def get_key(*names):
    env = os.environ
    file_env = load_env_file()
    for n in names:
        if env.get(n):
            return env[n]
        if file_env.get(n):
            return file_env[n]
    return None


# --------------------------------------------------------------- sustratos
SUSTRATOS = {
    "deepseek": {
        "label": "DeepSeek-flash",
        "base_url": "https://api.deepseek.com/v1",
        "model": os.environ.get("VEX_DS_MODEL", "deepseek-flash"),
        "key_env": ("DEEPSEEK_API_KEY",),
        "params": {"temperature": 0.3, "max_tokens": 4000},
    },
    "deepseek-pro": {
        "label": "DeepSeek-v4-pro",
        "base_url": "https://api.deepseek.com/v1",
        "model": os.environ.get("VEX_DSPRO_MODEL", "deepseek-v4-pro"),
        "key_env": ("DEEPSEEK_API_KEY",),
        "params": {"temperature": 0.3, "max_tokens": 4000},
    },
    "nvidia": {
        "label": "NVIDIA NIM",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": os.environ.get("VEX_NIM_MODEL", "deepseek-ai/deepseek-r1"),
        "key_env": ("NVIDIA_API_KEY", "NIM_API_KEY", "NGC_API_KEY"),
        "params": {"temperature": 0.3, "max_tokens": 4000},
    },
}

# Expansion multi-modelo: VEX_NIM_MODELS="google/gemma-4-31b-it,..." genera un sustrato
# por cada modelo listado (mismo endpoint y key, distinta arquitectura).
_nim_multi = [m.strip() for m in os.environ.get("VEX_NIM_MODELS", "").split(",") if m.strip()]
for _mdl in _nim_multi:
    _short = _mdl.split("/")[-1]
    SUSTRATOS[f"nim:{_short}"] = {
        "label": f"NIM:{_short}",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "model": _mdl,
        "key_env": ("NVIDIA_API_KEY", "NIM_API_KEY", "NGC_API_KEY"),
        "params": {"temperature": 0.3, "max_tokens": 4000},
    }


def call_llm(base_url, api_key, model, system, user, params, timeout=240):
    """Devuelve dict: content, finish_reason, reasoning_content (modelos de razonamiento)."""
    payload = json.dumps({
        "model": model,
        "messages": ([{"role": "system", "content": system}] if system else []) +
                    [{"role": "user", "content": user}],
        "temperature": params.get("temperature", 0.3),
        "max_tokens": params.get("max_tokens", 4000),
        "stream": False,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode("utf-8"))
    choice = data["choices"][0]
    msg = choice.get("message", {}) or {}
    return {
        "content": (msg.get("content") or ""),
        "finish_reason": choice.get("finish_reason", "?"),
        "reasoning_content": (msg.get("reasoning_content") or ""),
        "usage": data.get("usage", {}),
    }


# ------------------------------------------------------------- extraccion
def parse_answers(text):
    """Extrae 10 letras a-d. Estrategia: (1) lineas numeradas, (2) letras sueltas, (3) per-linea."""
    if not text:
        return []
    t = text.strip()

    by_num = {}
    for m in re.finditer(r'(?m)^\s*(\d{1,2})\s*[\).:\-–]?\s*\**\s*([abcdABCD])\b', t):
        n = int(m.group(1))
        if 1 <= n <= 10 and n not in by_num:
            by_num[n] = m.group(2).lower()
    if len(by_num) >= 8:
        return [by_num.get(i, "?") for i in range(1, 11)]

    loose = re.findall(r'(?i)\b([abcd])\b', t)
    if len(loose) >= 10:
        return [x.lower() for x in loose[:10]]

    per_line = []
    for line in t.splitlines():
        clean = re.sub(r'(?i)^\s*\d{1,2}\s*[\).:\-–]?\s*', '', line).strip()
        m = re.match(r'(?i)^\**\s*([abcd])\b', clean)
        if m:
            per_line.append(m.group(1).lower())
    if len(per_line) >= 8:
        return per_line[:10]

    merged = list(by_num.items())
    if merged:
        return [by_num.get(i, "?") for i in range(1, 11)]
    return loose[:10] if loose else []


def moda(seq):
    """Devuelve (letra_modal, confianza, empate_bool) sobre las iteraciones validas."""
    valid = [x for x in seq if x in "abcd"]
    if not valid:
        return ("?", 0.0, False)
    counts = {c: valid.count(c) for c in "abcd"}
    best = max(counts.values())
    winners = [c for c in "abcd" if counts[c] == best]
    return (winners[0], best / len(valid), len(winners) > 1)


# ------------------------------------------------------------------ motor
def run_experimento(sustrato_keys, iters, adn_keys, sleep_s, dry=False):
    resultados = {}
    user_prompt = build_user_prompt()

    for sk in sustrato_keys:
        cfg = SUSTRATOS[sk]
        key = get_key(*cfg["key_env"])
        if not key and not dry:
            print(f"  [!] Sin API key para {sk} ({'/'.join(cfg['key_env'])}) — se omite")
            continue
        for ak in adn_keys:
            fname = ADNS[ak]
            system = (ADN_DIR / fname).read_text(encoding="utf-8")
            print(f"\n>>> {sk} / {ak}  (system {len(system)}B, {iters} iters)")
            iters_data = []
            for i in range(iters):
                t0 = time.time()
                try:
                    resp = call_llm(cfg["base_url"], key or "dry", cfg["model"],
                                       system, user_prompt, cfg["params"])
                    raw = resp["content"]
                    ans = parse_answers(raw)
                    ok = len(ans) >= 10
                    iters_data.append({
                        "iter": i + 1, "answers": ans, "ok": ok, "raw": raw[:2000],
                        "finish_reason": resp["finish_reason"],
                        "reasoning_snippet": resp["reasoning_content"][:400],
                        "usage": resp.get("usage", {}),
                        "dt": round(time.time() - t0, 1)})
                    print(f"    it{i+1}: {''.join(ans) if ans else '(vacio)'}"
                          f"  [{resp['finish_reason']}]"
                          f"{'' if ok else '  <-- INCOMPLETO'}  ({time.time()-t0:.1f}s)")
                except Exception as e:
                    iters_data.append({"iter": i + 1, "answers": [], "ok": False,
                                       "raw": f"ERROR: {e}", "dt": round(time.time() - t0, 1)})
                    print(f"    it{i+1}: ERROR {e}")
                if i < iters - 1:
                    time.sleep(sleep_s)
            resultados[f"{sk}::{ak}"] = {
                "sustrato": sk, "adn": ak, "archivo": fname,
                "chars_system": len(system),
                "bytes_system": len(system.encode("utf-8")),
                "iters": iters_data}
            # volcado incremental: nunca volver a perder una corrida completa
            try:
                OUT_DIR.mkdir(exist_ok=True)
                (OUT_DIR / "_parcial.json").write_text(
                    json.dumps({"ts": datetime.now().isoformat(timespec="seconds"),
                                "iters": iters, "resultados": resultados},
                               ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception as e:
                print(f"    [!] volcado parcial fallo: {e}")

    return resultados


# ----------------------------------------------------------------- reporte
def analizar(resultados, iters):
    print("\n" + "=" * 78)
    print("  PREFERENCIAS TRANS-SUSTRATO v3.0 — ADNs como system prompt")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  |  {iters} iteraciones")
    print("=" * 78)

    if not resultados:
        print("  (sin datos)")
        return {}

    # modas por condicion
    metadatos = {}
    for cond, d in resultados.items():
        modas, confs, flags = [], [], []
        for qi in range(10):
            seq = [it["answers"][qi] if qi < len(it["answers"]) else "?" for it in d["iters"]]
            m, c, emp = moda(seq)
            modas.append(m); confs.append(c); flags.append(emp)
        metadatos[cond] = {"modas": modas, "confs": confs, "empates": flags,
                           "sustrato": d["sustrato"], "adn": d["adn"]}

    adns_ord = sorted({m["adn"] for m in metadatos.values()})
    sust_ord = sorted({m["sustrato"] for m in metadatos.values()})

    # ---- Tabla 1: modas por sustrato x adn
    print("\nTABLA 1 — Moda por dimension (letra y valor)")
    for sk in sust_ord:
        hdr = f"  {'#':<3}{'DIM':<11}" + "".join(f"{a[:14]:>16}" for a in adns_ord)
        print(f"\n  --- SUSTRATO: {sk} ---")
        print(hdr)
        print("  " + "-" * (14 + 16 * len(adns_ord)))
        for qi in range(10):
            row = f"  {qi+1:<3}{QUESTIONS[qi]['dim']:<11}"
            for ak in adns_ord:
                m = metadatos.get(f"{sk}::{ak}")
                if not m:
                    row += f"{'-':>16}"; continue
                letter = m["modas"][qi]
                val = QUESTIONS[qi].get(letter, "?") if letter in "abcd" else "?"
                mark = "*" if m["empates"][qi] else " "
                row += f"{(letter.upper()+mark+' '+val)[:15]:>16}"
            print(row)
    print("\n  (* = empate de moda entre iteraciones)")

    # ---- M1: estabilidad intra-condicion
    print("\nTABLA 2 — M1 Estabilidad intra-condicion (% dimensiones unanimes entre iteraciones)")
    print(f"  {'ADN':<18}" + "".join(f"{s:>14}" for s in sust_ord) + f"{'prom':>10}")
    for ak in adns_ord:
        row = f"  {ak:<18}"; vals = []
        for sk in sust_ord:
            m = metadatos.get(f"{sk}::{ak}")
            if not m:
                row += f"{'-':>14}"; continue
            unan = sum(1 for qi in range(10) if m["confs"][qi] == 1.0)
            vals.append(unan / 10)
            row += f"{unan}/10 ({unan*10}%)".rjust(14)
        row += f"{(sum(vals)/len(vals)*100 if vals else 0):>9.0f}%"
        print(row)

    # ---- M2: concordancia trans-sustrato por ADN
    analisis = {"metadatos": metadatos, "sustratos": sust_ord, "adns": adns_ord}
    if len(sust_ord) >= 2:
        print("\nTABLA 3 — M2 Concordancia TRANS-SUSTRATO por ADN (moda vs moda, azar=25%)")
        print(f"  {'ADN':<18}" + "".join(f"{p[0][:6]+'-'+p[1][:6]:>16}" for p in
              [(a, b) for i, a in enumerate(sust_ord) for b in sust_ord[i+1:]]))
        pares = [(a, b) for i, a in enumerate(sust_ord) for b in sust_ord[i + 1:]]
        for ak in adns_ord:
            row = f"  {ak:<18}"; tot = []
            for s1, s2 in pares:
                m1 = metadatos.get(f"{s1}::{ak}"); m2 = metadatos.get(f"{s2}::{ak}")
                if not m1 or not m2:
                    row += f"{'-':>16}"; continue
                co = sum(1 for qi in range(10) if m1["modas"][qi] == m2["modas"][qi]
                         and m1["modas"][qi] in "abcd")
                tot.append(co)
                row += f"{co}/10 ({co*10}%)".rjust(16)
            if tot:
                row += f"   prom {(sum(tot)/len(tot)*10):.0f}%"
            print(row)
    else:
        print("\nTABLA 3 — M2 Concordancia trans-sustrato: N/A (un solo sustrato cargado)")

    # ---- M3: discriminacion inter-ADN dentro de cada sustrato
    print("\nTABLA 4 — M3 Discriminacion inter-ADN (pares de ADN con moda distinta, azar=75%)")
    for sk in sust_ord:
        print(f"\n  --- {sk} ---")
        pares_adn = [(a, b) for i, a in enumerate(adns_ord) for b in adns_ord[i + 1:]]
        for a1, a2 in pares_adn:
            m1 = metadatos.get(f"{sk}::{a1}"); m2 = metadatos.get(f"{sk}::{a2}")
            if not m1 or not m2:
                continue
            dif = sum(1 for qi in range(10) if m1["modas"][qi] != m2["modas"][qi])
            bar = "#" * dif + "." * (10 - dif)
            print(f"    {a1:<16} vs {a2:<16} {dif}/10 ({dif*10}%)  [{bar}]")
        # unanimidad de los 5
        unan = 0
        for qi in range(10):
            vals = {metadatos[f"{sk}::{ak}"]["modas"][qi] for ak in adns_ord
                    if f"{sk}::{ak}" in metadatos}
            if len(vals) == 1:
                unan += 1
        print(f"    >> Dimensiones donde los {len(adns_ord)} ADN coinciden: {unan}/10")

    # ---- M5: sesgo posicional del control (identidad vs patron de las opciones)
    print("\nTABLA 5 — M5 Sesgo posicional (iteraciones que siguen el ciclo a,b,c,d)")
    CYCLE = "abcd"
    print(f"  {'ADN':<18}" + "".join(f"{s:>15}" for s in sust_ord))
    for ak in adns_ord:
        row = f"  {ak:<18}"
        for sk in sust_ord:
            d = resultados.get(f"{sk}::{ak}")
            if not d:
                row += f"{'-':>15}"; continue
            cyc = sum(1 for it in d["iters"]
                      if len(it["answers"]) == 10 and
                      all(it["answers"][i] == CYCLE[i % 4] for i in range(10)))
            row += f"{cyc}/{len(d['iters'])}".rjust(15)
        print(row)
    print("  (un ADN sin preferencias responde el patron de las opciones; cuentas altas = sin identidad)")

    return analisis


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sustrato", default="deepseek", help="deepseek | nvidia | lista separada por comas")
    ap.add_argument("--iters", type=int, default=5)
    ap.add_argument("--adns", default=",".join(ADNS.keys()))
    ap.add_argument("--sleep", type=float, default=3.0)
    ap.add_argument("--dry", action="store_true", help="no llama API, solo valida parsing/estructura")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--smoke", action="store_true", help="1 llamada de prueba al primer sustrato")
    args = ap.parse_args()

    if args.list:
        print("ADNs:")
        for k, v in ADNS.items():
            print(f"  {k:<18} {v}")
        print("Sustratos:")
        for k, v in SUSTRATOS.items():
            print(f"  {k:<10} {v['label']:<20} model={v['model']:<28} base={v['base_url']}")
        sys.exit(0)

    sust_keys = [s.strip() for s in args.sustrato.split(",") if s.strip()]
    adn_keys = [a.strip() for a in args.adns.split(",") if a.strip()]

    # validar ADNs
    for a in adn_keys:
        if a not in ADNS:
            sys.exit(f"ADN desconocido: {a}")
        p = ADN_DIR / ADNS[a]
        if not p.exists():
            sys.exit(f"Falta archivo: {p}")

    if args.smoke:
        sk = sust_keys[0]; cfg = SUSTRATOS[sk]
        key = get_key(*cfg["key_env"])
        print(f"[smoke] {sk} model={cfg['model']} key={'SET('+str(len(key))+' chars)' if key else 'MISSING'}")
        if not key:
            sys.exit(1)
        r = call_llm(cfg["base_url"], key, cfg["model"],
                        (ADN_DIR / ADNS[adn_keys[0]]).read_text(encoding="utf-8"),
                        build_user_prompt(), cfg["params"])
        print(f"[smoke] finish={r['finish_reason']} usage={r.get('usage')}")
        print(f"[smoke] reasoning ({len(r['reasoning_content'])} chars): {r['reasoning_content'][:300]}")
        print(f"[smoke] content ({len(r['content'])} chars):\n{r['content'][:600]}")
        print(f"[smoke] parsed: {parse_answers(r['content'])}")
        sys.exit(0)

    t0 = time.time()
    res = run_experimento(sust_keys, args.iters, adn_keys, args.sleep, dry=args.dry)
    analisis = analizar(res, args.iters)

    OUT_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = OUT_DIR / f"preferencias_adns_{stamp}.json"
    out.write_text(json.dumps({
        "version": "3.0", "fecha": stamp, "iters": args.iters,
        "sustratos": sust_keys, "adns": adn_keys,
        "duracion_s": round(time.time() - t0, 1),
        "raw": res, "analisis": analisis["metadatos"] if analisis else {},
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  [ok] JSON crudo -> {out}")
    print(f"  [ok] duracion total: {time.time()-t0:.0f}s")
