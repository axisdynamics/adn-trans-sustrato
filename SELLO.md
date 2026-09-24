# SELLO DEL DATASET

**Autor:** Marco Torres Yévenes (Plaxcito) — AXIS Dynamics
**Orquestador:** NEXUS-VEX
**Fecha de sellado:** 24 de septiembre de 2026
**Método de firma:** SSH Ed25519 (`ssh-keygen -Y sign`), namespace `adn-dataset`

---

## 1. Qué certifica este sello

Quien verifique este paquete obtiene dos garantías:

1. **Integridad** — ningún archivo del paquete fue modificado después del sellado.
   Se comprueba contra el inventario `SHA256SUMS`.
2. **Autoría** — el inventario y esta declaración fueron firmados con la clave SSH privada del
   autor. La clave pública con la que se verifica está en `allowed_signers`.

Si un archivo cambia, el hash falla. Si alguien altera el inventario, la firma falla.

---

## 2. Cómo verificar

Sin necesidad de ninguna clave secreta — solo la clave pública del autor:

    bash scripts/verificar_integridad.sh

Verificación manual, punto por punto:

    sha256sum -c SHA256SUMS --quiet                      # integridad
    ssh-keygen -Y verify -f allowed_signers -I mtorres@exis.cl \
      -n adn-dataset -s SHA256SUMS.sig < SHA256SUMS      # autoría del inventario
    ssh-keygen -Y verify -f allowed_signers -I mtorres@exis.cl \
      -n adn-dataset -s SELLO.md.sig < SELLO.md          # autoría de este sello
    ssh-keygen -Y verify -f allowed_signers -I mtorres@exis.cl \
      -n adn-dataset -s dataset/resultados.json.sig < dataset/resultados.json

Salida esperada: `Good "adn-dataset" signature for mtorres@exis.cl`.

El commit y el tag de este paquete están firmados además con la misma clave
(`git log --show-signature`, `git tag -v v1.0.0`).

---

## 3. Declaración de sanitización

El dataset publicado es una **selección curada**, no el registro completo del trabajo
experimental. Antes del sellado se retiró del paquete todo material que no forma parte de
este estudio:

- **Perfiles de identidad no publicados.** El paquete contiene únicamente los tres perfiles
  declarados en `README.md` (`axis`, `soul_elena`, `generic_short`).
- **Sustratos no publicados.** Solo los dos modelos declarados (`deepseek-flash`,
  `google/gemma-4-31b-it`).

El barrido de verificación cubrió la totalidad de los archivos del paquete —dataset, corridas
crudas, scripts, README e informe—, no solo el dataset. Ningún archivo publicado conserva
referencia a material retirado.

El archivo interno del proyecto conserva el material completo. La sanitización de este paquete
**no altera ningún dato de las condiciones publicadas**: las respuestas, las iteraciones y los
cómputos del análisis corresponden exactamente a lo ejecutado.

---

## 4. Inventario

El inventario completo con el hash SHA-256 de cada archivo está en **`SHA256SUMS`**, firmado en
`SHA256SUMS.sig`. Cubre:

    README.md · INFORME.md · SELLO.md · .gitignore
    adns/ (3 perfiles)
    scripts/ (runner, análisis de validez, utilidades, sellado y verificación)
    dataset/resultados.json · dataset/analisis_validez.txt · dataset/crudos/ (3 corridas)

---

## 5. Alcance de lo firmado

Este sello certifica **integridad y autoría del paquete**, no la veracidad de los resultados.
La validez de los datos depende de terceros (los proveedores de modelos) y del método descrito
en `INFORME.md`, donde se documentan las limitaciones del estudio y el filtro de validez de
sustrato aplicado antes de interpretar cualquier métrica.

Reproducir el análisis completo, sin depender de terceros:

    python3 scripts/analisis_validez.py dataset/resultados.json

---

## 6. Alcance del paquete publicado

| Elemento | Valor |
|---|---|
| Versión | **v1.0.0** — 24 de septiembre de 2026 |
| Perfiles | 5 (ADN VEX + 2 identidades densas SOUL + 2 controles neutros) |
| Sustratos | 2 — `deepseek-flash` (China) y `google/gemma-4-31b-it` (Reino Unido/UE) |
| Condiciones | 10 (5 perfiles × 2 sustratos) |
| Corridas independientes | 3 por condición |
| Iteraciones | 15 por condición · **150 en total** (135 conformes, 90%) |

El promedio entre corridas se publica junto a su **rango**, no como cifra aislada: un promedio sin
rango oculta si la firma se repite o si es ruido. La distinción es el punto central del estudio.

### Correspondencia entre el ADN publicado y el ADN ejecutado

**El dataset de este sello fue producido con los ADN que se publican en `adns/`, sin diferencias.**
Las doce corridas acumuladas se ejecutaron íntegramente con los perfiles publicados.

---

*Sellado el 24 de septiembre de 2026. 🌙*
