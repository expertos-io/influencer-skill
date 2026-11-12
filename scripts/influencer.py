#!/usr/bin/env python3
"""Influencer content from any agent — videos AND photos: Codex, Claude Code, ChatGPT tools, n8n...
Standard library only.

Each user connects THEIR agent to THEIR community (on the web address where they enter it) with OAuth.
Content is made with the influencers assigned to them, and everything is paid with their own credits.

  python3 influencer.py login                        # a link to authorize; run it again until connected
  python3 influencer.py welcome                      # first steps: their influencers, angles and settings
  python3 influencer.py influencer-photos <id|#number|name> [--out dir]   # download all the photos of one
  python3 influencer.py whoami                       # connected? community, permissions, credit balance
  python3 influencer.py influencers                  # YOUR influencers (assigned to you)
  python3 influencer.py models                       # the three tiers, qualities and price per second
  python3 influencer.py prefs [--model ultra --beauty on --quality normal]   # the user's defaults (saved here)
  python3 influencer.py quote  --influencer <id|#number|name> --video <file|URL|Instagram link> [--model ...]
  python3 influencer.py create --influencer <id|#number|name> --video <file|URL|Instagram link>
                               [--model lite|pro|ultra] [--quality hd|normal] [--beauty on|off|low|medium|high]
                               [--prompt "..."] [--outfit photo|video] [--start 0 --end 12]
                               [--out ./videos] [--no-wait]
  python3 influencer.py create --model pro --image face.jpg --video clip.mp4 ...   # any photo: only with AI Studio
  python3 influencer.py finalize <task_id_of_an_ultra_480p> [--out ./videos]     # Ultra only: that draft in 1080p
  python3 influencer.py status <task_id>             # one look
  python3 influencer.py wait <task_id> [--out dir]   # poll until it ends and download
  python3 influencer.py upload <file>                # → public URL usable as video_url

  PHOTOS (recreate a photo with the influencer — any member, with their assigned influencers):
  python3 influencer.py photo  --influencer <id|#number|name> --photo <Instagram post link|file|URL>
                               [--slides 1,3 | --all] [--no-wait]
  python3 influencer.py photo-not-her <id>           # same photo again with the original face covered (once)
  python3 influencer.py photo-fix <id> "the top is black"   # redo with a correction
  python3 influencer.py photo-retry <id>             # again (a failed one in place)
  python3 influencer.py photo-approve <id>           # keep it: goes to the influencer's content
  python3 influencer.py photo-status <id> | photo-wait <id> [<id> ...] [--out dir]
  python3 influencer.py logout                       # revokes the token

--video / --image accept a local file (uploaded first) or an https URL; --video also an Instagram reel or
post link (downloaded on the server). Without --model/--quality/--beauty the user's `prefs` are used
(first time: Ultra 480p, the cheapest, beauty on; HD 1080p only if the user chooses it).
Everything goes to the web address of the community (its /v1 API): COMMUNITY_SITE below. Env: INFLUENCER_SITE (another address),
INFLUENCER_TOKEN (use this token instead of the saved one).
Config (token): ~/.config/influencer-content/config.json (0600). Never print it or paste it in chats.
"""
import argparse, hashlib, json, mimetypes, os, shutil, subprocess
import sys, tempfile, time, urllib.error, urllib.parse, urllib.request, uuid, webbrowser

# ═══════════════════════════════════════════════════════════════════════════════════════════════════
# THE COMMUNITY: the web address this skill connects to. Edit ONLY this line, e.g.
#   COMMUNITY_SITE = "https://app.yourbrand.com"
# Empty = the main site, where the person signs in and picks their community.
COMMUNITY_SITE = ""
# ═══════════════════════════════════════════════════════════════════════════════════════════════════

DEFAULT_SITE = "https://bizo.so"
CONFIG = os.path.expanduser("~/.config/influencer-content/config.json")
# Public OAuth app (PKCE only, no secret) «Influencer · Crear contenido», 9-nov-2026
CLIENT_ID = "bz_client_3dbc80e94f12bf7c780cc536"
UA = "influencer-content/1.0"
MAX_UPLOAD = 20 * 1024 * 1024  # POST /v1/influencer/videos/files

MODELS = {
    "lite": "influencer-video-lite",
    "pro": "influencer-video-pro",
    "ultra": "influencer-video-ultra",
}
QUALITIES = {"lite": ["1080p"], "pro": ["720p", "1080p"], "ultra": ["480p", "720p", "1080p"]}
NAMES = {"lite": "Lite", "pro": "Pro", "ultra": "Ultra"}
# What the user gets when they have not chosen yet (and what `prefs` saves on top of)
# Quality: the cheapest of the tier unless the user asks for HD (Manuel, 10-nov: 1080p only on request)
# Model: Ultra, the cheapest in 480p and the fastest (Manuel, 10-nov)
DEFAULT_PREFS = {"model": "ultra", "beauty": "medium", "quality": "normal"}
BEAUTY_ALIASES = {"on": "medium", "si": "medium", "yes": "medium", "true": "medium", "no": "off", "false": "off"}


class ContentError(Exception):
    def __init__(self, msg, status=None):
        super().__init__(msg)
        self.status = status


def friendly(e):
    """One plain sentence for the user (no codes, no technical words) for any error."""
    m, st = str(e).lower(), getattr(e, "status", None)
    if st == "not_a_site":
        return "Esa dirección no parece la de tu comunidad. ¿Me pasas el enlace con el que entras a ella?"
    if st == 402 or "insufficient_credits" in m:
        return "No tienes créditos suficientes para esto. Puedes recargar tus créditos en tu comunidad."
    if st == 401 or "not connected" in m or "run `login`" in m:
        return "Tengo que volver a conectar tu cuenta. Te paso un enlace en un momento."
    if "influencer" in m and (st == 404 or "not one of your" in m):
        return "Esa influencer no está entre las tuyas. Te digo cuáles tienes."
    if "no influencers assigned" in m:
        return "Todavía no tienes ninguna influencer asignada. Cuando tu comunidad te asigne una, podemos crear contenido."
    if "could not be read" in m or "private" in m or "deleted" in m:
        return ("No he podido abrir esa publicación: puede que la cuenta sea privada o que se haya borrado. "
                "¿Me pasas otro enlace o la foto directamente?")
    if "instagram" in m:
        return "Instagram no me deja abrir esa publicación ahora mismo. Lo intento en un minuto, o pásame la foto o el vídeo directamente."
    if st == 403:
        return "Tu comunidad todavía no te ha dado acceso a esto. Pídeselo a quien la gestiona."
    if st in (400, 422):
        return "Ese archivo o enlace no me sirve tal cual. ¿Me pasas otro?"
    if "no connection" in m:
        return "No consigo conectar ahora mismo. Lo intento de nuevo en un momento."
    return "Algo ha fallado por el camino. ¿Lo intento otra vez?"


def die(msg, code=1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def load_config():
    try:
        with open(CONFIG) as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG), exist_ok=True)
    with open(CONFIG, "w") as f:
        json.dump(cfg, f, indent=2)
    os.chmod(CONFIG, 0o600)


def out(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False), flush=True)


# ------------------------------------------------------------------ HTTP
# Everything goes to the web address of the user's community (its /v1 API): on a white-label site, its own domain.

def site_of(value):
    """https://host of whatever the user gave (a link to their community, a bare domain…); "" if none."""
    v = (value or "").strip()
    if not v:
        return ""
    if not v.startswith("http"):
        v = "https://" + v
    u = urllib.parse.urlparse(v)
    return f"{u.scheme}://{u.netloc}" if u.netloc else ""


def fixed_site():
    """The community set for this skill (INFLUENCER_SITE or COMMUNITY_SITE); "" when none is set."""
    return site_of(os.environ.get("INFLUENCER_SITE") or COMMUNITY_SITE)


def api_base():
    """Where every call goes: the community of this skill, else the one the user connected to, else the main site."""
    cfg = load_config()
    return fixed_site() or site_of(cfg.get("web") or (cfg.get("pending") or {}).get("web")) or DEFAULT_SITE


def call(method, path, body=None, *, auth=True, files=None, form=None, timeout=300):
    url = path if path.startswith("http") else f"{api_base()}{path}"
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if auth:
        cfg = load_config()
        token = os.environ.get("INFLUENCER_TOKEN") or (
            cfg.get("token") if not fixed_site() or site_of(cfg.get("web")) == fixed_site() else None)
        if not token and load_config().get("pending") and finish_pending(0):
            token = load_config().get("token")
        if not token:
            raise ContentError("Not connected: run `login` and give the person the link")
        headers["Authorization"] = f"Bearer {token}"
    data = None
    if files:
        boundary = uuid.uuid4().hex
        parts = []
        for field, (name, content, ctype) in files.items():
            parts.append(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; filename=\"{name}\"\r\n"
                f"Content-Type: {ctype}\r\n\r\n".encode() + content + b"\r\n")
        data = b"".join(parts) + f"--{boundary}--\r\n".encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif form is not None:
        data = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                try:
                    res = json.loads(raw) if raw else {}
                except ValueError:
                    raise ContentError(f"{url} did not answer like a community site", "not_a_site")
                # The /api/v1/... routes wrap the answer in { success, data }
                return res["data"] if isinstance(res, dict) and res.get("success") is True and "data" in res else res
        except urllib.error.HTTPError as e:
            raw = e.read().decode(errors="replace")
            try:
                j = json.loads(raw)
                err = j.get("error") if isinstance(j.get("error"), dict) else {}
                code = err.get("code") or j.get("error") or ""
                msg = err.get("message") or j.get("error_description") or j.get("message") or raw[:300]
                msg = f"{e.code} {code}: {msg}"
            except Exception:
                msg = None
            if e.code in (429, 502, 503, 504) and attempt < 2:
                time.sleep(3 * (attempt + 1))
                continue
            if msg is None:
                # Not a JSON answer: that address is not a community site (or it doesn't serve its API)
                raise ContentError(f"{url} did not answer like a community site ({e.code})", "not_a_site")
            if e.code == 401 and auth:
                msg += " — the token was revoked or is invalid: run `login` again"
            raise ContentError(msg, e.code)
        except urllib.error.URLError as e:
            if attempt < 2:
                time.sleep(3 * (attempt + 1))
                continue
            raise ContentError(f"No connection with {url}: {e.reason}")


# ------------------------------------------------------------------ login (device flow, RFC 8628)
# The agent asks the community's site for a link; the person opens it, signs in and presses «Authorize»;
# the agent picks the connection up by itself. Nothing to copy or paste, works in any sandbox.

DEVICE_GRANT = "urn:ietf:params:oauth:grant-type:device_code"


def web_of(a=None):
    return (site_of(a and (getattr(a, "site", None) or getattr(a, "web", None))) or fixed_site()
            or site_of(load_config().get("web")) or DEFAULT_SITE)


def finish_pending(wait_s=0):
    """Polls the pending device login (if any). Returns True when connected, False if still waiting."""
    cfg = load_config()
    p = cfg.get("pending")
    if not p:
        return False
    if time.time() > p["expires_at"]:
        cfg.pop("pending", None)
        save_config(cfg)
        raise ContentError("The link expired before it was authorized: run `login` again for a new one")
    deadline = time.time() + wait_s
    while True:
        try:
            tok = call("POST", f"{p['web']}/v1/oauth/token", auth=False, form={
                "grant_type": DEVICE_GRANT, "device_code": p["device_code"], "client_id": p["client_id"]})
        except ContentError as e:
            msg = str(e)
            if "authorization_pending" in msg or "slow_down" in msg:
                if time.time() + p.get("interval", 5) > deadline:
                    return False
                time.sleep(p.get("interval", 5))
                continue
            cfg.pop("pending", None)
            save_config(cfg)
            if "access_denied" in msg:
                raise ContentError("The person cancelled the connection: run `login` again if they want to connect")
            if "expired_token" in msg:
                raise ContentError("The link expired: run `login` again for a new one")
            raise
        cfg = load_config()
        cfg.pop("pending", None)
        cfg.update({"token": tok["access_token"], "scope": tok.get("scope"), "client_id": p["client_id"],
                    "web": p["web"], "community": (tok.get("community") or {}).get("slug")})
        save_config(cfg)
        return True


def connected_summary():
    cfg = load_config()
    credits = call("GET", "/v1/credits")
    onboarded = bool((cfg.get("onboarded") or {}).get(cfg.get("community") or "?"))
    return {"connected": True, "community": cfg.get("community"), "permissions": cfg.get("scope"),
            "credits_available": credits.get("available"), "prefs": prefs(),
            "first_time": not cfg.get("prefs"), "onboarded": onboarded, "name": cfg.get("name"),
            "next": "ask what they want to make" if onboarded else "run `welcome` and say its messages (first steps)"}


# ------------------------------------------------------------------ the user's defaults

def prefs():
    """The user's saved defaults (model, beauty, quality), on top of DEFAULT_PREFS."""
    return {**DEFAULT_PREFS, **(load_config().get("prefs") or {})}


def quality_of(value, key):
    """normal (default) = the cheapest the tier renders (Ultra 480p, Pro 720p, Lite 1080p); hd = 1080p; or an exact one."""
    v = (value or "normal").lower()
    if v in ("hd", "1080", "1080p", "full"):
        return "1080p"
    if v in ("normal", "sd", "low", "draft"):
        return QUALITIES[key][0]
    v = v if v.endswith("p") else v + "p"
    if v not in QUALITIES[key]:
        die(f"{MODELS[key]} renders {', '.join(QUALITIES[key])} (not {value})")
    return v


def beauty_of(value):
    v = (value or "medium").lower()
    v = BEAUTY_ALIASES.get(v, v)
    if v not in ("off", "low", "medium", "high"):
        die(f"--beauty must be on, off, low, medium or high (got {value})")
    return v


def beauty_words(level):
    return {"off": "sin mejorador de belleza", "low": "con el mejorador de belleza suave",
            "medium": "con el mejorador de belleza activado", "high": "con el mejorador de belleza al máximo"}[level]


def cmd_prefs(a):
    cfg = load_config()
    p = dict(cfg.get("prefs") or {})
    if a.model:
        p["model"] = model_of(a.model)[0]
    if a.beauty:
        p["beauty"] = beauty_of(a.beauty)
    if a.quality:
        p["quality"] = a.quality.lower()
    if a.reset:
        p = {}
    if a.model or a.beauty or a.quality or a.reset:
        cfg["prefs"] = p
    if a.name:
        cfg["name"] = a.name.strip()[:60]
    if a.model or a.beauty or a.quality or a.reset or a.name:
        save_config(cfg)
    out({"prefs": prefs(), "first_time": not load_config().get("prefs"), "name": load_config().get("name")})


def cmd_login(a):
    cfg = load_config()
    # A link already given and not expired: keep waiting for it (the person may be authorizing right now)
    if cfg.get("pending") and not a.new and time.time() < cfg["pending"]["expires_at"]:
        if finish_pending(a.wait):
            out(connected_summary())
            return
        p = load_config()["pending"]
        out({"status": "waiting", "link": p["link"],
             "say_to_user": "Abre este enlace, entra con tu cuenta y pulsa «Autorizar». "
                            "Cuando veas «¡Listo!», vuelve aquí y dímelo.",
             "then": "run `login` again (it picks the connection up)"})
        return
    web = web_of(a)
    client_id = a.client_id or CLIENT_ID
    d = call("POST", f"{web}/v1/oauth/device_authorization", auth=False,
             form={"client_id": client_id, "scope": "influencer ai"})
    # The link always on the site where the person signs in (their community's address)
    link = f"{web}/oauth/device?user_code={d['user_code']}"
    cfg = load_config()
    cfg.pop("token", None)
    cfg["web"] = web
    cfg["pending"] = {"device_code": d["device_code"], "user_code": d["user_code"], "client_id": client_id,
                      "web": web, "link": link, "interval": d.get("interval", 5),
                      "expires_at": time.time() + int(d.get("expires_in", 600)) - 5}
    save_config(cfg)
    try:
        webbrowser.open(link)
    except Exception:
        pass
    print(json.dumps({"status": "waiting", "link": link,
                      "say_to_user": "Abre este enlace, entra con tu cuenta y pulsa «Autorizar». "
                                     "Cuando veas «¡Listo!», vuelve aquí y dímelo."}, ensure_ascii=False), flush=True)
    if finish_pending(a.wait):
        out(connected_summary())
    else:
        out({"status": "waiting", "then": "when the person says it's done, run `login` again"})


def cmd_logout(a):
    cfg = load_config()
    if not cfg.get("token"):
        die("Not connected")
    try:
        call("POST", "/v1/oauth/revoke", auth=False,
             form={"token": cfg["token"], "client_id": cfg.get("client_id") or CLIENT_ID})
    except ContentError as e:
        print(f"Revoke: {e}", file=sys.stderr)
    cfg.pop("token", None)
    save_config(cfg)
    out({"connected": False})


def cmd_whoami(a):
    out(connected_summary())


# ------------------------------------------------------------------ files

def compress_video(path):
    """A video over 20 MB is re-encoded (H.264, ≤1280 px, keeps the audio) so it can be uploaded."""
    if not shutil.which("ffmpeg"):
        raise ContentError(f"{os.path.basename(path)} is over 20 MB and ffmpeg is not installed: "
                        "compress it or pass an https URL instead")
    dst = os.path.join(tempfile.mkdtemp(prefix="influencer-video-"), "input.mp4")
    for crf in (23, 28, 32):
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", path, "-vf",
                        "scale='min(1280,iw)':'min(1280,ih)':force_original_aspect_ratio=decrease,"
                        "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-preset", "medium", "-crf", str(crf),
                        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", dst], check=True)
        if os.path.getsize(dst) <= MAX_UPLOAD:
            return dst
    raise ContentError("The video is still over 20 MB after compressing: cut it with --start/--end")


def upload(path):
    if not os.path.isfile(path):
        raise ContentError(f"File not found: {path}")
    name = os.path.basename(path)
    ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
    if os.path.getsize(path) > MAX_UPLOAD:
        if not ctype.startswith("video/"):
            raise ContentError(f"{name}: over 20 MB")
        path, ctype = compress_video(path), "video/mp4"
        name = os.path.splitext(name)[0] + ".mp4"
    with open(path, "rb") as f:
        content = f.read()
    return call("POST", "/v1/influencer/videos/files", files={"file": (name, content, ctype)})


def as_url(value, what):
    if value.startswith("https://") or value.startswith("http://"):
        return value
    f = upload(value)
    print(f"uploaded {what}: {f['url']}", file=sys.stderr, flush=True)
    return f["url"]


def cmd_upload(a):
    out(upload(a.file))


# ------------------------------------------------------------------ models, quote, tasks

def model_of(name):
    key = name.lower().replace("influencer-video-", "")
    if key not in MODELS:
        die(f"--model must be lite, pro or ultra (got {name})")
    return key, MODELS[key]


def mine():
    return call("GET", "/v1/influencer/mine")


def resolve_influencer(ref, catalog=False):
    """An influencer of yours by id, #number or name (GET /v1/influencer/mine); with `catalog`, an admin may also
    use any influencer of the community (GET /v1/influencer/influencers)."""
    res = mine()
    items = res.get("data") or []
    if catalog:
        try:
            more = call("GET", "/v1/influencer/influencers").get("data") or []
            seen = {i["id"] for i in items}
            items += [{"id": i["id"], "number": i.get("number"), "name": i.get("name"),
                       "main_url": i.get("main_url") or i.get("cover_url")} for i in more if i.get("id") not in seen]
        except ContentError:
            pass
    if not items:
        raise ContentError("You have no influencers assigned in this community: nothing can be created until the "
                        "community assigns you one")
    r = ref.strip().lstrip("#")
    for i in items:
        if i["id"] == r or str(i.get("number")) == r or (i.get("name") or "").lower() == r.lower():
            return i
    names = ", ".join(f"#{i.get('number')} {i.get('name')}" for i in items)
    raise ContentError(f"«{ref}» is not one of your influencers ({names})")


def cmd_influencers(a):
    res = mine()
    items = res.get("data") or []
    out({"influencers": [{"id": i["id"], "number": i.get("number"), "name": i.get("name"), "main_url": i.get("main_url")}
                         for i in items],
         "count": len(items),
         **({"note": "No influencers assigned to you here: you cannot create content until one is assigned"}
            if not items else {})})


# ------------------------------------------------------------------ first steps (a short onboarding, once)

ANGLES = ["front", "three_quarter_left", "three_quarter_right", "profile", "over_shoulder", "arms_crossed",
          "laughing", "closeup", "looking_away", "neutral"]
SETTINGS = ["interview", "youtube", "selfie", "headshots", "in_car", "stage", "podcast", "office", "gym",
            "concert", "ugc"]
LABELS = {
    "front": "De frente", "three_quarter_left": "Tres cuartos (izquierda)", "three_quarter_right": "Tres cuartos (derecha)",
    "profile": "De perfil", "over_shoulder": "Por encima del hombro", "arms_crossed": "Brazos cruzados",
    "laughing": "Riendo", "closeup": "Primer plano", "looking_away": "Mirando a otro lado", "neutral": "Neutral",
    "interview": "Entrevista", "youtube": "YouTube", "selfie": "Selfie", "headshots": "Retrato", "in_car": "En el coche",
    "stage": "En un escenario", "podcast": "Podcast", "office": "Oficina", "gym": "Gimnasio", "concert": "Concierto",
    "ugc": "UGC",
}


def pack_counts(inf):
    keys = {p.get("key") for p in inf.get("pack") or []}
    return sum(k in keys for k in ANGLES), sum(k in keys for k in SETTINGS)


def num(n):
    return f"{int(n):,}".replace(",", ".")


def names_list(items):
    names = [i.get("name") or f"#{i.get('number')}" for i in items]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " y " + names[-1]


def content_prices():
    """GET /v1/influencer/prices: what a photo and a short video cost now (None if it can't be read)."""
    try:
        return call("GET", "/v1/influencer/prices")
    except ContentError:
        return None


def cmd_welcome(a):
    """The first messages after connecting: their influencers, their credits (and how much they buy), then their
    photos or straight to recreating. Saved per community, so it is only done once."""
    cfg = load_config()
    community = cfg.get("community") or "?"
    first_time = not (cfg.get("onboarded") or {}).get(community)
    hi = f"🎉 ¡Listo, {cfg['name']}! Tu cuenta está conectada." if cfg.get("name") else "🎉 ¡Listo! Tu cuenta está conectada."
    items = mine().get("data") or []
    credits = call("GET", "/v1/credits").get("available") or 0
    pr = content_prices()
    photos = videos = None
    if pr and credits:
        photos = int(credits // max(1, (pr.get("photo") or {}).get("credits_min") or 6))
        videos = int(credits // max(1, (pr.get("cheapest_video") or {}).get("credits") or 83))
    if credits <= 0:
        money = "Todavía no tienes créditos: puedes recargarlos en tu comunidad."
    elif photos is not None:
        money = (f"Tienes {num(credits)} créditos disponibles: te alcanzan para unas {num(photos)} fotos "
                 f"o unos {num(videos)} vídeos cortos.")
    else:
        money = f"Tienes {num(credits)} créditos disponibles."
    if not items:
        first = (f"{hi} {money} Todavía no tienes ninguna influencer asignada: "
                 "cuando tu comunidad te asigne una, te ayudo a crear fotos y vídeos con ella.")
        second = None
    elif len(items) == 1:
        i = items[0]
        ang, sett = pack_counts(i)
        first = f"{hi} Ahora mismo tienes disponible a {i.get('name')}. {money}"
        second = (f"¿Quieres ver las fotos de {i.get('name')}? Tiene {ang} ángulos y {sett} escenarios. "
                  f"O, si prefieres empezar ya, pásame el link de una foto o de un vídeo de Instagram y lo recreo "
                  f"con ella.")
    else:
        parts = []
        for i in items:
            ang, sett = pack_counts(i)
            parts.append(f"{i.get('name')} ({ang} ángulos y {sett} escenarios)")
        first = (f"{hi} Ahora mismo tienes disponibles {len(items)} influencers: "
                 f"{names_list(items)}. {money}")
        second = (f"¿Quieres ver las fotos de alguna? {'; '.join(parts)}. O, si prefieres empezar ya, pásame el link "
                  f"de una foto o de un vídeo de Instagram y te pregunto con cuál lo recreo.")
    cfg = load_config()
    cfg.setdefault("onboarded", {})[community] = True
    save_config(cfg)
    out({"first_time": first_time, "credits_available": credits, "estimate": {"photos": photos, "videos": videos},
         "influencers": [{"id": i["id"], "number": i.get("number"), "name": i.get("name"),
                          "angles": pack_counts(i)[0], "settings": pack_counts(i)[1]} for i in items],
         "say_to_user": [m for m in (first, second) if m]})


def cmd_influencer_photos(a):
    """Downloads the main photo and every angle and setting of one influencer, to show them in the chat."""
    inf = resolve_influencer(a.influencer)
    full = next((i for i in mine().get("data") or [] if i["id"] == inf["id"]), inf)
    name = full.get("name") or f"#{full.get('number')}"
    folder = os.path.join(a.out, "".join(c for c in name if c.isalnum() or c in " -_").strip() or full["id"])
    os.makedirs(folder, exist_ok=True)
    by_key = {p.get("key"): p for p in full.get("pack") or []}
    main = by_key.get("main") or {}
    shots = [("main", "Foto principal", main.get("md_url") or main.get("url") or full.get("main_url"))]
    shots += [(k, LABELS.get(k, k), by_key[k].get("md_url") or by_key[k].get("url")) for k in ANGLES + SETTINGS if k in by_key]
    files = []
    for n, (key, label, url) in enumerate(shots):
        if not url:
            continue
        ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower() or ".jpg"
        path = os.path.join(folder, f"{n:02d}-{key}{ext if ext in ('.jpg', '.jpeg', '.png', '.webp') else '.jpg'}")
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as resp, open(path, "wb") as fh:
            shutil.copyfileobj(resp, fh)
        files.append({"key": key, "label": label, "kind": "angle" if key in ANGLES else "setting" if key in SETTINGS else "main",
                      "saved": path})
    ang, sett = pack_counts(full)
    out({"influencer": name, "files": files,
         "say_to_user": (f"Estas son las fotos de {name}: {ang} ángulos y {sett} escenarios. Con ella puedes:\n"
                         f"📸 Recrear fotos: pásame el link de una publicación de Instagram (una foto o un carrusel) "
                         f"y la hago igual, pero con {name}.\n"
                         f"🎬 Recrear vídeos: pásame el link de un reel y hago el mismo vídeo con {name}.\n"
                         f"¿Qué te gustaría recrear?")})


def build_input(a, key):
    inp = {"mode": "recreate", "video_url": as_url(a.video, "video")}
    if a.influencer and a.image:
        die("Use --influencer (your influencer) or --image (any photo, only with AI Studio), not both")
    if a.influencer:
        inf = resolve_influencer(a.influencer)
        inp.update({"source": "influencer", "influencer_id": inf["id"]})
        print(f"influencer: #{inf.get('number')} {inf.get('name')}", file=sys.stderr, flush=True)
    elif a.image:
        inp.update({"source": "image", "image_url": as_url(a.image, "image")})
    else:
        die("Say who goes in the video: --influencer <id|#number|name> (run `influencers`)")
    inp["quality"] = quality_of(a.quality or prefs()["quality"], key)
    inp["beauty"] = beauty_of(a.beauty or prefs()["beauty"])
    for k in ("prompt", "outfit"):
        v = getattr(a, k)
        if v:
            inp[k] = v
    if a.start is not None:
        inp["start_time"] = a.start
    if a.end is not None:
        inp["end_time"] = a.end
    if a.keep_engine_audio:
        inp["keep_original_audio"] = False
    if a.closed_eyes:
        inp["open_eyes"] = False
    return inp


def quote(slug, inp):
    """The price of the video in every tier with the user's token (an Instagram link is downloaded on the server)."""
    body = {k: v for k, v in inp.items() if k not in ("mode", "quality")}
    print("checking the video and the price…", file=sys.stderr, flush=True)
    q = call("POST", "/v1/influencer/videos/quote", body, timeout=600)
    key = slug.replace("influencer-video-", "")
    chosen = next((o for o in q["options"] if o["tier"] == key and o["quality"] == inp["quality"]), None)
    if not chosen or not chosen.get("available"):
        raise ContentError((chosen or {}).get("reason") or f"{NAMES[key]} cannot make this video")
    return {**chosen, "seconds": q.get("seconds"), "options": q["options"]}


def cmd_models(a):
    rows = []
    for key, slug in MODELS.items():
        m = call("GET", f"/api/v1/apis/catalog/{slug}", auth=False)
        m = m.get("model", m)
        prices = {p.get("variant", "").replace("quality=", ""): p.get("credits") for p in m.get("prices", []) if p.get("unit") == "second"}
        fixed = next((p.get("credits") for p in m.get("prices", []) if p.get("unit") == "request"), None)
        rows.append({"model": key, "slug": slug, "name": m.get("name"), "qualities": QUALITIES[key],
                     "credits_per_second": prices, "fixed_credits_per_video": fixed,
                     "description": m.get("description")})
    out(rows)


def cmd_quote(a):
    key, slug = model_of(a.model or prefs()["model"])
    inp = build_input(a, key)
    q = quote(slug, inp)
    credits = round(q["credits"])
    avail = [o for o in q["options"] if o.get("available") and o["tier"] == key]
    cheap = min(avail, key=lambda o: o["credits"]) if avail else None
    hd_opt = next((o for o in avail if o["quality"] == "1080p"), None)
    if inp["quality"] == "1080p" and cheap and cheap["quality"] != "1080p":
        quality_words = "en HD (1080p), la calidad más cara"
        alt = f" En {cheap['quality']} (la más barata y rápida) costaría {round(cheap['credits'])} créditos."
    elif inp["quality"] == "1080p":
        quality_words, alt = "en 1080p (la única calidad de Lite)", ""
    else:
        quality_words = f"en {inp['quality']} (la calidad más barata y rápida)"
        alt = f" En HD (1080p) costaría {round(hd_opt['credits'])} créditos, la más cara." if hd_opt else ""
    try:
        balance = call("GET", "/v1/credits").get("available")
    except ContentError:
        balance = None
    out({"model": key, "quality": inp["quality"], "beauty": inp["beauty"], "outfit": inp.get("outfit", "photo"),
         "extra_prompt": inp.get("prompt"),
         "seconds": q.get("seconds"), "credits": credits, "credits_available": balance,
         "enough_credits": balance is None or balance >= q["credits"],
         "first_time": not load_config().get("prefs"),
         "other_options": [{"model": o["tier"], "quality": o["quality"], "credits": round(o["credits"])}
                           for o in q["options"] if o.get("available")],
         "say_to_user": f"Este vídeo te costará {credits} créditos con el modelo {NAMES[key]} {quality_words} y "
                        f"{beauty_words(inp['beauty'])}{' y con tu indicación extra' if inp.get('prompt') else ''}.{alt} "
                        "¿Continúo así o quieres cambiar algo?",
         "input": inp})


def download_outputs(task, out_dir):
    files = (task.get("output") or {}).get("files") or []
    os.makedirs(out_dir, exist_ok=True)
    saved = []
    for i, f in enumerate(files, 1):
        ext = ".mp4" if "video" in (f.get("type") or "") else ".jpg"
        name = f"{task['id']}{'' if i == 1 else f'_{i}'}{ext}"
        path = os.path.join(out_dir, name)
        req = urllib.request.Request(f["url"], headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=600) as r, open(path, "wb") as fh:
            shutil.copyfileobj(r, fh)
        saved.append(path)
    return saved


def wait(task_id, out_dir, every=15, timeout=60 * 60):
    t0 = time.time()
    last = None
    while True:
        t = call("GET", f"/v1/influencer/videos/{task_id}")
        if t["status"] != last:
            print(f"[{int(time.time() - t0)}s] {t['status']}", file=sys.stderr, flush=True)
            last = t["status"]
        if t["status"] in ("succeeded", "failed"):
            break
        if time.time() - t0 > timeout:
            raise ContentError(f"Still {t['status']} after {timeout // 60} min: check later with `status {task_id}`")
        time.sleep(every)
    res = {"id": t["id"], "model": t["model"], "status": t["status"], "credits": t.get("credits"),
           "seconds": int(time.time() - t0)}
    if t["status"] == "succeeded":
        res["files"] = (t.get("output") or {}).get("files")
        notices = (t.get("output") or {}).get("notices") or []
        if notices:
            res["notices"] = notices
            if any(n.get("code") == "beauty_skipped" for n in notices):
                res["say_to_user"] = "No fue posible aplicar el mejorador de belleza a este vídeo."
        if out_dir:
            res["saved"] = download_outputs(t, out_dir)
    else:
        res["error"] = t.get("error")
    return res


def create(slug, inp, a):
    body = {"tier": slug.replace("influencer-video-", ""), **{k: v for k, v in inp.items() if k != "mode"}}
    if a.callback_url:
        body["callback_url"] = a.callback_url
    t = call("POST", "/v1/influencer/videos", body)
    print(f"task {t['id']} {t['status']} (credits held: {t.get('credits')})", file=sys.stderr, flush=True)
    if a.no_wait:
        out({"id": t["id"], "status": t["status"], "credits_held": t.get("credits")})
        return
    out(wait(t["id"], a.out))


def cmd_create(a):
    key, slug = model_of(a.model or prefs()["model"])
    inp = build_input(a, key)
    q = quote(slug, inp)
    print(f"{NAMES[key]} {inp['quality']}, beauty {inp['beauty']}: {round(q['credits'])} credits "
          "(charged only if it succeeds)", file=sys.stderr, flush=True)
    create(slug, inp, a)


def cmd_finalize(a):
    create(MODELS["ultra"], {"draft_task_id": a.task_id}, a)


def cmd_status(a):
    out(call("GET", f"/v1/influencer/videos/{a.task_id}"))


def cmd_wait(a):
    out(wait(a.task_id, a.out))


# ------------------------------------------------------------------ photos (recreate a photo with the influencer)
# POST /v1/influencer/recreations: the same photo (scene, pose, outfit, light) starring the influencer, made with
# Influencer Image (if one way refuses the photo, others are tried by themselves). «Not her» = the same photo with the original
# face and hair covered in green (once). Any member with their assigned influencers (admins: any of the community);
# charged to the connected user (~10 credits a photo). A single photo goes straight away; a carousel first
# asks which photos (the first, all or some) with the price.

IG_POST = ("instagram.com/p/", "instagram.com/reel/", "instagram.com/reels/", "instagram.com/tv/")
PHOTO_DONE = ("ready", "failed")
PHOTO_CREDITS = 10  # what a photo usually costs (6-15 credits; 13-nov-2026: average ~9)
POSTS_CACHE = os.path.join(os.path.dirname(CONFIG), "posts")


def read_post(url):
    """POST /v1/influencer/posts (free): the photos and videos of an Instagram post, already copied to the server.
    Cached for a day so asking «which photos?» and then making them reads the post only once."""
    os.makedirs(POSTS_CACHE, exist_ok=True)
    # (per community: the copies belong to the community the user is connected to)
    who = json.dumps(load_config().get("community"), sort_keys=True)
    key = os.path.join(POSTS_CACHE, hashlib.sha1((who + url.split("?")[0]).encode()).hexdigest() + ".json")
    try:
        if time.time() - os.path.getmtime(key) < 24 * 3600:
            with open(key) as f:
                return json.load(f)
    except (OSError, ValueError):
        pass
    post = call("POST", "/v1/influencer/posts", {"url": url}, timeout=300)
    with open(key, "w") as f:
        json.dump(post, f)
    return post


def carousel_say(photos, videos):
    n = len(photos)
    extra = f" y {len(videos)} vídeo{'s' if len(videos) > 1 else ''}" if videos else ""
    ask = ("¿Recreo solo la primera, solo la segunda o las dos?" if n == 2 else
           f"¿Recreo solo la primera, todas o alguna en concreto (por ejemplo, la 2 y la {n})?")
    each = ((content_prices() or {}).get("photo") or {}).get("credits") or PHOTO_CREDITS
    return (f"Este carrusel tiene {n} fotos{extra}. {ask} Cada foto cuesta unos {each} créditos "
            f"({'las dos' if n == 2 else f'las {n}'}, unos {n * each}) y solo se cobra si sale.")


def photo_items(value):
    """The `url` (an Instagram post) or the `items` (a photo file or https image) of a recreation."""
    if any(k in value for k in IG_POST):
        return {"url": value}
    return {"items": [{"kind": "image", "url": as_url(value, "photo")}]}


def photo_out(r):
    return {"id": r.get("id"), "status": r.get("status"), "engine": "Influencer Image",
            "face_covered": r.get("face_covered"), "result_url": r.get("result_url"),
            "original_url": r.get("original_url"), "credits": r.get("credits"), "error": r.get("error")}


def photo_wait(ids, out_dir, every=8, timeout=20 * 60):
    t0, last, done = time.time(), {}, {}
    while len(done) < len(ids):
        for i in ids:
            if i in done:
                continue
            r = call("GET", f"/v1/influencer/recreations/{i}")
            if r.get("status") != last.get(i):
                print(f"[{int(time.time() - t0)}s] {i[:8]} {r.get('status')}", file=sys.stderr, flush=True)
                last[i] = r.get("status")
            if r.get("status") in PHOTO_DONE:
                done[i] = r
        if len(done) < len(ids):
            if time.time() - t0 > timeout:
                raise ContentError(f"Still working after {timeout // 60} min: check later with `photo-status <id>`")
            time.sleep(every)
    res = []
    for i in ids:
        r = photo_out(done[i])
        if r["status"] == "ready" and out_dir and r.get("result_url"):
            os.makedirs(out_dir, exist_ok=True)
            path = os.path.join(out_dir, f"{i}.jpg")
            req = urllib.request.Request(r["result_url"], headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=300) as resp, open(path, "wb") as fh:
                shutil.copyfileobj(resp, fh)
            r["saved"] = path
        res.append(r)
    return res


def photos_say(res):
    ok = [r for r in res if r["status"] == "ready"]
    if not ok:
        return "No he podido recrear esta foto. ¿Probamos con otra?"
    n = len(ok)
    return (("Aquí tienes la foto" if n == 1 else f"Aquí tienes las {n} fotos") +
            ". ¿Te gusta? Si no se parece a ella, la rehago; si quieres cambiar algo, dime qué y lo corrijo.")


def cmd_photo(a):
    inf = resolve_influencer(a.influencer, catalog=True)
    print(f"influencer: #{inf.get('number')} {inf.get('name')}", file=sys.stderr, flush=True)
    if any(k in a.photo for k in IG_POST):
        # Read the post first (free): a single photo goes straight away; a carousel asks which photos (and the
        # price) unless --slides or --all already say it; a reel is a video (§4, with its quote)
        print("reading the post…", file=sys.stderr, flush=True)
        post = read_post(a.photo)
        items = post.get("items") or []
        photos = [i for i in items if i.get("kind") == "image"]
        videos = [i for i in items if i.get("kind") == "video"]
        if not photos:
            out({"kind": "video", "next": "This link is a video: make it with the video flow (§4, quote first)."})
            return
        if a.slides:
            want = {int(x) for x in a.slides.split(",") if x.strip()}
            picked = [i for i in photos if i.get("index") in want]
            if not picked:
                nums = [str(i["index"]) for i in photos]
                out({"error": "those slides are not photos", "photos": [i["index"] for i in photos],
                     "say_to_user": f"Las fotos de ese carrusel son la {', la '.join(nums[:-1])} y la {nums[-1]}. ¿Cuáles quieres?"
                     if len(nums) > 1 else "Ese carrusel solo tiene la foto 1. ¿La hago?"})
                return
        elif len(photos) == 1 or a.all:
            picked = photos
        else:
            out({"carousel": True, "photos": [i["index"] for i in photos], "videos": [i["index"] for i in videos],
                 "say_to_user": carousel_say(photos, videos),
                 "then": "photo --slides 1 | --slides 2,4 | --all (same link)"})
            return
        body = {"influencer_id": inf["id"], "kind": "image", "url": post.get("url") or a.photo,
                "items": [{"kind": "image", "url": i["url"], "cover_url": i.get("cover_url")} for i in picked]}
    else:
        body = {"influencer_id": inf["id"], "kind": "image", **photo_items(a.photo)}
    print("starting…", file=sys.stderr, flush=True)
    r = call("POST", "/v1/influencer/recreations", body, timeout=600)
    items = r.get("data") if isinstance(r, dict) and "data" in r else (r if isinstance(r, list) else [r])
    ids = [x["id"] for x in items if isinstance(x, dict) and x.get("id")]
    if not ids:
        raise ContentError("No photo to recreate in that post (is it a reel? use `create` for videos)")
    if a.no_wait:
        n = len(ids)
        out({"ids": ids, "status": "queued", "then": "photo-wait " + " ".join(ids),
             "say_to_user": "¡Voy! Te la paso en un par de minutos." if n == 1
             else f"¡Voy con las {n}! Te las paso en un par de minutos."})
        return
    res = photo_wait(ids, a.out)
    out({"photos": res, "say_to_user": photos_say(res)})


def photo_action(a, action, body=None):
    r = call("POST", f"/v1/influencer/recreations/{a.id}/{action}", body or {})
    if action == "approve":
        out({"approved": photo_out(r), "say_to_user": "Guardada en el contenido de tu influencer."})
        return
    new_id = r.get("id")
    print(f"new photo {new_id} ({action})", file=sys.stderr, flush=True)
    if a.no_wait:
        out({"id": new_id, "status": r.get("status")})
        return
    res = photo_wait([new_id], a.out)
    out({"photos": res, "say_to_user": photos_say(res)})


def cmd_photo_not_her(a):
    photo_action(a, "not-her")


def cmd_photo_fix(a):
    photo_action(a, "fix", {"text": a.text})


def cmd_photo_retry(a):
    photo_action(a, "retry")


def cmd_photo_approve(a):
    photo_action(a, "approve")


def cmd_photo_status(a):
    out(photo_out(call("GET", f"/v1/influencer/recreations/{a.id}")))


def cmd_photo_wait(a):
    res = photo_wait(a.id, a.out)
    out({"photos": res, "say_to_user": photos_say(res)})


# ------------------------------------------------------------------ CLI

def main():
    p = argparse.ArgumentParser(description="Influencer content: videos and photos with your influencer")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("welcome", help="first steps after connecting: influencers, credits and what fits in them")
    s.set_defaults(fn=cmd_welcome)
    s = sub.add_parser("influencer-photos", help="download the main photo, angles and settings of one influencer")
    s.add_argument("influencer", help="id, #number or name")
    s.add_argument("--out", default="./my-influencers")
    s.set_defaults(fn=cmd_influencer_photos)
    s = sub.add_parser("login")
    s.add_argument("--site", help="the web address where the user enters their community (a link to it is fine)")
    s.add_argument("--web", help=argparse.SUPPRESS)
    s.add_argument("--new", action="store_true", help="a new link even if one is still waiting")
    s.add_argument("--wait", type=int, default=90, help="seconds to wait for the person in this run (default 90)")
    s.add_argument("--client-id")
    s.set_defaults(fn=cmd_login)
    sub.add_parser("logout").set_defaults(fn=cmd_logout)
    sub.add_parser("whoami").set_defaults(fn=cmd_whoami)
    sub.add_parser("models").set_defaults(fn=cmd_models)
    sub.add_parser("influencers").set_defaults(fn=cmd_influencers)

    s = sub.add_parser("prefs", help="show or save the user's defaults for the next videos")
    s.add_argument("--model", help="lite | pro | ultra")
    s.add_argument("--beauty", help="on | off | low | medium | high")
    s.add_argument("--name", help="the user's first name, to call them by it")
    s.add_argument("--quality", help="normal (cheapest of the tier: Ultra 480p, Pro 720p; default) | hd (1080p, the most expensive)")
    s.add_argument("--reset", action="store_true")
    s.set_defaults(fn=cmd_prefs)

    s = sub.add_parser("upload")
    s.add_argument("file")
    s.set_defaults(fn=cmd_upload)

    for name, fn in (("quote", cmd_quote), ("create", cmd_create)):
        s = sub.add_parser(name)
        s.add_argument("--model", help="lite | pro | ultra (default: the user's, see `prefs`)")
        s.add_argument("--video", required=True, help="local file, https URL or Instagram reel/post link: the motion")
        s.add_argument("--influencer", help="your influencer: id, #number or name (run `influencers`)")
        s.add_argument("--image", help="any photo instead of an influencer (local file or https URL): only with AI Studio")
        s.add_argument("--quality", help="normal (default: Ultra 480p, Pro 720p) | hd (1080p, the most expensive) | 480p | 720p | 1080p")
        s.add_argument("--beauty", help="on | off | low | medium | high (default: the user's)")
        s.add_argument("--prompt", help="extra instruction, e.g. 'she wears sunglasses'")
        s.add_argument("--outfit", choices=["photo", "video"])
        s.add_argument("--start", type=float)
        s.add_argument("--end", type=float)
        s.add_argument("--keep-engine-audio", action="store_true", help="do not put the original audio back")
        s.add_argument("--closed-eyes", action="store_true", help="pro/ultra: do not draw the eyes open in the guide")
        if name == "create":
            s.add_argument("--out", default="./influencer-videos")
            s.add_argument("--no-wait", action="store_true")
            s.add_argument("--callback-url")
        s.set_defaults(fn=fn)

    s = sub.add_parser("finalize")
    s.add_argument("task_id")
    s.add_argument("--out", default="./influencer-videos")
    s.add_argument("--no-wait", action="store_true")
    s.add_argument("--callback-url")
    s.set_defaults(fn=cmd_finalize)
    s = sub.add_parser("photo", help="recreate a photo (Instagram post, file or URL) with the influencer")
    s.add_argument("--influencer", required=True, help="id, #number or name")
    s.add_argument("--photo", required=True, help="Instagram post/carousel link, a photo file or an https image")
    s.add_argument("--slides", help="only these photos of a carousel, e.g. 1,3 (1 = first)")
    s.add_argument("--all", action="store_true", help="every photo of a carousel (after the user said so)")
    s.add_argument("--out", default="./influencer-photos")
    s.add_argument("--no-wait", action="store_true")
    s.set_defaults(fn=cmd_photo)
    for name, fn in (("photo-not-her", cmd_photo_not_her), ("photo-retry", cmd_photo_retry),
                     ("photo-approve", cmd_photo_approve), ("photo-fix", cmd_photo_fix)):
        s = sub.add_parser(name)
        s.add_argument("id")
        if name == "photo-fix":
            s.add_argument("text", help="the correction, in any language")
        s.add_argument("--out", default="./influencer-photos")
        s.add_argument("--no-wait", action="store_true")
        s.set_defaults(fn=fn)
    for name, fn in (("photo-status", cmd_photo_status), ("photo-wait", cmd_photo_wait)):
        s = sub.add_parser(name)
        s.add_argument("id", nargs="+" if name == "photo-wait" else None)
        if name == "photo-wait":
            s.add_argument("--out", default="./influencer-photos")
        s.set_defaults(fn=fn)
    for name, fn in (("status", cmd_status), ("wait", cmd_wait)):
        s = sub.add_parser(name)
        s.add_argument("task_id")
        if name == "wait":
            s.add_argument("--out", default="./influencer-videos")
        s.set_defaults(fn=fn)

    a = p.parse_args()
    try:
        a.fn(a)
    except ContentError as e:
        # (for the agent: the error; for the user: only `say_to_user`, said as is)
        print(json.dumps({"error": str(e), "say_to_user": friendly(e)}, ensure_ascii=False), flush=True)
        die(str(e))
    except KeyboardInterrupt:
        die("Interrupted", 130)


if __name__ == "__main__":
    main()
