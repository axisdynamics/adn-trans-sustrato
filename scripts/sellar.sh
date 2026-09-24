#!/usr/bin/env bash
# Sella el paquete: inventario SHA-256 + firmas SSH detached de los archivos clave.
# Uso:  bash scripts/sellar.sh
# Re-ejecutable: si el dataset cambia, volver a correr y commitear.

set -euo pipefail
cd "$(dirname "$0")/.."
REPO="$(pwd)"
KEY="${SSH_SIGNING_KEY:-$HOME/.ssh/id_ed25519}"
NS="adn-dataset"          # namespace de firma SSH

echo "== Sellando $REPO =="
echo "   clave: $KEY"
echo "   namespace de firma: $NS"

# 1. Claves publicas autorizadas a verificar (allowed_signers)
if [ ! -f allowed_signers ]; then
  pub="${KEY}.pub"
  principal="$(awk '{print $3}' "$pub")"
  echo "${principal:-plaxcito} $(cat "$pub")" > allowed_signers
  echo "   [creado] allowed_signers (principal: ${principal:-plaxcito})"
else
  echo "   [existe] allowed_signers"
fi

# 2. Inventario SHA-256 de todo el contenido versionado
#    (se excluyen: .git, las firmas .sig, el propio inventario y su firma)
rm -f SUBJECTS.txt
{
  find . -type f \
    ! -path "./.git/*" \
    ! -name "*.sig" \
    ! -name "SHA256SUMS" \
    ! -name "SUBJECTS.txt" \
    ! -name "*.pyc" \
    | sed 's|^\./||' | sort
} > SUBJECTS.txt

sha256sum $(cat SUBJECTS.txt) > SHA256SUMS
n=$(wc -l < SHA256SUMS)
echo "   [ok] SHA256SUMS: $n archivos"

# 3. Firmas SSH detached
sign() {
  local f="$1"
  rm -f "$f.sig"
  ssh-keygen -Y sign -f "$KEY" -n "$NS" "$f" >/dev/null 2>&1
  echo "   [firmado] $f.sig"
}

sign SHA256SUMS
sign SELLO.md

# firma dedicada del dataset principal
if [ -f dataset/resultados.json ]; then
  cp dataset/resultados.json dataset/resultados.json.tmp
  rm -f dataset/resultados.json.sig
  ssh-keygen -Y sign -f "$KEY" -n "$NS" dataset/resultados.json >/dev/null 2>&1
  rm -f dataset/resultados.json.tmp
  echo "   [firmado] dataset/resultados.json.sig"
fi

echo
echo "== Verificacion inmediata =="
sha256sum -c SHA256SUMS --quiet && echo "   [ok] hashes validos"
ssh-keygen -Y verify -f allowed_signers -I "$(head -1 allowed_signers | awk '{print $1}')" \
  -n "$NS" -s SHA256SUMS.sig < SHA256SUMS >/dev/null 2>&1 \
  && echo "   [ok] firma de SHA256SUMS valida" || echo "   [!] firma de SHA256SUMS NO valida"
ssh-keygen -Y verify -f allowed_signers -I "$(head -1 allowed_signers | awk '{print $1}')" \
  -n "$NS" -s SELLO.md.sig < SELLO.md >/dev/null 2>&1 \
  && echo "   [ok] firma de SELLO.md valida" || echo "   [!] firma de SELLO.md NO valida"
