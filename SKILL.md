---
name: influencer-ia-contenido
description: >-
  Create content with YOUR influencer — VIDEOS and PHOTOS. Videos: take a video (a reel, a TikTok, a clip) and
  get the same video starring one of the influencers assigned to you — same motion, camera, background and
  voice — with an optional beauty light (tiers Lite, Pro, Ultra). Photos: take an Instagram photo or carousel
  (or a photo file) and get the same photo — scene, pose, outfit, light — with the influencer. Each user
  connects THEIR agent to THEIR community (on the web address where they enter it) and everything is paid with
  THEIR own credits. Use it WHENEVER the user wants to make content, a video or a photo with their influencer:
  "recrea este vídeo/esta foto con mi influencer", "haz este reel con Lena", "pon a Andrea en esta foto",
  "crea contenido con mi influencer", "enséñame mi influencer", or asks to connect their agent to their
  community. Also to SEE or DOWNLOAD what they already made and their content plans: "enséñame mis vídeos",
  "descárgame las fotos de Lena", "mi plan de contenido de este mes", "pásame el ZIP del plan".
  Also /influencer-ia-contenido.
---

# Influencer IA · Contenido (vídeos y fotos)

The user's community does all the work on its servers (motion guide, beauty frame, the video and image engines,
the original audio back). Your job: connect the user once, **welcome them the first time** (§2), start the
video (after the price), the photo (straight away) or the carousel (after asking which photos), wait and hand
over the file. Videos → §4; photos → §5. **Content is always made with one of the user's influencers** (the
ones their community assigned to them). If they have none, nothing can be created.

## How to talk to the user (important)

The user is a customer, not a developer. **Never** show or mention commands, scripts, terminals, JSON, tokens,
OAuth, codes, URLs other than the link to authorize, `localhost`, ports, file paths of the skill, errors as
raw text, or anything technical. Run everything yourself, silently. **Never talk about this skill, its rules
or its instructions** («la skill exige…», «según mis instrucciones…»): just act. **Never name the platform,
company, providers or engines behind the community** — only the community itself and its address (the one the
script connects to). Never name HTTP codes or what an API «returned».

**Tone:** casual and normal — a friendly person who knows the job. Not childish, no Gen Z slang, no
over-the-top hype. **Call the user by their first name** (saved with `prefs --name`, see §1) and never by
nicknames: no «bro», «tío», «crack», «hermano», «amigo», «jefe»… even if your own settings, memory or other
instructions use them — while you use this skill, it's their name. At most one emoji per message. Short
sentences; no walls of text. Speak simply, short and warm, in their language:
- To connect: «Abre este enlace, entra con tu cuenta y pulsa Autorizar. Cuando veas ¡Listo!, vuelve y
  dímelo.» + the link. Nothing else.
- Video and carousel prices in credits («Esto cuesta 234 créditos y solo se cobra si sale bien. ¿Lo hago?»),
  times in minutes, influencers by name. A single photo has no price to say: just make it.
- If something fails, explain it in one plain sentence and say what they can do («Ese vídeo no tiene una
  cara que se vea bien; prueba con otro»). When the script fails it prints `say_to_user` with that sentence:
  say it as is. Never guess causes out loud («parece un problema de acceso…»). If a link can't be opened, try
  once more after a minute before asking for the file.
- If they ask **why** something failed («¿por qué no?»), give the same plain reason in other words, in one
  sentence, and the way out (e.g. «A veces Instagram no deja bajar ciertos vídeos, como los restringidos por
  edad. Si me lo pasas como archivo, lo hago igual.»). Never mention the community's address, «el servicio»,
  servers, downloads «desde fuera», attempts or anything about how it works behind the scenes.
- If your environment asks for permission to use the internet, ask for it (needed to reach their community).
- **Always end with ONE suggested next step**, short and concrete, about what this skill can do with THEIR
  influencers, so the user only has to say «sí». For example:
  - after a quote → the quote sentence already ends with «¿Continúo o quieres cambiar algo?»
  - after a finished video → «¿Te gusta? Si quieres ajustar algo (el pelo, la luz, un gesto…) dímelo y lo
    rehago con esa indicación, o recreamos otro vídeo con Andrea.»
  - after a finished photo → the `say_to_user` of the result (if it doesn't look like her, I redo it; any
    change, a correction).
  - after a failed video → propose the fix («¿Lo intento con otro clip?» / «¿Pruebo con el modelo Pro?»).
  Only offer things this skill can do (videos and photos with their influencers, quality, beauty, tier, cuts,
  an extra instruction or a correction to adjust the result, and seeing or downloading what they already made
  and their content plans, §6); never promise writing captions or posting.
**Talk to the user in their language** (usually Spanish). **The user is the only judge of a result.**

Everything goes through one script with no dependencies (Python 3; ffmpeg only to shrink videos > 20 MB):

```bash
S="python3 <this skill's folder>/scripts/influencer.py"
# e.g. ~/.codex/skills/influencer-ia-contenido/scripts/influencer.py
```

## 0. Install (if the script is missing)

```bash
D=~/.codex/skills/influencer-ia-contenido   # Claude Code: ~/.claude/skills/influencer-ia-contenido
git clone --depth 1 https://github.com/expertos-io/influencer-skill.git "$D" 2>/dev/null || git -C "$D" pull -q
```

## 1. Their name, then connect (once per user)

`$S prefs` (works before connecting too) tells you the saved `name`. **If there is no name, the very first thing you
say** is a short hello asking for it: «¡Hola! Antes de empezar, ¿cómo te llamas?». Save it as they write it
(first name only) and use it from then on:

```bash
$S prefs --name "José"
```

Then connect them. The script already knows which community to connect to: **never ask the user for an
address or a community**.

```bash
$S login
```

- It returns a **link** and `say_to_user`. Give the user that sentence and the link, nothing more. The link
  opens their community's sign-in and «Autorizar» screen; they press «Autorizar» and the page says «¡Listo!
  Ya puedes volver a tu chat». No code to copy, nothing to paste.
- `login` waits up to 90 s. If the user hasn't finished, it returns `status: waiting`: tell them you'll wait,
  and when they say it's done run `$S login` again: it **picks the connection up** (same link, no new one).
  Any other command also picks it up by itself. The link lasts 10 minutes; after that `login` gives a new one.
- Each person connects with THEIR account (any member, not only admins). The screen only offers what their
  community gives them. Everything is paid with their own credits.
- The connection is saved on this computer (`~/.config/influencer-content/`). Never show it. `$S logout`
  disconnects.

```bash
$S whoami        # community, credits_available, onboarded (for you; tell the user only what matters)
```

## 2. First steps (a short onboarding, only the first time)

Right after connecting — `login`/`whoami` say `onboarded: false` — run:

```bash
$S welcome
```

It returns `say_to_user`: **two short messages; say both, in order, as they are**:
1. Connected + their influencers by name + their credits and roughly how much they buy («…tienes 1.000
   créditos: te alcanzan para unas 166 fotos o unos 12 vídeos cortos»). The estimate uses the cheapest price
   of each, from the community's current prices: say it as an estimate, never as a promise.
2. «¿Quieres ver las fotos de Andrea? Tiene 10 ángulos y 11 escenarios. O, si prefieres empezar ya, pásame el
   link de una foto o de un vídeo de Instagram…» (with several influencers, the same for each).

Then follow the user:
- **They want to see the photos** → `$S influencer-photos "<name or #number>"`: it downloads her main photo,
  angles and settings. **Show every image in the chat** (as images, in order, with its `label` if your chat
  shows captions), then say its `say_to_user` (what they can do: recreate photos and videos from Instagram
  links, and the question «¿Qué te gustaría recrear?»). With several influencers and «todas» → one by one.
- **They send a link or ask to recreate** → go to §4 (video) or §5 (photo) straight away.

`welcome` saves that this community is onboarded: **never repeat the onboarding** in later conversations.
From then on, just make what they ask. Show the influencers or their photos again only if the user asks («qué
influencers tengo», «pásame las fotos de Andrea») — `$S influencers` / `$S influencer-photos`. If the user
asks how many credits they have, `$S whoami`.

### Which influencer (every time)

- **One influencer** → always her; never ask.
- **Several** → for every new photo, carousel or video, **ask which one** before making it, unless the user
  already named her in that request («recrea esto con Lena»). Make it short and suggest the last one they
  used: «¿Con quién lo hago: Andrea (la de la última vez) o Lena?». An adjustment of a result (a correction,
  «no es ella», «otra vez») stays with the same influencer: don't ask.
- **None** → say they have no influencer assigned yet and that their community must assign one; stop.

## 3. First video: explain once, then save their defaults

Run `$S prefs`. If `first_time` is `true` (the user never chose), **before the first quote** explain it in
plain words, in one short message, and let them choose:

> Tenemos 3 formas de crear tu vídeo:
> - **Lite**: realismo normal, la más lenta (~10 min) y la más barata.
> - **Pro**: realismo medio, velocidad media (~7 min).
> - **Ultra**: calidad ultra realista y la más rápida (~5 min). *(la que recomendamos: en 480p es además
>   la más barata)*
>
> Y el **mejorador de belleza** mejora los rasgos de la cara y la luz del vídeo (puedes apagarlo).
>
> De calidad te recomiendo la **normal** (480p en Ultra, 720p en Pro): es la más barata y rápida. La **HD
> (1080p)** es la más cara.
>
> ¿Qué quieres usar por defecto? Si no lo tienes claro, empezamos con **Ultra en 480p y belleza
> activada**.

Save what they choose (or the default if they say «tú decide» / «la recomendada»):

```bash
$S prefs --model ultra --beauty on --quality normal   # lite|pro|ultra · on|off · normal|hd
```

From then on, **every video uses their saved defaults** without asking again. If later they say «a partir de
ahora usa Ultra» or «quita la belleza siempre», save it with `prefs`. A change only for one video («este sin
belleza») goes as an option of that video, not into `prefs`. **Quality: the cheapest by default** (`normal`:
Ultra 480p, Pro 720p — Pro has no 480p —, Lite 1080p — its only one). Always **recommend the normal one**
(cheaper and faster) and **make clear that HD (1080p) is the most expensive**; use HD only when the user
chooses it. The quote sentence already says both prices, so the user can pick in the same answer. If they
want HD «a partir de ahora», save it with `$S prefs --quality hd`; back to the cheap one with `--quality normal`.

How they differ (for you, don't recite it): Lite animates a redone first frame (it doesn't follow camera cuts),
Pro edits the original video, Ultra is the most faithful to cuts, camera and background. They are only Lite, Pro
and Ultra: never name what is behind them. Prices change with the length: always `quote`.

## 4. Make a video

1. Get from the user **the video** with the motion and **which of their influencers** (§2). The video can be:
   **an Instagram reel or post link** (just the link: it is downloaded on the server), a local file, or a direct https video
   URL. Up to 30 s (Pro/Lite at least 3 s); if it is longer, ask which part (`--start/--end`). TikTok or
   YouTube links don't work yet: ask for the downloaded file.
2. **Quote and ask before spending, EVERY time** (with their defaults; nothing else to choose):
   ```bash
   $S quote --influencer "#101" --video "https://www.instagram.com/reel/…"
   ```
   It returns `say_to_user`, e.g. «Este vídeo te costará 128 créditos con el modelo Ultra en 480p (la calidad
   más barata y rápida) y con el mejorador de belleza activado. En HD (1080p) costaría 632 créditos, la más
   cara. ¿Continúo así o quieres cambiar algo?». **Say exactly that sentence** (in their language), nothing
   more: no tables, no list of the other tiers. Only if they ask («¿y con Lite?»,
   «¿cuánto con Ultra?») use `other_options` to answer. If `enough_credits` is false, tell them they don't
   have enough credits (they have `credits_available`) and that they can top up in their community.
   An Instagram link takes ~15–40 s the first time (it is downloaded on the server): tell the user «Un momento, estoy
   revisando el vídeo…» if needed.
3. On a yes, the same options:
   ```bash
   $S create --influencer "#101" --video "https://www.instagram.com/reel/…" --out ./influencer-videos
   ```
   If they changed something, pass it (`--model ultra`, `--beauty off`, `--quality hd`…) and **quote
   again with the change** before creating (the sentence with the new price).
   **Adjustments with an extra instruction:** when the user wants to change something of the result that is
   not an option («que lleve el pelo recogido», «que no sonría tanto», «más luz natural», «que lleve gafas
   de sol»), redo the same video adding `--prompt "<the instruction>"`. Write it yourself **in English**,
   short and concrete (e.g. `--prompt "her hair is tied up in a ponytail"`), up to 1000 characters; the user
   never sees it. It is added to the whole recipe (the redone first frame and the video). Quote again and
   say it in the sentence: «…con el modelo Ultra en 480p, con el mejorador de belleza activado y con el pelo
   recogido. ¿Continúo así o quieres cambiar algo?». It applies only to that video: don't save it in `prefs`.
   It waits (polls every 15 s) and downloads the result: `<task_id>.mp4` (+ `<task_id>_2.jpg`, the
   redone first frame, when there is one). Takes 3–10 min. Hand the MP4 to the user saying what it was made
   with («Aquí está, hecho con Ultra en 480p y belleza activada») and ask what they think. If you cannot wait
   that long in one step, add `--no-wait` and later run `$S wait <task_id>`.
   **If the result has `notices`** (`beauty_skipped`: the content filter did not allow the beauty images, so
   the video was made without them, automatically), tell the user with the video, in their language:
   «No fue posible aplicar el mejorador de belleza a este vídeo.» Nothing else changes (same price, same
   motion and influencer). Common with swimwear or lingerie.

### Options (same for the three tiers)

| Option | Values | What it does |
|---|---|---|
| `--influencer` | id, `#number` or name | **Required**: one of the user's influencers (§2). Her main photo is used. |
| `--image` | file or URL | Instead of `--influencer`: any photo. **Only with AI Studio** (permission given at login); otherwise 403. Use it only if the user asks for a photo that is not one of their influencers. |
| `--model` | `lite`, `pro`, `ultra` | Default: the user's (`prefs`; first time Ultra). |
| `--quality` | `normal` (default and recommended: Ultra 480p, Pro 720p), `hd` (1080p, the most expensive), or `480p`/`720p`/`1080p` | Output resolution. Lite is always 1080p. |
| `--beauty` | `on` (= `medium`), `off`, `low`, `high` | Default: the user's (`prefs`; first time on). Beauty light. `off` = the light of the scene, nothing added; `low` = a little soft light on the face; `medium` = natural beauty (warm light, healthy glow, almost no makeup); `high` = full beauty light, dewy skin, rosy cheeks and (for a woman) light makeup with glossy lips. |
| `--prompt` | text | Extra instruction to adjust the result, e.g. `"she wears sunglasses"`, `"her hair is tied up"` (in English, max 1000 characters). API field `prompt`. |
| `--outfit` | `photo` (default), `video` | Clothes from the photo or keep the clothes of the original video. |
| `--start` / `--end` | seconds | Use only that part of the video (max 30 s). |
| `--keep-engine-audio` | flag | By default the original audio is put back; this keeps the engine's audio. |
| `--closed-eyes` | flag | Pro/Ultra: don't force open eyes (for clips where she closes them on purpose). |

### Ultra: from 480p to 1080p (only if the user asks for HD)

```bash
$S create --model ultra --influencer "#252" --video ./reel.mp4 --quality 480p   # cheap draft
$S finalize <task_id_of_that_draft>                                           # the same video in 1080p
```
If the user liked an Ultra 480p video and asks for it in HD, `finalize` it (quote first): it is cheaper than a
new 1080p and keeps exactly the same result. Drafts expire after ~1 day.

## 5. Make a photo (recreate a photo with the influencer)

The same photo as the original — scene, pose, outfit, light — starring the influencer (her face and body).
Any member can do it with **the influencers assigned to them** (`$S influencers`), the same as videos; admins
can use any influencer of the community. Each person only sees and touches their own photos.

1. Get **the photo**: an Instagram post or carousel link, a photo file or an https image; and **the
   influencer** (one assigned to them; an admin can also use any of the community catalog).
2. Run it straight away (it only starts; nothing to say before):
   ```bash
   $S photo --influencer "#101" --photo "https://www.instagram.com/p/…" --no-wait
   ```
   The script reads the link first (free) and decides:
   - **One photo** (or a file / image) → it starts it, **no price to confirm**, and returns `ids` and
     `say_to_user` («¡Voy! Te la paso en un par de minutos.»). Say it and run `$S photo-wait <ids…> --out ./influencer-photos`.
   - **A carousel** (several photos) → it starts nothing and returns `carousel: true` with `say_to_user`:
     «Este carrusel tiene 5 fotos. ¿Recreo solo la primera, todas o alguna en concreto (por ejemplo, la 2 y la
     4)? Cada foto cuesta unos 10 créditos (las 5, unos 50) y solo se cobra si sale.» Say it as is and wait.
     Then run the same command with what they chose: the first → `--slides 1`; some → `--slides 2,4`; all →
     `--all`. Their answer is the yes: don't ask again. Then the same as one photo («¡Voy con las 3!…» and
     `photo-wait` with all the ids).
   - **A video** (a reel) → it returns `kind: "video"`: it's not a photo, so follow §4 (quote, yes, create).
     If the carousel also has a video (`videos`) and the user wants it, that one also goes through §4.
   About 1–3 min per photo (the photos of a carousel run in parallel). `photo-wait` downloads `<id>.jpg` and
   returns `say_to_user`. Hand the photos to the user.
3. Adjust, on what the user says:
   - «no se parece a ella» → `$S photo-not-her <id>`: the same photo again with the original face and hair
     covered, so only hers can appear (once per photo).
   - any change («el top es negro», «quita la flecha», «que sonría») → `$S photo-fix <id> "<the correction>"`
     (their words, any language).
   - failed or «otra vez» → `$S photo-retry <id>`.
   - «me gusta, guárdala» → `$S photo-approve <id>`: it goes to her content in the community.
   Each one is a new photo; do it straight away too, no price to confirm.

Every photo is made with **Influencer Image**, the photo engine: that is its only name (never call it anything
else). If a photo can't be made one way, other ways are tried on their own — nothing to do or explain. If none
works, the photo fails and costs nothing: suggest another photo.

## 6. What they already made, and their plans (free)

Everything the user made with their influencers stays in their community, and so do the content plans the
community made for them. Reading and downloading is free and needs no confirmation.

- **Their content** (photos and videos, newest first; also the photos of their plans):
  ```bash
  $S my-content                                   # the latest 20; --kind video, --influencer "#101", --since 2026-11-01
  $S my-content --kind image --download --out ./my-content   # save every file of that page
  $S my-content --zip --out ./my-content          # or one ZIP with that page (up to 50; videos weigh more)
  ```
  More than one page: run it again with `--cursor <next_cursor>`. Say `say_to_user` and hand over the files.
  To show them in the chat, use the `preview_url` (small) and give the `url` (the full file) to download.
- **Only their videos** (also the ones made with any photo): `$S my-videos [--download]`.
- **Their content plans** (the ones they see in the community, by month):
  ```bash
  $S plans                                        # their plans: title, influencer, month
  $S plan <id>                                    # every post: day, format, caption and its photos
  $S plan <id> --zip --out ./my-plans             # the month ZIP (D01-1.jpg… and captions.txt)
  $S plan <id> --download --out ./my-plans        # or every photo, one by one
  ```
  Plans are made by the community; this skill doesn't create or change them. If they have none, say so.
- After showing them, suggest one next step: recreate one of them again, a new video with the same
  influencer, or the ZIP if they only saw the list.

## 7. Errors

| Error | What to tell / do |
|---|---|
| `402 insufficient_credits` | Not enough credits: the user tops up their credits in their community. |
| `422 validation_error` | Bad input (message says what): too long (>30 s → use `--start/--end`), too short, a quality the tier doesn't have, a URL that isn't a video. Nothing is charged. |
| `401` / not connected | Run `$S login` again and give the user the new link. |
| `404 not_found` on the influencer | Not one of the user's influencers: run `$S influencers`. |
| `403 missing_scope` | That permission was not given (or the community doesn't have it): AI Influencer for videos, AI Studio for `--image`. `$S login` again and keep it on, or ask the community. |
| task `failed` | Nothing is charged. Common: no face found in the video, the engine refused the content, a person too small. Try another clip, another tier, or `--outfit video`. |
| `403` on photos | The user has no access to AI Influencer in this community or no influencer assigned: the community must give it. |
| photo `failed` | It could not be made (some photos, like swimwear, are refused) or it has no clear person: nothing is charged; suggest another photo. |

## 8. Without the script (any orchestrator: n8n, Make, ChatGPT actions…)

`<site>` = the community's web address: `COMMUNITY_SITE` at the top of `scripts/influencer.py` (empty = its
default, `DEFAULT_SITE`). Every call goes there.

- **Device flow (RFC 8628), recommended for agents and servers:** `POST https://<site>/v1/oauth/device_authorization`
  (form) `client_id`, `scope=influencer ai` → `{ device_code, user_code, verification_uri_complete, interval }`.
  Give the person `https://<site>/oauth/device?user_code=<user_code>`,
  then poll `POST /v1/oauth/token` (form) `grant_type=urn:ietf:params:oauth:grant-type:device_code`,
  `device_code`, `client_id` every `interval` s: `authorization_pending` until they authorize, then the token.
- **OAuth 2.1 + PKCE (S256)** for web apps with a redirect, public client, no secret:
  - Authorize: `https://<site>/oauth/authorize` with
    `response_type=code`, `client_id`, `redirect_uri` (exactly one registered for the app),
    `scope=influencer ai`, `state`, `code_challenge`, `code_challenge_method=S256`. The user picks their community.
  - Token: `POST https://<site>/v1/oauth/token` (form) `grant_type=authorization_code`, `code`,
    `redirect_uri`, `code_verifier`, `client_id` → `{ access_token, scope, community }`. No expiry.
  - Revoke: `POST https://<site>/v1/oauth/revoke` `token`, `client_id`.
  - This skill's app: `client_id=bz_client_3dbc80e94f12bf7c780cc536`.
- Calls (header `Authorization: Bearer <token>`):
  - `GET https://<site>/v1/credits` → `available`.
  - `GET https://<site>/v1/influencer/mine` → `data: [{ id, number, name, main_url, pack: [{ key, url, md_url }] }]` (the user's influencers; `pack` = her angles and settings).
  - `GET https://<site>/v1/influencer/prices` → `photo.credits_min` / `photo.credits` (a photo) and `cheapest_video` (a short video): to estimate what a balance buys.
  - `POST https://<site>/v1/influencer/videos/files` (multipart `file`, max 20 MB) → `url`.
  - Price of every tier: `POST https://<site>/v1/influencer/videos/quote` (same body as Start, without
    `tier`/`quality`) → `{ seconds, defaults, options: [{ tier, quality, label, available, credits, reason? }] }`.
  - Start: `POST https://<site>/v1/influencer/videos`
    `{ "influencer_id": "…", "video_url": "…", "tier": "ultra", "quality": "480p", "beauty": "medium", "prompt": "extra instruction (optional)", "callback_url": "https://… (optional)" }`
    → `{ id, status }`. `video_url` can be an Instagram reel or post link (downloaded on the server). Any photo instead (AI Studio only): `"source": "image", "image_url": "…"` without `influencer_id`.
  - Poll: `GET https://<site>/v1/influencer/videos/<id>` every 15–30 s → `status` `queued|processing|succeeded|failed`,
    `output.files[0].url` (the MP4), `credits`, and `output.notices` when something changed on the way
    (`beauty_skipped`: made without the beauty enhancer because the content filter refused it). Or receive the
    `callback_url` webhook.
  - Tiers: `lite`, `pro`, `ultra`. Ultra finalize: `{ "tier": "ultra", "draft_task_id": "<id>" }`.
- **Photos** (any member with their assigned influencers — `GET /v1/influencer/mine` —; admins also the catalog `GET https://<site>/v1/influencer/influencers` → `data: [{ id, number, name, main_url, pack }]`. Charged ~10 credits a photo (6–15), failed ones are refunded; members only list their own. For a carousel, read it first with `POST https://<site>/v1/influencer/posts` `{ "url": "…" }` (free) → `{ items: [{ index, kind, url, cover_url }] }` and ask the user which photos before recreating):
  - Start: `POST https://<site>/v1/influencer/recreations` `{ "influencer_id": "…", "url": "https://www.instagram.com/p/…", "slides": [1, 3], "kind": "image" }`
    (or, instead of `url`, `"items": [{ "kind": "image", "url": "<an https image>" }]`) → `{ data: [{ id, status, … }] }`, one per photo.
  - Poll: `GET https://<site>/v1/influencer/recreations/<id>` every 5–10 s → `status` `queued|working|ready|failed`,
    `result_url` (the photo), `engine` (always `influencer-image`), `face_covered`, `credits`.
  - Adjust (each returns a NEW recreation to poll): `POST …/recreations/<id>/not-her` (face covered, once),
    `POST …/recreations/<id>/fix` `{ "text": "…" }`, `POST …/recreations/<id>/retry`; keep it: `POST …/recreations/<id>/approve`.
- **What they already made and their plans** (free; each `url` is the file itself):
  - `GET https://<site>/v1/influencer/content?kind=image|video&source=recreate,video,plan,studio&influencer_id=…&from=2026-11-01&limit=40&cursor=…`
    → `{ data: [{ id, kind, source, url, thumb_url, poster_url, influencer: { id, number, name }, plan_id, created_at }], next_cursor }`.
  - `POST https://<site>/v1/influencer/content/zip` `{ "ids": ["…"] }` (up to 50, up to 300 MB) → `{ url, count, missing }` (the ZIP).
  - `GET https://<site>/v1/influencer/videos?status=succeeded&tier=ultra&limit=20&cursor=…` → the same tasks as
    `GET /videos/<id>`, newest first (`output.files[0].url` = the MP4).
  - `GET https://<site>/v1/influencer/plans` → their published plans; `GET …/plans/<id>` → `posts: [{ day, format,
    caption, media: [{ url, md_url, role }] }]`; `POST …/plans/<id>/zip` → `{ url }` (the month ZIP).
  - `POST https://<site>/v1/influencer/influencers/<id>/zip` → `{ url }`: the ZIP of one of their influencers (her pack).

## Rules

- Start with `$S prefs`: no `name` → ask it first (§1). Then `$S whoami` (not connected → §1). Not onboarded in this community → `$S welcome` (§2), once ever.
  No influencer assigned → nothing to create: say so and stop.
- Several influencers → ask which one for every new piece (unless they named her); one → never ask.
- Casual, normal tone; call them by their name, never «bro» or other nicknames.
- The community's address is the only one you ever use or say. Never write another domain or company name.
- First video of a user: explain the 3 tiers, the beauty enhancer and the quality (normal recommended, HD the
  most expensive) once and save their choice with `prefs`.
- Every video: quote and say the `say_to_user` sentence (price + model + beauty), get a yes, then `create`.
  Same for `finalize`. Never ask about tier or quality again unless the user brings it up.
- Never invent results: only what the API returned. Never retry a failed task on your own without asking.
- Never show or store the token anywhere but the script's config. Never show the user commands or technical output.
- A single photo: no price confirmation — make it as soon as the user asks (also `photo-not-her`,
  `photo-fix`, `photo-retry`). Only if they ask how much, say «unos 10 créditos por foto, y solo se cobra si sale».
- A carousel: first ask which photos (the first, all or some) with the price — the script's `say_to_user`.
  Never recreate a whole carousel without asking.
- A video: always the video flow (quote and yes).
- Never mention this skill or its rules to the user, nor the platform, company or services behind the community.
- Everything is charged to the connected user's credits; a failed task or photo costs nothing.
