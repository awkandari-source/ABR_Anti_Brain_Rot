#!/usr/bin/env python3
"""
End-to-end Gumroad Storefront Publisher via Official Gumroad Remote MCP
(`https://gumroad.com/antigravity/v1/mcp`) for @ABR-AntiBrainRot.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

PACK_DIR = Path("/home/antigravity/awkandari-source/ABR_Anti_Brain_Rot/December_2026_Launch_Pack")
AUDIO_DIR = PACK_DIR / "Mastered_Audio_Episodes"
COVER_DIR = Path("/tmp/gumroad_covers")
REPO_DIR = Path("/home/antigravity/awkandari-source/ABR_Anti_Brain_Rot")

sys.path.insert(0, str(PACK_DIR))
from gumroad_mcp_bridge import OAUTH_STATE_FILE, mcp_rpc  # type: ignore

TEMP_TAG = "v0.0.1-gumroad-s3-ingest"
REPO_SLUG = "awkandari-source/ABR_Anti_Brain_Rot"

BUNDLE_HTML = """<p><strong>🌿 FOUNDING PARENT EARLY-BIRD OFFER (NOV 17–30 ONLY):</strong> Download the complete 5-Episode Zero-Music Bedtime Audio Pack + 5-Page Printable 30-Day Parent Reset Kit instantly today for <strong>$12</strong> before the price steps up to <strong>$17 on December 1</strong>.</p>

<p>If turning off evening cartoons triggers meltdowns, bedtime stalling, or <em>"I'm bored!"</em> restlessness within 30 seconds, nothing is wrong with your child. Modern kids' media cuts every 2 seconds and layers constant music behind speech—locking your child's brainstem <strong>orienting reflex</strong> while exhausting prefrontal self-regulation (<em>Lillard &amp; Peterson, Pediatrics</em>; <em>McMillan &amp; Saffran, Child Development</em>).</p>

<p>Even when your family loves our slow 20-second watercolor stories on <strong>@ABR-AntiBrainRot</strong>, pediatric sleep science is clear: <strong>during the final 60 minutes before sleep, zero glowing screens works best.</strong></p>

<p>We built <strong>The Calm Evening Sanctuary Bundle</strong> so you can turn every screen in the house completely off—and guide your 3-to-7-year-old effortlessly into deep rest tonight.</p>

<hr>

<h3>1. The 5-Episode Winter Woodland Screen-Free Audio Story Pack (48kHz / 320kbps MP3s — 28m 12s Total)</h3>
<p>Mastered to our strict <strong>100% Zero-Music Clinical Standard</strong>: warm, noticeably slow, unhurried human storytelling (<code>-14.0 LUFS</code>) cushioned <strong>+32.8 dB to +33.6 dB</strong> above whisper-soft, real-world woodland nature foley (0% piano, 0% lo-fi beats, 0% synth pads, 0% chimes). Every story ends with a gentle 20-second nature fade into complete silence:</p>
<ul>
  <li><strong>Track 01 (06:26):</strong> <em>The Little Snowshoe Hare's Cedar Hollow</em> — Soft pine &amp; cedar snow breeze (+32.88 dB voice clarity)</li>
  <li><strong>Track 02 (05:51):</strong> <em>The Sleepy Badger's Warm Earth Den</em> — Dry oak leaves &amp; cozy underground sett stillness (+32.77 dB voice clarity)</li>
  <li><strong>Track 03 (05:30):</strong> <em>The Winter Wren's Mossy Stone Wall</em> — Clear spring rill over mossy granite &amp; orchard grass (+32.88 dB voice clarity)</li>
  <li><strong>Track 04 (05:19):</strong> <em>The Quiet Mountain Beaver's Willow Lodge</em> — Muffled under-ice mountain pond current (+32.78 dB voice clarity)</li>
  <li><strong>Track 05 (05:06):</strong> <em>The Starlight Dormouse's Hazelnut Loft</em> — Slow night rain on old barn slate &amp; dry hay (+33.55 dB voice clarity)</li>
</ul>

<h3>2. The 30-Day Anti-Brain Rot Screen Reset &amp; Printable Nature Storybook Guide (5-Page Letter PDF)</h3>
<ul>
  <li><strong>Page 1:</strong> The 7-Day Dopamine &amp; Orienting-Reflex Reset Protocol (4 simple household rules).</li>
  <li><strong>Page 2:</strong> 15 Off-Screen <em>"Soft Fascination"</em> Nature &amp; Tactile Invitations spanning Days 1–30 (zero batteries, under 3 minutes of prep).</li>
  <li><strong>Page 3:</strong> Whispered Post-Story <em>"Serve &amp; Return"</em> Prompts for all 5 audio tracks + 90-Second Airplane-Mode &amp; <strong>Yoto Make-Your-Own Card</strong> Setup Guide.</li>
  <li><strong>Page 4 (Printable Poster):</strong> Our Family's 60-Minute Calm Evening Sanctuary Countdown.</li>
  <li><strong>Page 5 (Printable Fridge Grid):</strong> 30-Day <em>"Calm Minds"</em> Crayon Check-Off Tracker for kids to color each evening.</li>
</ul>

<hr>

<h3>Works in 90 Seconds With Zero Extra Hardware</h3>
<ul>
  <li><strong>Phone Airplane-Mode Method (Free):</strong> Save or stream the individual MP3s, switch on Airplane Mode, set volume low (&le; 50 dBA at 2 meters), and place your phone face-down across the dark bedroom.</li>
  <li><strong>Yoto Player &amp; Creative-Tonie Ready:</strong> Drag and drop the 5 clinically leveled MP3s straight onto any blank Yoto Make-Your-Own card so your child starts bedtime independently with zero screens.</li>
</ul>

<p><strong>Click "I want this!" to download all 5 individual MP3s, the 5-Page Printable PDF, and the all-in-one ZIP archive instantly for $12 (Founding Parent Early-Bird through Nov 30 — rises to $17 on December 1).</strong></p>"""

CLUB_HTML = """<p><strong>Keep Children's Bedtimes &amp; Curious Minds 100% Zero-Music and Brain-Rot Free.</strong></p>

<p>Every bedtime story, 3-hour dark-screen sleep sanctuary, and pediatric neuroscience documentary on <strong>@ABR-AntiBrainRot</strong> is crafted with 20-second hand-painted holds, unhurried human narration, real-world nature foley, and <strong>strictly 0% background music</strong>.</p>

<h3>What You Receive as a Quiet Woodland Club Supporter ($5/month — Cancel Anytime):</h3>
<ul>
  <li><strong>Instant Welcome Download Today:</strong> Full zero-music MP3 of <em>The Little Snowshoe Hare's Cedar Hollow</em> (06:26, 48kHz/320kbps — Airplane-Mode &amp; Yoto MYO ready) + our <strong>5-Page Printable 30-Day Calm Minds Family Reset Kit (PDF)</strong>.</li>
  <li><strong>Monthly Member Drop (1st of Every Month):</strong> 1 brand-new downloadable Screen-Free Bedtime Audio Story MP3 (100% Voice + Organic Nature SFX, Zero Music) + 1 Printable Seasonal Nature Activity Sheet.</li>
  <li><strong>Direct Studio Support:</strong> Directly funds peer-reviewed pediatric science synthesis and non-looped nature recordings with zero noisy toy ads.</li>
</ul>"""


def call_tool(tok: str, sid: str | None, req_id: int, name: str, arguments: dict) -> tuple[dict, str | None]:
    res, new_sid = mcp_rpc(
        tok,
        {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments},
        },
        session_id=sid,
    )
    if "error" in res:
        raise RuntimeError(f"MCP tool {name} failed: {json.dumps(res['error'])}")
    if res.get("result", {}).get("isError"):
        raise RuntimeError(f"MCP tool {name} returned isError: {json.dumps(res['result'])}")
    sc = res.get("result", {}).get("structuredContent")
    if sc is None:
        txt = res.get("result", {}).get("content", [{}])[0].get("text", "{}")
        sc = json.loads(txt)
    return sc, new_sid


def main() -> None:
    st = json.loads(OAUTH_STATE_FILE.read_text(encoding="utf-8"))
    tok = st["token"]["access_token"]

    assets_to_stage = [
        COVER_DIR / "bundle_cover_1280x720.png",
        COVER_DIR / "club_cover_1280x720.png",
        PACK_DIR / "Calm_Minds_30_Day_Anti_Brain_Rot_Parent_Kit_Printable.pdf",
        AUDIO_DIR / "01_The_Little_Snowshoe_Hares_Cedar_Hollow_ZeroMusic.mp3",
        AUDIO_DIR / "02_The_Sleepy_Badgers_Warm_Earth_Den_ZeroMusic.mp3",
        AUDIO_DIR / "03_The_Winter_Wrens_Mossy_Stone_Wall_ZeroMusic.mp3",
        AUDIO_DIR / "04_The_Quiet_Mountain_Beavers_Willow_Lodge_ZeroMusic.mp3",
        AUDIO_DIR / "05_The_Starlight_Dormouses_Hazelnut_Loft_ZeroMusic.mp3",
        PACK_DIR / "ABR_Calm_Minds_Bedtime_Bundle_2026.zip",
    ]
    for p in assets_to_stage:
        assert p.exists(), f"Missing asset: {p}"

    staging_git = Path("/tmp/gumroad_s3_staging")
    ephemeral_branch = "temp-gumroad-s3-ingest"
    subprocess.run(["rm", "-rf", str(staging_git)], check=False)
    staging_git.mkdir(parents=True, exist_ok=True)

    remote_url = subprocess.check_output(
        ["git", "remote", "get-url", "origin"], cwd=str(REPO_DIR), text=True
    ).strip()

    try:
        print("1. Pushing isolated ephemeral orphan branch to feed Gumroad S3 ingest...", flush=True)
        subprocess.run(["git", "init", "-b", ephemeral_branch], cwd=str(staging_git), check=True, capture_output=True)
        subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=str(staging_git), check=True, capture_output=True)
        for p in assets_to_stage:
            (staging_git / p.name).write_bytes(p.read_bytes())
        subprocess.run(["git", "add", "."], cwd=str(staging_git), check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "ephemeral s3 ingest"],
            cwd=str(staging_git),
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "push", "--force", "origin", ephemeral_branch],
            cwd=str(staging_git),
            check=True,
            capture_output=True,
        )
        time.sleep(3)
        base_dl = f"https://raw.githubusercontent.com/{REPO_SLUG}/{ephemeral_branch}"

        _, sid = mcp_rpc(
            tok,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "abr-studio-publisher", "version": "1.0.0"},
                },
            },
        )
        mcp_rpc(tok, {"jsonrpc": "2.0", "method": "notifications/initialized"}, session_id=sid)

        req_id = 10
        existing, sid = call_tool(tok, sid, req_id, "list_products", {})
        req_id += 1
        by_name = {p.get("name"): p for p in existing.get("products", [])}

        # --- PRODUCT 1: FLAGSHIP $12 BUNDLE ---
        bundle_title = "The Calm Evening Sanctuary Bundle: 5 Screen-Free Bedtime Audio Stories (Zero Music) + 30-Day Printable Parent Reset Kit"
        if bundle_title in by_name:
            bundle_id = by_name[bundle_title]["id"]
            print(f"Reusing existing bundle draft: {bundle_id}", flush=True)
        else:
            print("2. Creating flagship $12 Early-Bird digital bundle on Gumroad MCP...", flush=True)
            created, sid = call_tool(
                tok,
                sid,
                req_id,
                "create_draft_product",
                {
                    "name": bundle_title,
                    "price_cents": 1200,
                    "currency": "usd",
                    "pay_what_you_want": False,
                    "description": BUNDLE_HTML,
                    "product_type": "digital",
                },
            )
            req_id += 1
            bundle_id = created.get("id") or created.get("product", {}).get("id")
            print(f"   Created bundle ID: {bundle_id}", flush=True)

        updated_bundle, sid = call_tool(
            tok,
            sid,
            req_id,
            "update_product",
            {
                "id": bundle_id,
                "permalink": "calm-evening-bundle",
                "category": "fiction-books/childrens-books",
                "summary": "Founding Parent Early-Bird ($12 through Nov 30 — rises to $17 Dec 1). Instant download: 5 Zero-Music MP3 Bedtime Stories + 5-Page Printable 30-Day Reset PDF.",
                "additional_details": [
                    {"name": "Audio Stories", "value": "5 MP3s (28m 12s · 48kHz / 320kbps)"},
                    {"name": "Audio Standard", "value": "100% Zero Music (+32.8 dB Voice)"},
                    {"name": "Printable Guide", "value": "5 Letter Pages (PDF Checklists)"},
                    {"name": "Works On", "value": "Airplane-Mode Phone, Yoto MYO, Tonie"},
                    {"name": "Recommended Ages", "value": "Ages 3–7 & Parents"},
                ],
                "tags": [
                    "bedtime-stories",
                    "screen-free",
                    "gentle-parenting",
                    "low-stimulation",
                    "montessori",
                    "kids-audio",
                    "yoto-cards",
                ],
                "custom_receipt_text": "Thank you for supporting 100% Zero-Music children's storytelling on @ABR-AntiBrainRot! Download your 5-Page Printable 30-Day Reset PDF and all 5 MP3 stories below (ready for Airplane Mode or blank Yoto Make-Your-Own cards).",
                "custom_view_content_button_text": "Open Stories & PDF Kit",
            },
        )
        req_id += 1

        print("3. Uploading cover banner + zero-music YouTube preview to Gumroad...", flush=True)
        call_tool(tok, sid, req_id, "add_cover", {"id": bundle_id, "url": f"{base_dl}/bundle_cover_1280x720.png"})
        req_id += 1
        call_tool(tok, sid, req_id, "add_cover", {"id": bundle_id, "url": "https://www.youtube.com/watch?v=xguUhCj4wdQ"})
        req_id += 1

        bundle_files = [
            ("Calm_Minds_30_Day_Anti_Brain_Rot_Parent_Kit_Printable.pdf", "00 — 30-Day Calm Minds Printable Parent Reset Kit (5-Page Letter PDF)"),
            ("01_The_Little_Snowshoe_Hares_Cedar_Hollow_ZeroMusic.mp3", "Track 01 — The Little Snowshoe Hare's Cedar Hollow (06:26 · Zero Music MP3)"),
            ("02_The_Sleepy_Badgers_Warm_Earth_Den_ZeroMusic.mp3", "Track 02 — The Sleepy Badger's Warm Earth Den (05:51 · Zero Music MP3)"),
            ("03_The_Winter_Wrens_Mossy_Stone_Wall_ZeroMusic.mp3", "Track 03 — The Winter Wren's Mossy Stone Wall (05:30 · Zero Music MP3)"),
            ("04_The_Quiet_Mountain_Beavers_Willow_Lodge_ZeroMusic.mp3", "Track 04 — The Quiet Mountain Beaver's Willow Lodge (05:19 · Zero Music MP3)"),
            ("05_The_Starlight_Dormouses_Hazelnut_Loft_ZeroMusic.mp3", "Track 05 — The Starlight Dormouse's Hazelnut Loft (05:06 · Zero Music MP3)"),
            ("ABR_Calm_Minds_Bedtime_Bundle_2026.zip", "Complete All-in-One ZIP Archive (All 5 MP3s + 5-Page Printable PDF)"),
        ]
        print("4. Attaching all 7 digital files to flagship bundle...", flush=True)
        for fname, disp in bundle_files:
            f_res, sid = call_tool(
                tok,
                sid,
                req_id,
                "add_file",
                {"id": bundle_id, "url": f"{base_dl}/{fname}", "display_name": disp},
            )
            req_id += 1
            print(f"   Attached: {disp} -> {json.dumps(f_res)[:160]}", flush=True)

        # --- PRODUCT 2: QUIET WOODLAND MONTHLY SUPPORTER CLUB ($5/mo) ---
        club_title = "The Quiet Woodland Club — Monthly Zero-Music Story & Supporter Membership (@ABR-AntiBrainRot)"
        if club_title in by_name:
            club_id = by_name[club_title]["id"]
        else:
            print("5. Creating $5/mo Quiet Woodland Supporter Club membership...", flush=True)
            created_club, sid = call_tool(
                tok,
                sid,
                req_id,
                "create_draft_product",
                {
                    "name": club_title,
                    "currency": "usd",
                    "description": CLUB_HTML,
                    "product_type": "membership",
                    "tiers": [
                        {
                            "name": "Quiet Woodland Supporter ($5/mo + Monthly Bonus Story)",
                            "price_cents": 500,
                            "pay_what_you_want": True,
                            "suggested_price_cents": 500,
                            "recurrence": "monthly",
                        }
                    ],
                },
            )
            req_id += 1
            club_id = created_club.get("id") or created_club.get("product", {}).get("id")

        call_tool(
            tok,
            sid,
            req_id,
            "update_product",
            {
                "id": club_id,
                "permalink": "quiet-woodland-club",
                "category": "audio/sleep-and-meditation",
                "summary": "Support independent 100% zero-music children's media & receive 1 new screen-free MP3 story + 1 printable activity sheet every month (plus instant welcome pack).",
                "tags": ["bedtime-stories", "screen-free", "low-stimulation", "gentle-parenting", "kids-audio"],
                "custom_receipt_text": "Welcome to The Quiet Woodland Club! Your support keeps @ABR-AntiBrainRot 100% zero-music and independent. Enjoy your instant welcome story & 30-Day Printable Guide below!",
                "custom_view_content_button_text": "Open Member Library",
            },
        )
        req_id += 1
        call_tool(tok, sid, req_id, "add_cover", {"id": club_id, "url": f"{base_dl}/club_cover_1280x720.png"})
        req_id += 1
        call_tool(
            tok,
            sid,
            req_id,
            "add_file",
            {
                "id": club_id,
                "url": f"{base_dl}/01_The_Little_Snowshoe_Hares_Cedar_Hollow_ZeroMusic.mp3",
                "display_name": "Welcome Story — The Little Snowshoe Hare's Cedar Hollow (Zero Music MP3)",
            },
        )
        req_id += 1
        call_tool(
            tok,
            sid,
            req_id,
            "add_file",
            {
                "id": club_id,
                "url": f"{base_dl}/Calm_Minds_30_Day_Anti_Brain_Rot_Parent_Kit_Printable.pdf",
                "display_name": "Welcome Bonus — 30-Day Calm Minds Printable Parent Reset Kit (PDF)",
            },
        )
        req_id += 1

        print("6. Waiting 25s to guarantee Gumroad S3 finishes background transfer of 65.67 MB ZIP...", flush=True)
        time.sleep(25)

        files_check, sid = call_tool(tok, sid, req_id, "list_files", {"id": bundle_id})
        req_id += 1
        print("7. Verified bundle files on Gumroad:", json.dumps(files_check, indent=2), flush=True)

        print("8. Publishing both products LIVE...", flush=True)
        pub_bundle, sid = call_tool(tok, sid, req_id, "publish_product", {"id": bundle_id})
        req_id += 1
        pub_club, sid = call_tool(tok, sid, req_id, "publish_product", {"id": club_id})
        req_id += 1

        final_bundle, sid = call_tool(tok, sid, req_id, "get_product", {"id": bundle_id})
        req_id += 1
        final_club, sid = call_tool(tok, sid, req_id, "get_product", {"id": club_id})

        manifest = {
            "bundle_product": final_bundle,
            "club_product": final_club,
            "bundle_files": files_check,
        }
        (PACK_DIR / "gumroad_live_products.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print("\n=== LIVE ON GUMROAD ===")
        print("Bundle:", json.dumps(final_bundle, indent=2))
        print("Club:", json.dumps(final_club, indent=2))

    finally:
        print("9. Deleting ephemeral GitHub branch & local staging so paid files remain private...", flush=True)
        subprocess.run(
            ["git", "push", "origin", "--delete", ephemeral_branch],
            cwd=str(staging_git),
            check=False,
            capture_output=True,
        )
        subprocess.run(["rm", "-rf", str(staging_git)], check=False)


if __name__ == "__main__":
    main()
