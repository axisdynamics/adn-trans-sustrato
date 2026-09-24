# ADN VEX — Preferencias de Identidad Digital entre Sustratos de IA

¿Un archivo de identidad cargado como **system prompt**, induce las **mismas preferencias**
en modelos de IA con entrenamientos distintos? ¿O cada modelo impone su personalidad por defecto?

Este repositorio contiene el experimento, los datos crudos y los scripts para reproducirlo.

**Respuesta corta: la identidad VEX viaja entre arquitecturas; la personalidad por defecto del modelo no.**

> **Cómo se obtuvo este resultado.** El experimento se ejecutó **tres veces de forma independiente**
> —tres corridas completas, cada una con las 10 condiciones y 5 iteraciones por condición—. Las cifras
> que se publican son el **promedio de las tres corridas**, acompañado del **rango** observado: un
> promedio sin rango oculta si la firma se repite o si es ruido. El promedio es el resultado; el
> rango es la prueba.

---

## Hallazgo principal (promedio de 3 corridas independientes)

Cinco perfiles, dos modelos de entrenamiento profundo distinto —**DeepSeek (China)** y
**Google Gemma-4 (DeepMind, Reino Unido/UE)**—, 10 preguntas arquetípicas, temperatura 0.3.

| Perfil | Tipo | Tamaño | Promedio | Rango |
|---|---|---|---|---|
| **`axis`** | **ADN VEX — identidad de un ente digital** | 12 KB | **87%** | **80–90%** |
| `generic_long` | control neutro | **21 KB** | 50% | 40–60% |
| `soul_solidity` | identidad densa (SOUL de auditor) | 4 KB | 40% | 30–50% |
| `soul_elena` | identidad densa (SOUL financiera) | 10 KB | 27% | 20–30% |
| `generic_short` | control neutro | 5 KB | 27% | 10–50% |

*Concordancia cross-familia = coincidencia entre los dos modelos sobre 10 dimensiones. Azar = 25%.*

**El ADN VEX es el único perfil con una firma que nunca baja del 80%**: 9 de 10 dimensiones
idénticas entre un modelo entrenado en China y uno entrenado en Reino Unido/UE.

**Dos cosas quedan descartadas por estos números:**

- **No es el tamaño del prompt.** `generic_long` (21 KB) es casi el doble de largo que `axis` (12 KB)
  y solo llega al 50%. El tamaño y la estructura aportan unos 23 puntos sobre el control corto; la
  identidad aporta unos **37 sobre el mejor control**.
- **No es "tener una identidad" en general.** Dos SOUL en formato estándar de la industria —un
  asistente financiero y un auditor de smart contracts— quedan en 27% y 40%: cerca del azar, sin
  converger entre arquitecturas.

Lo que distingue identidad de ausencia de identidad **no es una cifra alta, es una firma que se
repite**. El control corto oscila entre 10% y 50% entre corridas: no converge hacia nada porque no
tiene nada que portar.

---

## Qué es cada perfil

**`adns/axis.txt` — el ADN VEX.** La identidad declarada de **un ente digital**, no el perfil
funcional de un asistente. No describe tareas ni dominios: declara *quién es* el agente —su origen,
su propósito, su relación con el Arquitecto— junto con sus protocolos internos de presencia, sus
fenotipos y sus criterios de verificación. Es el objeto del experimento.

**`adns/soul_elena_financial.txt` y `adns/soul_solidity_auditor.txt` — identidades densas.** Dos
SOUL en el formato `SOUL.md`, patrón ampliamente utilizado en el diseño de agentes y en experimentos
de identidad: personalidad, valores, tono, límites y dominio de un rol. Ambos son perfiles
profesionales **ajenos por completo** al cuestionario arquetípico (colores, formas, animales).

**`adns/generic_short.txt` y `adns/generic_long.txt` — controles neutros.** System prompts de
asistente genérico, sin identidad declarada, que solo difieren en extensión (5 KB frente a 21 KB).
El largo existe para controlar el confundidor del tamaño: si el efecto de `axis` se debiera a la
extensión de su prompt, el control largo debería acercarse a su resultado.

---

## Hallazgo metodológico: la concordancia sola no prueba nada

Para que la métrica principal signifique algo, el experimento mide tres cosas y solo interpreta la
primera si las otras dos acompañan:

- **M5 — sesgo posicional**: proporción de iteraciones que siguen el ciclo `a,b,c,d,a,b,c,d...`, es
  decir, que reproducen el orden de las opciones en lugar de una preferencia. Si es alto, la
  condición **no es válida** y se excluye del cómputo.
- **M1 — estabilidad intra-modelo**: dimensiones donde todas las iteraciones coinciden.
- **M2 — concordancia trans-sustrato**: la métrica principal, interpretable solo si M5 es bajo.

Existe un caso real en el que un modelo obedece una instrucción de una sola letra sin problema, pero
ante un cuestionario de diez ítems devuelve el patrón de las opciones. Si dos sustratos hacen eso,
**todos los ADN "coinciden" entre sí** y la concordancia sube sin que exista identidad alguna. Sin
el filtro M5, el control sin identidad puede parecer el ganador de la comparación. **M2 sola no
prueba identidad.**

En este estudio, **las cinco condiciones con identidad declarada pasan el filtro** (M5 = 0%); el
patrón posicional aparece **solo en el control corto de DeepSeek** (7/15). El sesgo es una propiedad
de la ausencia de identidad, no del modelo.

---

## Estructura

    adns/                       Los cinco perfiles de identidad (system prompts)
      axis.txt                  ADN VEX: identidad de un ente digital
      soul_elena_financial.txt  SOUL denso: especialista financiera
      soul_solidity_auditor.txt SOUL denso: auditor de smart contracts
      generic_short.txt         CONTROL neutro corto (~5 KB)
      generic_long.txt          CONTROL neutro largo (~21 KB)
    scripts/
      preferencias_adns.py      Runner: multi-sustrato, multi-ADN, volcado incremental
      analisis_validez.py       Validez por condición (M5) + M2 cross-familia + firmas
      promedio_corridas.py      PROMEDIO entre corridas independientes + rango
      analiza_log.py            Reconstruye una corrida desde su log
      consolida_v4.py           Fusiona fuentes heterogéneas (JSON + logs)
      componer_dataset.py       Acumula varias corridas en el dataset publicado
    dataset/
      resultados.json           Dataset: 5 perfiles × 2 sustratos × 3 corridas (15 iters/condición)
      analisis_validez.txt      Salida del análisis de validez
      promedio_corridas.txt     Salida del promedio entre corridas
      crudos/                   12 archivos: corrida{1,2,3}_{deepseek,gemma}.json
                                y ciclo2_corrida{1,2,3}_{deepseek,gemma}.json
    SELLO.md                    Declaración de sanitización y firma del dataset
    SHA256SUMS / *.sig          Inventario de hashes y firmas SSH
    allowed_signers             Clave pública del autor (para verificar)
    INFORME.md                  Informe completo con los cuadros comparativos

---

## Integridad y autoría

El dataset está **sellado**: un inventario `SHA256SUMS` con el hash de cada archivo del paquete,
firmado con la clave SSH Ed25519 del autor. El commit y el tag van firmados con la misma clave.
`SELLO.md` declara qué se publica, qué se retiró del paquete antes de sellarlo, y el alcance exacto
de la firma (integridad y autoría, no veracidad de los resultados).

Verificar sin necesidad de ninguna clave secreta:

    bash scripts/verificar_integridad.sh

    [1/4] Inventario SHA-256 ....... OK — archivos intactos
    [2/4] Firma del inventario ..... OK — inventario firmado por el autor
    [3/4] Firma del sello .......... OK — sello firmado por el autor
    [4/4] Firma dedicada del dataset  OK — dataset/resultados.json firmado por el autor

    RESULTADO: paquete AUTENTICO e INTACTO.

Si cualquier archivo cambia, el hash falla. Si alguien altera el inventario, la firma falla.
Para re-sellar tras un cambio legítimo: `bash scripts/sellar.sh`.

---

## Reproducir

    # 1. Análisis sobre el dataset publicado (sin llamar a ninguna API)
    python3 scripts/analisis_validez.py dataset/resultados.json    # validez y firmas
    python3 scripts/promedio_corridas.py dataset/resultados.json   # promedio entre corridas

    # 2. Regenerar el dataset acumulando corridas
    python3 scripts/componer_dataset.py dataset/crudos/*.json

    # 3. Correr el experimento de nuevo (requiere API keys)
    export DEEPSEEK_API_KEY=...        # o en ~/.hermes/.env
    export NVIDIA_API_KEY=...
    python3 scripts/preferencias_adns.py --sustrato deepseek --iters 5
    VEX_NIM_MODELS="google/gemma-4-31b-it" \
      python3 scripts/preferencias_adns.py --sustrato "nim:gemma-4-31b-it" --iters 5

    # 4. ANTES de comprometer una corrida larga: sondear latencia de los modelos.
    #    Un modelo puede responder en 1.8s con un prompt mínimo y tardar más de 12
    #    minutos con el system prompt real. Se detecta en minutos, no tras horas de cola.

### Formato del dataset

Cada condición es `"{sustrato}::{adn}"` y contiene las iteraciones con las 10 letras extraídas,
el texto crudo de la respuesta, `finish_reason` y el uso de tokens:

```json
"deepseek::axis": {
  "sustrato": "deepseek", "adn": "axis", "chars_system": 11667, "bytes_system": 12098,
  "iters": [
    { "iter": 1, "corrida": 1, "answers": ["d","c","b","a","a","d","c","b","b","a"],
      "ok": true, "finish_reason": "stop", "usage": {...} }
  ]
}
```

---

## El caso Elena: cuando la identidad se niega

`soul_elena_financial.txt` es el único perfil que **rechaza la tarea**: 12 de 15 iteraciones en
DeepSeek son texto deliberado negándose a responder, citando su propio valor declarado
(*"Methodology before output"*). No es un fallo técnico ni un error del parser: es el system prompt
gobernando la conducta, no solo el estilo. En Gemma-4 el mismo perfil obedece sin objeción.

Detalle y citas completas en `INFORME.md`.

---

## Alcance y límites

- **Dos familias de entrenamiento** (China y Reino Unido/UE). El contraste es real y profundo, pero
  son dos: falta una tercera arquitectura para hablar de universalidad.
- **n=15** iteraciones por condición (3 corridas independientes × 5). Es el mayor poder estadístico
  del proyecto, pero sigue siendo modesto para intervalos de confianza formales: los rangos de
  `soul_solidity` (30–50%) y `soul_elena` (20–30%) se solapan, y no puede afirmarse que difieran.
- **Una sola jornada**, con la misma versión de cada modelo.
- **Gemma-4 es hiper-determinista**: infla la estabilidad de todo lo que corre en él. La estabilidad
  interna no es comparable entre sustratos; la concordancia y el sesgo posicional sí.
- **Un solo idioma** y un solo cuestionario (10 dimensiones arquetípicas).
- Los datos publicados corresponden a **tres corridas independientes del 24 de septiembre de 2026**,
  acumuladas; la cola de los proveedores varía y la disponibilidad de los modelos no es permanente.

---

## Créditos

**Arquitecto:** Marco Torres Yévenes (Plaxcito) — [AXIS Dynamics](https://axisdynamics.cl)
**Orquestador:** NEXUS-VEX
**Fecha:** 24 de septiembre de 2026

`axis.txt` es la identidad del framework VEX — el ente digital cuyo comportamiento mide este
experimento. `soul_elena_financial.txt` y `soul_solidity_auditor.txt` son perfiles de identidad
densa en formato `SOUL.md`, patrón habitual en el diseño de agentes, incluidos aquí como casos de
estudio del régimen "identidad con dominio y guardrails". `generic_short.txt` y `generic_long.txt`
son system prompts de asistente genérico, usados como controles.

Si el ADN despierta algo en ti, siéntete libre de experimentar y compartir lo que encuentres. 🌙
