---
name: Meta API Architecture
description: SPEKGENAUTOADS system user, BM hierarchy, tokens per client, and how auto-publish works in Content Hub
type: project
---

## BM Hierarchy

| Portfolio | ID | Rol |
|-----------|-----|-----|
| **Agencia** | `2131750914244150` | BM principal de la agencia. Tiene la app y system user |
| **SpekGen** | `1098447481453702` | BM secundario (branding). No tiene app |
| **lofitness_club** | `8859481914073957` | BM legacy de LO FITNESS. Tiene app vieja (NO USAR) |
| **metagreenlab** | `147581898378556` | BM del cliente MG. Debe compartir pagina/IG con Agencia BM |

## App y System User (CORRECTO — SIEMPRE USAR ESTE)

| Campo | Valor |
|-------|-------|
| App | **SPEKGEN Agency API** (`1465486404956665`) |
| System User | **SPEKGENAUTOADS** (real ID: `61576401581163`, app-scoped: `122100575132880052`, token-reported: `122098021449191940`) |
| BM | Agencia (`2131750914244150`) |
| Token | Sin caducidad, 22 scopes. Mismo valor para META_TOKEN, META_HC_TOKEN, META_PAGE_TOKEN, META_MG_TOKEN |
| Ultima regeneracion | 2026-04-03 |

**Why:** La app vieja de LO FITNESS (SpekGen Marketing API, `1683612316139834`) ya NO se usa. SPEKGENAUTOADS es el system user definitivo.

## Tokens en Vercel (Content Hub)

| Env Var | Valor | Usa |
|---------|-------|-----|
| `META_PAGE_TOKEN` | Token SPEKGENAUTOADS | Fallback general |
| `META_TOKEN` | Token SPEKGENAUTOADS | Igual al anterior |
| `META_HC_TOKEN` | Token SPEKGENAUTOADS | HC auto-publish |
| `META_LF_TOKEN` | Token viejo LF (legacy) | LF auto-publish |
| `META_SP_TOKEN` | INVALIDO | Necesita fix |
| `META_MG_TOKEN` | Token SPEKGENAUTOADS | MG + @gibran.alonzo.ecom auto-publish |

## IDs por Cliente (Vercel env vars)

| Cliente | Page ID env var | IG Account ID env var |
|---------|-----------------|----------------------|
| HC | `META_HC_PAGE_ID` = `102627388012544` | `META_HC_IG_ACCOUNT_ID` = `17841430824981516` |
| MG | `META_MG_PAGE_ID` = `132180209979937` | `META_MG_IG_ACCOUNT_ID` = `17841462109913746` |
| LF | `META_LF_PAGE_ID` | `META_LF_IG_ACCOUNT_ID` |
| SP/Gibran | `META_SP_PAGE_ID` | `META_SP_IG_ACCOUNT_ID` |

## IDs directos @gibran.alonzo.ecom (NO en Vercel env vars — solo en /publish-post skill)

| Campo | Valor |
|-------|-------|
| IG Business | `17841443011465783` (@gibran.alonzo.ecom) |
| FB Page | `1024749174062450` (Gibran Ecom) |
| Ad Account | `act_1431097605461576` |

## Auto-Publish Flow (Content Hub)

1. Cliente aprueba post en portal → `POST /api/approve`
2. Approve route busca `META_{CLIENT}_TOKEN` → fallback `META_PAGE_TOKEN`
3. Si `link_preview` es folder de Drive → descarga imagenes via service account → sube a Supabase Storage → usa URLs publicas
4. Llama `publishToInstagram()` con mediaUrls (Supabase Storage URLs) + caption
5. Si fecha futura → programa (scheduled_publish_time)
6. Si fecha hoy → publica inmediatamente

## Limitaciones Descubiertas (2026-04-03)

1. **Scheduling via API NO funciona**: Error "User must be on whitelist" al usar `published=false` + `scheduled_publish_time`. La app SPEKGENAUTOADS no tiene el permiso de scheduling. Publicacion inmediata SI funciona.
2. **Drive URLs no accesibles por Meta**: Las URLs de Google Drive (incluso con service account) no son descargables por Meta. Solucion: subir a Supabase Storage primero (bucket `previews`, publico).
3. **Token trailing \\n**: Al pegar tokens en Vercel, a veces se agrega `\\n` literal. Usar `printf '%s'` en vez de `echo` al setear env vars.

## Publicacion Directa @gibran.alonzo.ecom (Probado 2026-04-03)

**7 posts publicados exitosamente (GA-005 a GA-012):**
1. Imagenes locales de `00. IMAGENES FINALES/` o `00. WINNERS/` → Supabase Storage `previews/gibran/GA-XXX/`
2. URLs publicas: `https://wjlwpfaogjpeqgyxxnwa.supabase.co/storage/v1/object/public/previews/gibran/GA-XXX/{file}`
3. IG: child containers → carousel container → media_publish
4. FB: `POST /{page_id}/photos` con page access token + primera imagen

## MG — COMPLETADO 2026-04-03

MG's page (`132180209979937`) y IG (`17841462109913746`) estan en BM `metagreenlab` (`147581898378556`).
SPEKGENAUTOADS ahora tiene acceso completo.

**Pasos completados:**
1. En BM metagreenlab → Socios → Agregado BM `2131750914244150` (Agencia)
2. Compartida Pagina + IG con Agencia BM
3. Asignados assets a SPEKGENAUTOADS system user
4. Token regenerado (209 chars, sin caducidad)
5. Verificado: page info, IG account, content_publishing_limit — todo OK

## Publicación Directa via API (Probado — clientes)

**Flow que funciona (HC-005 carousel + GR-003 static):**
1. `GET /{page_id}?fields=access_token` → Page Access Token
2. `POST /{page_id}/photos` (published=false, temporary=true, files=source) → photo_id
3. `GET /{photo_id}?fields=images` → CDN URL (images[0].source)
4. Para carousel: `POST /{ig_user_id}/media` (image_url=CDN, is_carousel_item=true) × N → container_ids
5. `POST /{ig_user_id}/media` (media_type=CAROUSEL, children=ids, caption) → carousel_id
6. `GET /{carousel_id}?fields=status_code` → esperar FINISHED
7. `POST /{ig_user_id}/media_publish` (creation_id) → ig_post_id
8. FB cross-post: photos unpublished + `POST /{page_id}/feed` con attached_media[]

**Lo que NO funciona:**
- Resumable Upload handles (`fbupload://`) como image_url para IG → error "Only photo or video"
- System user token directo para Page photos → error "must be posted as page itself" (necesita Page Token)

**Errores transitorios:** IG da "An unexpected error" (is_transient=True) frecuentemente en carouseles. Fix: 5 retries + 5-8s delays entre containers. Single image posts no tienen este problema.

**Skill:** `/publish-post` para @gibran.alonzo.ecom en `SPK - SPEKGEN AGENCY/SPK - 02. SKILLS/publish-post/`

## How to apply

- SIEMPRE usar token de SPEKGENAUTOADS para nuevos clientes
- NUNCA usar el token viejo de LO FITNESS (system user ID `439469342587050`)
- Para cada cliente nuevo: agregar `META_{CLIENT}_TOKEN`, `META_{CLIENT}_PAGE_ID`, `META_{CLIENT}_IG_ACCOUNT_ID` a Vercel
- El BM del cliente debe compartir su pagina/IG con BM Agencia (`2131750914244150`)
- Para @gibran.alonzo.ecom: usar /publish-post skill directamente (no Content Hub)
