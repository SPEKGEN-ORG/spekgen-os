# secrets/ — Credenciales SPEKGEN cifradas

Este folder contiene **credenciales del equipo cifradas con AES-256-CBC + PBKDF2 (200K iteraciones)**. El password lo comparte Gibran con cada miembro nuevo vía Signal/WhatsApp encriptado.

## Workflow

### Pedro / nuevo miembro: descifrar la primera vez

```bash
# Mac/Linux
bash scripts/decrypt-secrets.sh

# Windows PowerShell
.\scripts\decrypt-secrets.ps1
```

Te pide el password (te lo pasa Gibran). Descifra en `~/.env.spekgen` con permisos 600. Scripts del repo lo cargan automáticamente desde ahí.

### Gibran: agregar/cambiar credenciales

1. Descifra a archivo temporal:
   ```bash
   openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -d \
       -in secrets/credentials.env.enc \
       -out /tmp/edit_secrets.env \
       -k 'TU_PASSWORD'
   ```
2. Edita `/tmp/edit_secrets.env`.
3. Re-cifra y borra el plaintext:
   ```bash
   openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -salt \
       -in /tmp/edit_secrets.env \
       -out secrets/credentials.env.enc \
       -k 'TU_PASSWORD'
   rm -P /tmp/edit_secrets.env
   ```
4. Commit + push:
   ```bash
   git add secrets/credentials.env.enc
   git commit -m "chore(secrets): rotate <provider> token"
   git push
   ```

### Pedro: tras un git pull si las credenciales cambiaron

```bash
bash scripts/decrypt-secrets.sh
# (re-descifra sobre ~/.env.spekgen)
```

## Reglas

- **NUNCA** commitees el archivo descifrado. `.env.spekgen`, `decrypted.env`, etc. están en `.gitignore`.
- **NUNCA** pegues el password en chat público, GitHub Issues, Slack/Discord, email plano.
- **Password rotation:** si sospechas leak del password, Gibran genera nuevo password, re-cifra todo el archivo, y rota credenciales individuales que sean alto-riesgo (Meta tokens, Shopify, OpenAI).
- **Credenciales individuales rotan:** edita-cifra-commit (no requiere rotar el password del archivo).

## Estructura del archivo descifrado

`credentials.env.enc` contiene un único `.env` consolidado con secciones comentadas por cliente:

```
# ======================
# SPEKGEN AGENCY
# fuente: SPK - SPEKGEN AGENCY/.env
# ======================
META_TOKEN=...
APIFY_TOKEN=...
...

# ======================
# HC HEALTHY CHUCHOS
# fuente: HC - HEALTHY CHUCHOS/.env
# ======================
HC_SHOPIFY_TOKEN=...
...
```

Scripts del repo cargan `~/.env.spekgen` con `python-dotenv`. Variables se accesan con `os.environ["HC_SHOPIFY_TOKEN"]`.

## Algoritmo

```
AES-256-CBC
PBKDF2-SHA256 con 200,000 iteraciones
Salt aleatorio por archivo (incluido en output)
```

Equivalente moderno a `openssl enc` con buenas defaults. Compatible con cualquier OpenSSL 1.1.1+.

Para verificar integridad del archivo cifrado:
```bash
openssl enc -aes-256-cbc -pbkdf2 -iter 200000 -d \
    -in secrets/credentials.env.enc -k 'TU_PASSWORD' | head -5
```

Si el password es incorrecto, openssl tira `bad decrypt`. Si el archivo está corrupto, tira `bad magic number`.
