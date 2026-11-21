#!/usr/bin/env python3
"""
Batch update YouTube video descriptions & Channel About on @ABR-AntiBrainRot
with the Nov 17-30 Founding Parent Early-Bird Gumroad CTA + GitHub Pages
Parent Reset Kit storefront link, strictly respecting the 9,200-unit
QuotaLedger production soft cap.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STUDIO_DIR = Path("/shared/user/.gemini/raw_video_studio")
REPO_DIR = Path("/home/antigravity/awkandari-source/ABR_Anti_Brain_Rot")
sys.path.insert(0, str(STUDIO_DIR))

from linked_api_hub import LinkedAPIHub, LinkedAPIError, YouTubeQuotaExhaustedError  # noqa: E402

GUMROAD_BUNDLE_URL = "https://chronicle60.gumroad.com/l/calm-evening-bundle"
GUMROAD_CLUB_URL = "https://chronicle60.gumroad.com/l/quiet-woodland-club"
STOREFRONT_URL = "https://awkandari-source.github.io/ABR_Anti_Brain_Rot/"

GUMROAD_CTA_BLOCK = (
    "🌿 FOUNDING PARENT EARLY-BIRD ($12 INSTANT DOWNLOAD — RISES TO $17 ON DEC 1):\n"
    "Get all 5 Screen-Free Winter Woodland Bedtime Audio Stories (MP3s ready for "
    "Airplane-Mode phones & Yoto Make-Your-Own cards — 100% Human Voice + Nature SFX, "
    "Strictly Zero Music) + our 5-Page Printable 30-Day Calm Minds Parent Reset Kit:\n"
    f"👉 {GUMROAD_BUNDLE_URL}\n"
    f"☕ Join The Quiet Woodland Monthly Story Club ($5/mo): {GUMROAD_CLUB_URL}"
)

STOREFRONT_LINE = f"📚 Free Printable Parent Reset Kit & Storefront: {STOREFRONT_URL}"

CHANNEL_ABOUT_DESCRIPTION = (
    "Welcome to ABR Anti-Brain Rot — a quiet space engineered to counteract "
    "hyper-stimulating, fast-cut digital media.\n\n"
    "We create slow-paced, low-stimulation children's stories, evidence-based "
    "pediatric brain science, calm historical deep dives, and 180-minute sleep "
    "sanctuaries—crafted with 0% background music, using only human voice and "
    "natural foley.\n\n"
    "🌿 FOUNDING PARENT EARLY-BIRD ($12 INSTANT DOWNLOAD — RISES TO $17 ON DEC 1):\n"
    "5 Screen-Free Winter Woodland Bedtime Audio Stories (MP3s for Airplane Mode & "
    "Yoto cards, Zero Music) + 5-Page Printable 30-Day Parent Reset Kit:\n"
    f"👉 {GUMROAD_BUNDLE_URL}\n"
    f"☕ Quiet Woodland Club ($5/mo): {GUMROAD_CLUB_URL}\n"
    f"📚 Free Parent Reset Kit: {STOREFRONT_URL}"
)

MAX_DESC_BYTES = 4880


def build_updated_description(original: str) -> tuple[str, list[str]]:
    """Inject Gumroad CTA and/or storefront link right after the opening paragraph."""
    desc = (original or "").replace("\r\n", "\n").strip()
    added: list[str] = []

    needs_gumroad = GUMROAD_BUNDLE_URL not in desc
    needs_storefront = "awkandari-source.github.io/ABR_Anti_Brain_Rot" not in desc

    if not needs_gumroad and not needs_storefront:
        return desc, added

    inject_parts: list[str] = []
    if needs_gumroad:
        inject_parts.append(GUMROAD_CTA_BLOCK)
        added.append("gumroad_cta")
    if needs_storefront:
        inject_parts.append(STOREFRONT_LINE)
        added.append("storefront_url")

    inject_block = "\n".join(inject_parts)

    # Place right after the first paragraph so premise stays on lines 1-2
    if "\n\n" in desc:
        first_para, rest = desc.split("\n\n", 1)
        candidate = f"{first_para.rstrip()}\n\n{inject_block}\n\n{rest.lstrip()}"
    elif "\n" in desc:
        first_line, rest = desc.split("\n", 1)
        candidate = f"{first_line.rstrip()}\n\n{inject_block}\n\n{rest.lstrip()}"
    else:
        candidate = f"{desc}\n\n{inject_block}" if desc else inject_block

    # Enforce safe < 4,900 UTF-8 byte ceiling without damaging injected links
    if len(candidate.encode("utf-8")) > MAX_DESC_BYTES:
        # Trim from the very end (typically trailing hashtags) line by line
        lines = candidate.split("\n")
        while len("\n".join(lines).encode("utf-8")) > MAX_DESC_BYTES and len(lines) > 10:
            lines.pop()
        candidate = "\n".join(lines).rstrip()
        # Final byte-safe truncation fallback
        while len(candidate.encode("utf-8")) > MAX_DESC_BYTES:
            candidate = candidate[:-10].rstrip()

    return candidate, added


def fetch_all_channel_videos(yt: Any) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    ch_resp = yt.request(
        "GET",
        "channels",
        params={"part": "contentDetails,snippet,brandingSettings,statistics", "mine": "true"},
        purpose="production",
    )
    channel_item = ch_resp["items"][0]
    uploads_pl = channel_item["contentDetails"]["relatedPlaylists"]["uploads"]

    video_ids: list[str] = []
    page_token: str | None = None
    while True:
        params: dict[str, Any] = {
            "part": "contentDetails",
            "playlistId": uploads_pl,
            "maxResults": 50,
        }
        if page_token:
            params["pageToken"] = page_token
        resp = yt.request("GET", "playlistItems", params=params, purpose="production")
        for item in resp.get("items", []):
            video_ids.append(item["contentDetails"]["videoId"])
        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    videos: list[dict[str, Any]] = []
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i : i + 50]
        resp = yt.request(
            "GET",
            "videos",
            params={"part": "snippet,status", "id": ",".join(batch)},
            purpose="production",
        )
        videos.extend(resp.get("items", []))

    # Sort newest publishedAt first so latest & launch-window videos go first
    videos.sort(key=lambda v: v["snippet"].get("publishedAt", ""), reverse=True)
    return channel_item, videos


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Inspect without writing")
    parser.add_argument("--skip-channel-about", action="store_true")
    parser.add_argument("--limit", type=int, default=0, help="Optional max videos to update")
    args = parser.parse_args()

    hub = LinkedAPIHub()
    yt = hub.youtube

    channel_item, videos = fetch_all_channel_videos(yt)
    ch_id = channel_item["id"]
    ch_desc_now = channel_item["snippet"].get("description", "") or ""
    ch_needs_update = (
        GUMROAD_BUNDLE_URL not in ch_desc_now
        or "awkandari-source.github.io/ABR_Anti_Brain_Rot" not in ch_desc_now
    )

    to_update: list[tuple[dict[str, Any], str, list[str]]] = []
    already_done: list[str] = []
    max_bytes_seen = 0

    for v in videos:
        vid = v["id"]
        orig_desc = v["snippet"].get("description", "") or ""
        new_desc, added = build_updated_description(orig_desc)
        if not added:
            already_done.append(vid)
        else:
            b_len = len(new_desc.encode("utf-8"))
            if b_len > max_bytes_seen:
                max_bytes_seen = b_len
            to_update.append((v, new_desc, added))

    quota_state = yt.quota.status()
    remaining_prod = quota_state["production_soft_cap"] - quota_state["units_used"]
    print(f"Channel: {channel_item['snippet']['title']} ({ch_id})")
    print(f"Total videos: {len(videos)} | Already complete: {len(already_done)} | Need update: {len(to_update)}")
    print(f"Channel About needs update: {ch_needs_update} (new desc bytes: {len(CHANNEL_ABOUT_DESCRIPTION.encode('utf-8'))})")
    print(f"Max updated video description UTF-8 bytes: {max_bytes_seen} (ceiling: {MAX_DESC_BYTES})")
    print(f"QuotaLedger today ({quota_state['pt_date']}): {quota_state['units_used']} / {quota_state['production_soft_cap']} soft cap (remaining: {remaining_prod})")

    if args.dry_run:
        if to_update:
            sample_v, sample_desc, sample_added = to_update[0]
            print("\n--- SAMPLE UPDATED DESCRIPTION (first video) ---")
            print(f"ID: {sample_v['id']} | Title: {sample_v['snippet']['title']} | Added: {sample_added}")
            print(sample_desc[:750])
            print("--- END SAMPLE ---")
        return 0

    updated_records: list[dict[str, Any]] = []
    queued_for_reset: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    channel_about_updated = False

    # 1. Update Channel About description first (50 units) if needed and budget allows
    if ch_needs_update and not args.skip_channel_about:
        snap = yt.quota.status()
        if snap["units_used"] + 50 <= snap["production_soft_cap"]:
            try:
                branding = channel_item.get("brandingSettings", {})
                ch_branding = dict(branding.get("channel", {}))
                ch_branding["description"] = CHANNEL_ABOUT_DESCRIPTION
                yt.request(
                    "PUT",
                    "channels",
                    params={"part": "brandingSettings"},
                    json_body={"id": ch_id, "brandingSettings": {"channel": ch_branding}},
                    purpose="production",
                )
                channel_about_updated = True
                print("UPDATED Channel About description (50 units).")
                # Sync pending_channel_about_cta.json
                about_path = STUDIO_DIR / "pending_channel_about_cta.json"
                about_path.write_text(
                    json.dumps(
                        {
                            "channel_id": ch_id,
                            "description": CHANNEL_ABOUT_DESCRIPTION,
                            "utf8_bytes": len(CHANNEL_ABOUT_DESCRIPTION.encode("utf-8")),
                            "completed": True,
                            "completed_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        },
                        indent=2,
                        ensure_ascii=False,
                    )
                    + "\n",
                    encoding="utf-8",
                )
            except Exception as exc:
                print(f"WARN: Channel About update failed: {exc}")
                errors.append({"target": "channel_about", "error": str(exc)})

    # 2. Update video descriptions newest-first within 9,200-unit soft cap
    count = 0
    for idx, (v, new_desc, added) in enumerate(to_update, 1):
        vid = v["id"]
        sn = v["snippet"]
        if args.limit and count >= args.limit:
            queued_for_reset.append({"video_id": vid, "title": sn.get("title", ""), "publishedAt": sn.get("publishedAt", ""), "added_needed": added})
            continue

        snap = yt.quota.status()
        if snap["units_used"] + 50 > snap["production_soft_cap"]:
            queued_for_reset.append({"video_id": vid, "title": sn.get("title", ""), "publishedAt": sn.get("publishedAt", ""), "added_needed": added})
            continue

        try:
            yt.update_video_snippet(
                vid,
                title=sn["title"],
                description=new_desc,
                category_id=sn.get("categoryId", "27"),
                tags=sn.get("tags"),
                default_language=sn.get("defaultLanguage"),
                default_audio_language=sn.get("defaultAudioLanguage"),
                purpose="production",
            )
            count += 1
            updated_records.append(
                {
                    "video_id": vid,
                    "title": sn.get("title", ""),
                    "publishedAt": sn.get("publishedAt", ""),
                    "added": added,
                    "utf8_bytes": len(new_desc.encode("utf-8")),
                }
            )
            if count % 25 == 0 or count == len(to_update):
                q = yt.quota.status()
                print(f"Progress: {count} updated | Quota: {q['units_used']}/{q['production_soft_cap']} | Queued: {len(queued_for_reset)}")
        except YouTubeQuotaExhaustedError as exc:
            print(f"QUOTA CAP REACHED at {count} updates: {exc}")
            queued_for_reset.append({"video_id": vid, "title": sn.get("title", ""), "publishedAt": sn.get("publishedAt", ""), "added_needed": added})
            for rem_v, _, rem_added in to_update[idx:]:
                queued_for_reset.append(
                    {
                        "video_id": rem_v["id"],
                        "title": rem_v["snippet"].get("title", ""),
                        "publishedAt": rem_v["snippet"].get("publishedAt", ""),
                        "added_needed": rem_added,
                    }
                )
            break
        except Exception as exc:
            print(f"ERROR updating {vid} ({sn.get('title', '')[:45]}): {exc}")
            errors.append({"video_id": vid, "title": sn.get("title", ""), "error": str(exc)})

    # 3. Sync pending_gumroad_cta_injections.json so sweeper/next-day run knows exact remainder
    pending_ids = [item["video_id"] for item in queued_for_reset]
    completed_ids = list(dict.fromkeys(already_done + [r["video_id"] for r in updated_records]))
    pending_path = STUDIO_DIR / "pending_gumroad_cta_injections.json"
    pending_path.write_text(
        json.dumps(
            {
                "gumroad_bundle_url": GUMROAD_BUNDLE_URL,
                "gumroad_club_url": GUMROAD_CLUB_URL,
                "storefront_url": STOREFRONT_URL,
                "cta_block": GUMROAD_CTA_BLOCK,
                "updated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "pending_video_ids": pending_ids,
                "completed_video_ids": completed_ids,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    # 4. Write receipt JSON to repo
    final_quota = yt.quota.status()
    receipt = {
        "executed_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "channel_id": ch_id,
        "total_channel_videos": len(videos),
        "channel_about_updated": channel_about_updated,
        "already_complete_before_run": len(already_done),
        "updated_this_run": len(updated_records),
        "queued_for_next_pt_reset": len(queued_for_reset),
        "errors_count": len(errors),
        "quota_ledger": final_quota,
        "queued_videos": queued_for_reset,
        "errors": errors,
    }
    receipt_path = REPO_DIR / "December_2026_Launch_Pack" / "description_update_receipt_2026-11-21.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("\n=== SUMMARY ===")
    print(json.dumps({k: v for k, v in receipt.items() if k not in ("queued_videos", "errors")}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
