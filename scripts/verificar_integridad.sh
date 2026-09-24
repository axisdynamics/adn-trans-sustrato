#!/usr/bin/env bash
# Verifica que el paquete no fue alterado: hashes + firmas SSH.
# Uso:  bash scripts/verificar_integridad.sh
# No requiere ninguna clave secreta: solo allowed_signers (clave publica del autor).

set -uo pipefail
cd "$(dirname "$0")/.."
NS="adn-dataset"
PRINCIPAL="$(head -1 allowed_signers 2>/dev/null | awk '{print $1}')"
[ -z "$PRINCIPAL" ] && PRINCIPAL="mtorres@exis.cl"

echo "== Verificacion de integridad del dataset =="
echo "   autor (principal): $PRINCIPAL"
echo

fail=0

echo "[1/4] Inventario SHA-256"
if sha256sum -c SHA256SUMS --quiet 2>/dev/null; then
  echo "      OK — $(wc -l < SHA256SUMS) archivos intactos"
else
  echo "      FALLA — algun archivo fue modificado"; fail=1
fi

echo "[2/4] Firma del inventario"
if ssh-keygen -Y verify -f allowed_signers -I "$PRINCIPAL" -n "$NS" \
     -s SHA256SUMS.sig < SHA256SUMS >/dev/null 2>&1; then
  echo "      OK — inventario firmado por el autor"
else
  echo "      FALLA — firma invalida"; fail=1
fi

echo "[3/4] Firma del sello"
if ssh-keygen -Y verify -f allowed_signers -I "$PRINCIPAL" -n "$NS" \
     -s SELLO.md.sig < SELLO.md >/dev/null 2>&1; then
  echo "      OK — sello firmado por el autor"
else
  echo "      FALLA — firma invalida"; fail=1
fi

echo "[4/4] Firma dedicada del dataset"
if [ -f dataset/resultados.json.sig ]; then
  if ssh-keygen -Y verify -f allowed_signers -I "$PRINCIPAL" -n "$NS" \
       -s dataset/resultados.json.sig < dataset/resultados.json >/dev/null 2>&1; then
    echo "      OK — dataset/resultados.json firmado por el autor"
  else
    echo "      FALLA — firma del dataset invalida"; fail=1
  fi
else
  echo "      (sin firma dedicada)"
fi

echo
if [ "$fail" -eq 0 ]; then
  echo "RESULTADO: paquete AUTENTICO e INTACTO."
else
  echo "RESULTADO: NO VERIFICADO — revisar los puntos marcados."
fi
exit "$fail"
