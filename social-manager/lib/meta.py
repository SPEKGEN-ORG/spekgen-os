"""Helpers Graph API para el social manager. Solo lectura + reply (reply lo usa Fase 2/3).
Detecta comentarios sin atender en 3 fuentes: FB feed, IG media, y ADS dark posts."""
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import datetime

GRAPH_VERSION = "v21.0"
BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"


def _request(url, method="GET", data=None, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, method=method)
            body = None
            if data is not None:
                body = urllib.parse.urlencode(data).encode()
            with urllib.request.urlopen(req, data=body, timeout=40) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            payload = e.read().decode("utf-8", "replace")
            # rate limit (code 4/17/32/613) -> backoff
            if e.code in (429, 500, 503) or '"code":4' in payload or '"code":17' in payload or '"code":613' in payload:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt * 3)
                    continue
            raise RuntimeError(f"Graph {e.code}: {payload[:300]}")
        except urllib.error.URLError:
            if attempt < retries - 1:
                time.sleep(2 ** attempt * 2)
                continue
            raise
    raise RuntimeError("Graph: retries agotados")


def _get(path, params):
    return _request(f"{BASE}/{path}?{urllib.parse.urlencode(params)}")


def days_ago(ts):
    if not ts:
        return None
    try:
        # FB: 2026-06-20T12:00:00+0000 ; IG: 2026-06-20T12:00:00+0000
        s = ts[:19]
        dt = datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
        return (datetime.datetime.utcnow() - dt).days
    except Exception:
        return None


def page_access_token(page_id, user_token):
    """Saca un Page Access Token desde el system-user token (para leer/responder como la Pagina)."""
    return _get(page_id, {"fields": "access_token", "access_token": user_token})["access_token"]


# ----------------------- COMENTARIOS -----------------------

def _comment_unanswered_fb(c, page_id):
    """Top-level comment de FB sin reply de la pagina."""
    frm = (c.get("from") or {}).get("id")
    if frm == page_id:
        return False
    # comment_count = # de replies en el hilo. 0 => nadie respondio.
    return c.get("comment_count", 0) == 0


def fb_feed_comments(page_id, page_token, limit=25):
    out = []
    data = _get(f"{page_id}/feed", {
        "fields": "id,message,created_time,permalink_url,"
                  "comments.limit(50){id,message,from,created_time,comment_count,permalink_url}",
        "limit": limit, "access_token": page_token,
    }).get("data", [])
    for post in data:
        for c in (post.get("comments", {}) or {}).get("data", []):
            if _comment_unanswered_fb(c, page_id):
                out.append(_norm_fb_comment(c, post.get("id"), source="organic", ad_name=None))
    return out


def ad_comments(ad_account, page_id, ads_token, page_token, ig_username=None, max_ads=100):
    """Comentarios sin atender en dark posts (la fuente real para clientes ad-heavy).
    Cubre AMBOS lados del anuncio: la historia de FB (effective_object_story_id) y el
    media de IG (effective_instagram_media_id). Sin el lado IG, los comentarios de
    anuncios en Instagram quedaban invisibles (caso Oceane LF, 2026-07-13)."""
    out = []
    seen_stories = set()
    seen_ig = set()
    ads = _get(f"{ad_account}/ads", {
        "fields": "id,name,effective_status,"
                  "creative{effective_object_story_id,effective_instagram_media_id}",
        "limit": max_ads, "access_token": ads_token,
    }).get("data", [])
    for a in ads:
        cr = a.get("creative") or {}
        # --- lado FB (dark post) ---
        sid = cr.get("effective_object_story_id")
        if sid and sid not in seen_stories:
            seen_stories.add(sid)
            try:
                cs = _get(f"{sid}/comments", {
                    "fields": "id,message,from,created_time,comment_count,permalink_url",
                    "limit": 50, "access_token": page_token,
                }).get("data", [])
                for c in cs:
                    if _comment_unanswered_fb(c, page_id):
                        out.append(_norm_fb_comment(c, sid, source="ad", ad_name=a.get("name")))
            except RuntimeError:
                pass
        # --- lado IG (dark post) ---
        mid = cr.get("effective_instagram_media_id")
        if mid and mid not in seen_ig:
            seen_ig.add(mid)
            try:
                cs = _get(f"{mid}/comments", {
                    "fields": "id,text,username,timestamp,replies.limit(10){username}",
                    "limit": 50, "access_token": page_token,
                }).get("data", [])
                for c in cs:
                    if _ig_unanswered(c, ig_username):
                        out.append(_norm_ig_comment(c, {"id": mid, "permalink": None},
                                                    ig_username, source="ad", ad_name=a.get("name")))
            except RuntimeError:
                pass
    return out


def ig_media_comments(ig_id, page_token, ig_username, limit=25):
    out = []
    data = _get(f"{ig_id}/media", {
        "fields": "id,caption,timestamp,permalink,comments_count,"
                  "comments.limit(50){id,text,username,timestamp,replies.limit(10){username}}",
        "limit": limit, "access_token": page_token,
    }).get("data", [])
    for m in data:
        for c in (m.get("comments", {}) or {}).get("data", []):
            if _ig_unanswered(c, ig_username):
                out.append(_norm_ig_comment(c, m, ig_username))
    return out


def _norm_fb_comment(c, parent_id, source, ad_name):
    return {
        "channel": "ad_comment" if source == "ad" else "fb_comment",
        "type": "comment", "source": source,
        "external_id": c["id"], "parent_id": parent_id, "ad_name": ad_name,
        "author": (c.get("from") or {}).get("name"),
        "author_id": (c.get("from") or {}).get("id"),
        "body": c.get("message"),
        "permalink": c.get("permalink_url"),
        "item_created_at": _iso(c.get("created_time")),
        "age_days": days_ago(c.get("created_time")),
    }


def _norm_ig_comment(c, media, ig_username, source="organic", ad_name=None):
    return {
        "channel": "ig_comment", "type": "comment", "source": source,
        "external_id": c["id"], "parent_id": media.get("id"), "ad_name": ad_name,
        "author": c.get("username"), "author_id": None,
        "body": c.get("text"),
        "permalink": media.get("permalink"),
        "item_created_at": _iso(c.get("timestamp")),
        "age_days": days_ago(c.get("timestamp")),
    }


def _ig_unanswered(c, ig_username):
    """Comentario de IG que no es de la propia cuenta y sin reply de la cuenta."""
    if c.get("username") == ig_username:
        return False
    return not any(r.get("username") == ig_username
                   for r in (c.get("replies", {}) or {}).get("data", []))


# ----------------------- DMs (IG) -----------------------

def ig_unanswered_dms(page_id, page_token, limit=25):
    """Conversaciones de IG cuyo ultimo mensaje es del usuario (sin responder)."""
    out = []
    try:
        convos = _get(f"{page_id}/conversations", {
            "platform": "instagram",
            "fields": "id,updated_time,participants,"
                      "messages.limit(1){id,message,from,created_time}",
            "limit": limit, "access_token": page_token,
        }).get("data", [])
    except RuntimeError:
        return out
    for cv in convos:
        msgs = (cv.get("messages", {}) or {}).get("data", [])
        if not msgs:
            continue
        last = msgs[0]
        frm = (last.get("from") or {}).get("id")
        if frm == page_id:   # la pagina ya fue la ultima en hablar
            continue
        parts = (cv.get("participants", {}) or {}).get("data", [])
        user = next((p for p in parts if p.get("id") != page_id), {})
        out.append({
            "channel": "ig_dm", "type": "dm", "source": "organic",
            "external_id": f"convo:{cv['id']}",  # dedupe por conversacion
            "parent_id": cv.get("id"), "ad_name": None,
            "author": user.get("username") or user.get("name"),
            "author_id": (last.get("from") or {}).get("id"),
            "body": last.get("message"),
            "permalink": None,
            "item_created_at": _iso(last.get("created_time")),
            "age_days": days_ago(last.get("created_time")),
        })
    return out


def reply_to_comment(channel, comment_id, message, page_token):
    """Publica una respuesta a un comentario. Devuelve {'id': <reply_id>}.
    IG: POST /{comment}/replies ; FB/ad: POST /{comment}/comments."""
    path = f"{comment_id}/replies" if channel == "ig_comment" else f"{comment_id}/comments"
    return _request(f"{BASE}/{path}", method="POST",
                    data={"message": message, "access_token": page_token})


def send_private_reply(channel, page_id, ig_id, comment_id, message, page_token):
    """Envía UNA respuesta privada (DM) al autor de un comentario (ventana de 7 días).
    FB/ad: POST /{page_id}/messages ; IG: POST /{ig_id}/messages. recipient={comment_id}.
    Requiere pages_messaging (FB) / instagram_manage_messages (IG). Devuelve la respuesta cruda."""
    # FB usa 'me/messages' (me = la página, según el page token); IG usa {ig_id}/messages.
    # OJO: NADA de messaging_type — con él Meta rechaza el comment_id (subcode 1893060).
    actor = ig_id if channel == "ig_comment" else "me"
    body = {
        "recipient": json.dumps({"comment_id": comment_id}),
        "message": json.dumps({"text": message}),
        "access_token": page_token,
    }
    return _request(f"{BASE}/{actor}/messages", method="POST", data=body)


def send_message_to_user(recipient_id, message, page_token):
    """Mensaje de seguimiento a un usuario ya en conversación (ventana 24h)."""
    body = {
        "recipient": json.dumps({"id": recipient_id}),
        "message": json.dumps({"text": message}),
        "access_token": page_token,
    }
    return _request(f"{BASE}/me/messages", method="POST", data=body)


def _iso(ts):
    if not ts:
        return None
    try:
        return datetime.datetime.strptime(ts[:19], "%Y-%m-%dT%H:%M:%S").isoformat() + "Z"
    except Exception:
        return None
