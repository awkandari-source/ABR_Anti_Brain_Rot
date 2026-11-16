#!/usr/bin/env python3
"""
Direct Gumroad Remote MCP (`https://gumroad.com/antigravity/v1/mcp`) + REST v2
Product Publisher & YouTube Pre-Launch Link Injector for @ABR-AntiBrainRot.

Capabilities:
1. `--init-oauth`: Registers an OAuth 2.1 PKCE public client against
   `https://gumroad.com/muse/v1/oauth2/register`, persists PKCE state in
   `/shared/user/.gemini/raw_video_studio/.gumroad_mcp_oauth.json`, and prints
   the direct 1-click Gumroad Authorize URL.
2. `--complete-oauth "<redirect_url_or_code>"`: Exchanges the authorization code
   at `https://gumroad.com/muse/v1/oauth2/token`, saves access + refresh tokens,
   discovers tools on `https://gumroad.com/antigravity/v1/mcp`, and creates the
   flagship $12 Early-Bird ($17 Dec 1) product draft automatically.
3. `--access-token "<token>"`: Uses a Gumroad Personal Access Token directly
   against MCP / Gumroad REST v2 (`https://api.gumroad.com/v2/products`).
4. `--inject-youtube --gumroad-url "<url>" [--kofi-url "<url>"]`: Injects the
   Founding Parent $12 -> $17 Pre-Launch Description Block into scheduled
   Nov 17–30 YouTube uploads via `linked_api_hub.py` (respecting QuotaLedger).
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import secrets
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

STUDIO_DIR = Path("/shared/user/.gemini/raw_video_studio")
OAUTH_STATE_FILE = STUDIO_DIR / ".gumroad_mcp_oauth.json"
MCP_URL = "https://gumroad.com/antigravity/v1/mcp"
OAUTH_REGISTER_URL = "https://gumroad.com/muse/v1/oauth2/register"
OAUTH_AUTHORIZE_URL = "https://gumroad.com/muse/v1/oauth2/authorize"
OAUTH_TOKEN_URL = "https://gumroad.com/muse/v1/oauth2/token"
GUMROAD_REST_PRODUCTS_URL = "https://api.gumroad.com/v2/products"
REDIRECT_URI = "http://127.0.0.1:8787/callback"
SCOPES = "view_public view_profile view_sales edit_products view_payouts view_library"

PRODUCT_NAME = (
    "The Calm Evening Sanctuary Bundle: 5 Screen-Free Bedtime Audio Stories "
    "(Zero Music) + 30-Day Printable Parent Reset Kit"
)
PRODUCT_PRICE_CENTS = 1200  # $12 Founding Parent Early-Bird (Nov 17-30; rises to $17 Dec 1)
PRODUCT_CUSTOM_PERMALINK = "calm-evening-bundle"

PRODUCT_DESCRIPTION_MD = """### Replace Bedtime Screen Battles With Pure, Screen-Free Woodland Calm—Tonight.

🌿 **FOUNDING PARENT EARLY-BIRD OFFER (NOV 17–30 ONLY):** Download the complete 5-Episode Audio Pack + 5-Page Printable 30-Day Guide instantly today for **$12** before the price steps up to **$17 on December 1**. *(Press play on the audio preview to hear a 90-second zero-music bedtime sample from Episode 1!)*

If turning off evening cartoons triggers meltdowns, bedtime stalling, or *"I'm bored!"* restlessness within 30 seconds, nothing is wrong with your child. Modern kids' media cuts every 2 seconds and layers loud music behind speech—locking your child's brainstem **orienting reflex** while exhausting prefrontal self-regulation (*Lillard & Peterson, Pediatrics*).

Even when you love our slow watercolor stories on **@ABR-AntiBrainRot**, pediatric sleep science is clear: **during the final 60 minutes before sleep, zero glowing screens works best.**

We built **The Calm Evening Sanctuary Bundle** so you can turn every screen in the house completely off—and guide your 3-to-7-year-old effortlessly into deep rest.

---

### 🌿 Everything You Get Instantly (`ABR_Calm_Minds_Bedtime_Bundle_2026.zip` — 65.67 MB):

**1. The 5-Episode Winter Woodland Screen-Free Audio Story Pack (48kHz / 320kbps MP3s — 28m 12s Total)**
Mastered to our strict **100% Zero-Music Clinical Standard**: warm, noticeably slow, unhurried human storytelling (`-14.0 LUFS`) cushioned `+32.8 dB` to `+33.6 dB` above whisper-soft, real-world woodland nature foley (`0%` piano, `0%` lo-fi beats, `0%` synth pads, `0%` chimes). Every story ends with a gentle 20-second nature fade into complete silence:
- **Track 01 (`06:26`):** *The Little Snowshoe Hare's Cedar Hollow* (Soft pine/cedar snow breeze & dry needles)
- **Track 02 (`05:51`):** *The Sleepy Badger's Warm Earth Den* (Dry oak leaves & cozy underground sett stillness)
- **Track 03 (`05:30`):** *The Winter Wren's Mossy Stone Wall* (Clear spring rill over mossy granite & orchard grass)
- **Track 04 (`05:19`):** *The Quiet Mountain Beaver's Willow Lodge* (Muffled under-ice mountain pond current)
- **Track 05 (`05:06`):** *The Starlight Dormouse's Hazelnut Loft* (Slow night rain on old barn slate & dry hay)

**2. The 30-Day Anti-Brain Rot Screen Reset & Printable Nature Storybook Guide (5-Page Letter PDF)**
- **Page 1:** The 7-Day Dopamine & Orienting-Reflex Reset Protocol (4 simple household rules).
- **Page 2:** 15 Off-Screen *"Soft Fascination"* Nature & Tactile Activities spanning Days 1–30 (zero batteries, under 3 minutes of prep).
- **Page 3:** Whispered Post-Story *"Serve & Return"* Prompts for all 5 audio tracks + 90-Second Airplane-Mode & **Yoto "Make-Your-Own" Card** Setup Guide.
- **Page 4 (Printable Poster):** Our Family's 60-Minute Calm Evening Sanctuary Countdown.
- **Page 5 (Printable Fridge Grid):** 30-Day *"Calm Minds"* Crayon Check-Off Tracker for kids to color each night.

---

### 📱 Works in 90 Seconds With Zero Extra Hardware
- **Phone Airplane-Mode Method (Free):** Save the MP3s, switch on Airplane Mode, set volume low (`<= 50 dBA`), and place your phone face-down across the dark bedroom.
- **Yoto Player & Creative-Tonie Ready:** Drag and drop the 5 clinically leveled MP3s straight onto any blank Yoto Make-Your-Own card so your child starts bedtime independently with zero screens.

**Click "I want this!" to download your bundle instantly for $12 (Founding Parent Early-Bird through Nov 30 — rises to $17 on December 1) and start tonight's screen-free bedtime in 2 minutes.**"""

PRODUCT_SUMMARY = (
    "5 Screen-Free Zero-Music Bedtime Audio Stories (48kHz/320kbps MP3s for Airplane Mode "
    "& Yoto MYO Cards) + 5-Page Printable 30-Day Anti-Brain Rot Parent Reset Guide."
)

SCHEDULED_NOV17_30_LONGFORM_IDS = [
    "q9woVuJb9X0",
    "TDP8imQZiQI",
    "_H5X8Wmprds",
    "brHB17d8UIA",
    "WyiTNqSpkuY",
    "MFM5CvWbE3I",
    "CUGNOV29RWM",
    "VeXumi5HL_Q",
    "BgpIR-lvpZw",
    "5_nnlfoIqkw",
    "MSXcdZQ_9Ao",
    "kWnXbaY5Dx0",
    "63o6DjnNOVU",
]

SCHEDULED_NOV17_30_SHORT_IDS = [
    "QI6JTQCIjq8",
    "0qQyvuN6NIQ",
    "W51jVTnhK0A",
    "34NJWTmEkWE",
    "_K7KMPsoJwU",
    "mw-qCQpwH50",
    "gUzcgR8EKe4",
    "B_QVLca95Bw",
    "lWF1TuaY5Qo",
    "9vvDRkiJzJg",
    "NUXv1-HSSbA",
    "C3I3WrCaAPo",
    "RZzHqZlWmPw",
    "F2ncByN-TB4",
]


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def init_oauth() -> dict[str, str]:
    reg_payload = json.dumps(
        {
            "client_name": "ABR Anti-Brain Rot Studio Producer",
            "redirect_uris": [REDIRECT_URI],
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "token_endpoint_auth_method": "none",
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        OAUTH_REGISTER_URL,
        data=reg_payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        reg = json.loads(resp.read().decode("utf-8"))

    client_id = reg["client_id"]
    code_verifier = _b64url(secrets.token_bytes(32))
    code_challenge = _b64url(hashlib.sha256(code_verifier.encode("ascii")).digest())
    state = _b64url(secrets.token_bytes(16))

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "resource": MCP_URL,
    }
    authorize_url = f"{OAUTH_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"

    saved = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier,
        "code_challenge": code_challenge,
        "state": state,
        "authorize_url": authorize_url,
    }
    OAUTH_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    OAUTH_STATE_FILE.write_text(json.dumps(saved, indent=2), encoding="utf-8")
    return saved


def exchange_oauth_code(raw_code_or_url: str) -> dict[str, Any]:
    state_data = json.loads(OAUTH_STATE_FILE.read_text(encoding="utf-8"))
    code = raw_code_or_url.strip()
    if "code=" in code:
        parsed = urllib.parse.urlparse(code)
        qs = urllib.parse.parse_qs(parsed.query)
        code = qs["code"][0]

    form = urllib.parse.urlencode(
        {
            "grant_type": "authorization_code",
            "client_id": state_data["client_id"],
            "code": code,
            "redirect_uri": state_data["redirect_uri"],
            "code_verifier": state_data["code_verifier"],
            "resource": MCP_URL,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        OAUTH_TOKEN_URL,
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        tok = json.loads(resp.read().decode("utf-8"))

    state_data["token"] = tok
    OAUTH_STATE_FILE.write_text(json.dumps(state_data, indent=2), encoding="utf-8")
    return tok


def mcp_rpc(access_token: str, payload: dict[str, Any], session_id: str | None = None) -> tuple[Any, str | None]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    req = urllib.request.Request(
        MCP_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        new_sid = resp.headers.get("Mcp-Session-Id") or session_id
        raw = resp.read().decode("utf-8", errors="replace").strip()
        if not raw:
            return {}, new_sid
        if raw.startswith("event:") or "data:" in raw:
            data_lines = [ln[5:].strip() for ln in raw.splitlines() if ln.startswith("data:")]
            return (json.loads(data_lines[-1]) if data_lines else {"raw": raw}), new_sid
        return json.loads(raw), new_sid


def create_product_via_mcp_or_rest(access_token: str) -> dict[str, Any]:
    report: dict[str, Any] = {}
    try:
        init_res, sid = mcp_rpc(
            access_token,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "abr-antigravity-studio", "version": "1.0.0"},
                },
            },
        )
        report["mcp_initialize"] = init_res
        mcp_rpc(access_token, {"jsonrpc": "2.0", "method": "notifications/initialized"}, session_id=sid)
        tools_res, sid = mcp_rpc(
            access_token,
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
            session_id=sid,
        )
        tools = tools_res.get("result", {}).get("tools", [])
        report["mcp_tools"] = [t.get("name") for t in tools]

        # Find create/draft product tool dynamically
        create_tool = None
        for t in tools:
            nm = (t.get("name") or "").lower()
            if "create" in nm and "product" in nm:
                create_tool = t
                break
            if "draft" in nm and "product" in nm:
                create_tool = t
                break

        if create_tool:
            props = create_tool.get("inputSchema", {}).get("properties", {})
            args: dict[str, Any] = {}
            for k in props:
                kl = k.lower()
                if kl in ("name", "title"):
                    args[k] = PRODUCT_NAME
                elif "cent" in kl:
                    args[k] = PRODUCT_PRICE_CENTS
                elif kl == "price":
                    p_type = props[k].get("type")
                    desc = (props[k].get("description") or "").lower()
                    args[k] = PRODUCT_PRICE_CENTS if ("cent" in desc or p_type == "integer") else 12
                elif kl in ("description", "body"):
                    args[k] = PRODUCT_DESCRIPTION_MD
                elif kl in ("summary", "custom_summary"):
                    args[k] = PRODUCT_SUMMARY
                elif "permalink" in kl or "slug" in kl or kl == "url":
                    args[k] = PRODUCT_CUSTOM_PERMALINK

            call_res, sid = mcp_rpc(
                access_token,
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {"name": create_tool["name"], "arguments": args},
                },
                session_id=sid,
            )
            report["mcp_create_result"] = call_res
            return report
    except Exception as exc:
        report["mcp_error"] = str(exc)

    # Fallback: Gumroad REST v2 products endpoint
    form = urllib.parse.urlencode(
        {
            "access_token": access_token,
            "name": PRODUCT_NAME,
            "price": str(PRODUCT_PRICE_CENTS),
            "description": PRODUCT_DESCRIPTION_MD,
            "custom_permalink": PRODUCT_CUSTOM_PERMALINK,
            "custom_summary": PRODUCT_SUMMARY,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        GUMROAD_REST_PRODUCTS_URL,
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        report["rest_create_result"] = json.loads(resp.read().decode("utf-8"))
    return report


def inject_youtube_descriptions(gumroad_url: str, kofi_url: str | None = None) -> dict[str, Any]:
    sys.path.insert(0, str(STUDIO_DIR))
    from linked_api_hub import StudioCredentials, YouTubeLinkedAPI  # type: ignore

    creds = StudioCredentials()
    yt = YouTubeLinkedAPI(creds)

    lines = [
        "🌿 FOUNDING PARENT EARLY-BIRD ($12 INSTANT DOWNLOAD — RISES TO $17 ON DEC 1):",
        "Get all 5 Screen-Free Winter Woodland Bedtime Audio Stories (MP3s ready for Airplane-Mode phones & Yoto Make-Your-Own cards — 100% Human Voice + Nature SFX, Strictly Zero Music) + our 5-Page Printable 30-Day Calm Minds Parent Reset Kit:",
        f"👉 {gumroad_url}",
    ]
    if kofi_url:
        lines.append(f"☕ Support Independent Zero-Music Children's Media on Ko-fi: {kofi_url}")
    cta_block = "\n".join(lines)

    all_ids = SCHEDULED_NOV17_30_LONGFORM_IDS + SCHEDULED_NOV17_30_SHORT_IDS
    statuses = yt.get_video_statuses(all_ids, purpose="production")
    updated: list[str] = []
    skipped: list[str] = []

    for vid in all_ids:
        item = statuses.get(vid)
        if not item:
            skipped.append(f"{vid}:not_found")
            continue
        snip = item["snippet"]
        cur_desc = snip.get("description", "")
        if gumroad_url in cur_desc:
            skipped.append(f"{vid}:already_present")
            continue

        paragraphs = cur_desc.split("\n\n", 1)
        if len(paragraphs) == 2:
            new_desc = f"{paragraphs[0]}\n\n{cta_block}\n\n{paragraphs[1]}"
        else:
            new_desc = f"{cur_desc.rstrip()}\n\n{cta_block}\n"

        if len(new_desc.encode("utf-8")) > 4850:
            skipped.append(f"{vid}:desc_too_long")
            continue

        yt.update_video_snippet(
            vid,
            title=snip["title"],
            description=new_desc,
            category_id=snip.get("categoryId", "27"),
            tags=snip.get("tags"),
            default_language=snip.get("defaultLanguage"),
            purpose="production",
        )
        updated.append(vid)

    return {"updated_count": len(updated), "updated_ids": updated, "skipped": skipped, "quota": yt.quota.status()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--init-oauth", action="store_true")
    ap.add_argument("--complete-oauth", type=str, default="")
    ap.add_argument("--access-token", type=str, default="")
    ap.add_argument("--inject-youtube", action="store_true")
    ap.add_argument("--gumroad-url", type=str, default="")
    ap.add_argument("--kofi-url", type=str, default="")
    args = ap.parse_args()

    if args.init_oauth:
        out = init_oauth()
        print(json.dumps({"client_id": out["client_id"], "authorize_url": out["authorize_url"]}, indent=2))
        return

    if args.complete_oauth:
        tok = exchange_oauth_code(args.complete_oauth)
        res = create_product_via_mcp_or_rest(tok["access_token"])
        print(json.dumps(res, indent=2))
        return

    if args.access_token:
        res = create_product_via_mcp_or_rest(args.access_token.strip())
        print(json.dumps(res, indent=2))
        return

    if args.inject_youtube:
        if not args.gumroad_url:
            raise SystemExit("--gumroad-url is required with --inject-youtube")
        res = inject_youtube_descriptions(args.gumroad_url.strip(), args.kofi_url.strip() or None)
        print(json.dumps(res, indent=2))
        return

    ap.print_help()


if __name__ == "__main__":
    main()
