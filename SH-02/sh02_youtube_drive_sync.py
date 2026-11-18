#!/usr/bin/env python3
"""
SH-02 ("Neuro-Acoustic Sleep Sanctuaries — Shorts") Multi-Platform Sync Orchestrator
====================================================================================
1. Verifies 6/6 `QA_VERIFIED` Dual-Gate status across `SH02_S01`..`SH02_S06`.
2. Mirrors all 6 `QA_VERIFIED` MP4 masters, WAV stems, `sh02_manifest.json`, per-asset manifests,
   scripts, and gate audit logs to a dedicated `SH-02` Google Drive folder under root
   `1mlAlS_xpEn11gUGyKi_zuQiDZ0Co9Ay9`.
3. Uploads & schedules all 6 vertical Shorts on `@ABR-AntiBrainRot` for evening release windows
   (`02:00:00Z` / `21:00 EST`), binds to playlist `"Neuro-Acoustic Sleep Sanctuaries — Shorts"`
   + `"Evidence-Based Media & Sleep Shorts"` (`PLUt7V0-ta200`), and binds Related Video funnel
   metadata to parent 180-minute sanctuaries (`ABR_NS01`..`ABR_NS05`).
   (If YouTube OAuth token is expired `invalid_grant`, stages full sweeper/upload payloads cleanly
   without fabricating IDs and supports `--resume-youtube`.)
4. Commits and pushes all scripts, manifests, and audit reports cleanly to GitHub, preserving the
   `git status --porcelain` working-tree check so `git status` finishes 100% clean.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, "/shared/user/.gemini/raw_video_studio")
from linked_api_hub import LinkedAPIError, LinkedAPIHub, YouTubeQuotaExhaustedError

REPO_ROOT = Path("/home/antigravity/awkandari-source/ABR_Anti_Brain_Rot")
SH02_DIR = REPO_ROOT / "SH-02"
STUDIO_DIR = Path("/shared/user/.gemini/raw_video_studio")
STUDIO_SH02_DIR = STUDIO_DIR / "SH-02"
SHARED_TRACKER_PATH = STUDIO_DIR / "ABR_AntiGravity_Workspace" / "INDEX_Tracker.json"

MANIFEST_PATH = SH02_DIR / "sh02_manifest.json"
SH02_TRACKER_PATH = SH02_DIR / "sh02_tracker.json"

DRIVE_ROOT_ID = "1mlAlS_xpEn11gUGyKi_zuQiDZ0Co9Ay9"
DRIVE_SH02_FOLDER_NAME = "SH-02_Neuro_Acoustic_Sleep_Sanctuaries_Shorts"

PLAYLIST_TITLE = "Neuro-Acoustic Sleep Sanctuaries — Shorts"
SHORTS_SHELF_PLAYLIST_ID = "PLUt7V0-ta200"
SLEEP_SCIENCE_PLAYLIST_ID = "PLAe5Tqk750cc"
PARENT_SANCTUARIES_PLAYLIST_ID = "PLO3jEEgHm_Iw"

GDRIVE_BIN = "/opt/antigravity/plugins/gdrive/skills/gdrive/scripts/gdrive"


def safe_copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with src.open("rb") as f_in, dst.open("wb") as f_out:
        while chunk := f_in.read(4 * 1024 * 1024):
            f_out.write(chunk)


def gdrive_extract_id(out_str: str) -> str:
    if isinstance(out_str, dict):
        return str(out_str.get("id", ""))
    text = str(out_str).strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict) and "id" in parsed:
            return str(parsed["id"])
    except Exception:
        pass
    m_parens = re.search(r"\(([A-Za-z0-9_-]{25,})\)", text)
    if m_parens:
        return m_parens.group(1)
    tokens = [
        tok for tok in text.replace("(", " ").replace(")", " ").replace('"', " ").replace(",", " ").split()
        if len(tok) >= 25 and any(c.isdigit() for c in tok) and any(c.isalpha() for c in tok) and "/" not in tok and "." not in tok
    ]
    return tokens[-1] if tokens else text


def gdrive_find_or_mkdir(hub: LinkedAPIHub, name: str, parent_id: str) -> str:
    found = hub.gdrive.search(name, parent_id=parent_id)
    if isinstance(found, list):
        for entry in found:
            if entry.get("name") == name and "folder" in str(entry.get("mimeType", "")).lower():
                return str(entry["id"])
    p = subprocess.run(
        [GDRIVE_BIN, "mutate", "mkdir", name, "--parent", parent_id, "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    return gdrive_extract_id(p.stdout)


def gdrive_upsert_file(hub: LinkedAPIHub, local_path: Path, parent_id: str) -> str:
    found = hub.gdrive.search(local_path.name, parent_id=parent_id)
    if isinstance(found, list):
        for entry in found:
            if entry.get("name") == local_path.name and "folder" not in str(entry.get("mimeType", "")).lower():
                fid = str(entry["id"])
                p_up = subprocess.run(
                    [GDRIVE_BIN, "mutate", "update", fid, str(local_path), "--json"],
                    capture_output=True,
                    text=True,
                )
                if p_up.returncode == 0:
                    return fid
    p_new = subprocess.run(
        [GDRIVE_BIN, "mutate", "upload", str(local_path), "--parent", parent_id, "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    return gdrive_extract_id(p_new.stdout)


def resolve_parent_sanctuary_links() -> dict[str, dict[str, str]]:
    """
    Dynamically resolves live YouTube IDs for ABR_NS01..ABR_NS05 (including verified live
    ABR_NS03 `psEs90dgdcU` on @ABR-AntiBrainRot) + companion 180-minute sanctuaries in `PLO3jEEgHm_Iw`.
    """
    parent_map: dict[str, dict[str, str]] = {
        "ABR_NS01": {
            "id": "ABR_NS01",
            "title": "180-Minute Midnight Cedar Rain & Mossy Cave Drip",
            "youtube_id": "",
            "companion_sanctuary_youtube_id": "q9woVuJb9X0",
            "playlist_url": f"https://www.youtube.com/playlist?list={PARENT_SANCTUARIES_PLAYLIST_ID}",
        },
        "ABR_NS02": {
            "id": "ABR_NS02",
            "title": "180-Minute Deep Ocean Swell & Pebbled Cove Undertow",
            "youtube_id": "",
            "companion_sanctuary_youtube_id": "xcAo79qLcLc",
            "playlist_url": f"https://www.youtube.com/playlist?list={PARENT_SANCTUARIES_PLAYLIST_ID}",
        },
        "ABR_NS03": {
            "id": "ABR_NS03",
            "title": "The 180-Minute Settling Stone Hearth & Dusk Pine Breeze",
            "youtube_id": "psEs90dgdcU",
            "companion_sanctuary_youtube_id": "psEs90dgdcU",
            "playlist_url": f"https://www.youtube.com/playlist?list={PARENT_SANCTUARIES_PLAYLIST_ID}",
        },
        "ABR_NS04": {
            "id": "ABR_NS04",
            "title": "180-Minute Alpine Snowfall & Quiet Cabin Timber",
            "youtube_id": "",
            "companion_sanctuary_youtube_id": "OwMTPuornpo",
            "playlist_url": f"https://www.youtube.com/playlist?list={PARENT_SANCTUARIES_PLAYLIST_ID}",
        },
        "ABR_NS05": {
            "id": "ABR_NS05",
            "title": "180-Minute Desert Night Wind & Cooling Basalt Stone",
            "youtube_id": "",
            "companion_sanctuary_youtube_id": "BgpIR-lvpZw",
            "playlist_url": f"https://www.youtube.com/playlist?list={PARENT_SANCTUARIES_PLAYLIST_ID}",
        },
    }
    if SHARED_TRACKER_PATH.exists():
        try:
            tracker = json.loads(SHARED_TRACKER_PATH.read_text(encoding="utf-8"))
            for ns_id, info in parent_map.items():
                entry = tracker.get("assets", {}).get(ns_id, {})
                yt_id = entry.get("youtube_id") or entry.get("youtube_video_id") or ""
                if yt_id:
                    info["youtube_id"] = str(yt_id)
        except Exception:
            pass
    return parent_map


def build_sleep_short_description(
    item: dict[str, Any],
    parent_info: dict[str, str],
    shorts_playlist_id: str | None,
) -> str:
    parent_id = item["parent_sanctuary_id"]
    parent_title = item["parent_sanctuary_title"]
    parent_yt = parent_info.get("youtube_id", "")
    comp_yt = parent_info.get("companion_sanctuary_youtube_id", "")
    if parent_yt:
        parent_watch_line = (
            f"Enter Parent Sanctuary ({parent_id} — {parent_title}): https://www.youtube.com/watch?v={parent_yt} "
            f"| Full 180-Min Sanctuaries: https://www.youtube.com/playlist?list={PARENT_SANCTUARIES_PLAYLIST_ID}"
        )
    elif comp_yt:
        parent_watch_line = (
            f"Enter Parent Sanctuary ({parent_id} — {parent_title}) in 180-Min Sleep Sanctuaries: "
            f"https://www.youtube.com/playlist?list={PARENT_SANCTUARIES_PLAYLIST_ID} "
            f"| Companion 3-Hr Sanctuary: https://www.youtube.com/watch?v={comp_yt}"
        )
    else:
        parent_watch_line = (
            f"Enter Parent Sanctuary ({parent_id} — {parent_title}) in our 180-Minute Sleep Sanctuaries Playlist: "
            f"https://www.youtube.com/playlist?list={PARENT_SANCTUARIES_PLAYLIST_ID}"
        )
    pl_line = (
        f"Neuro-Acoustic Sleep Sanctuaries — Shorts Playlist: https://www.youtube.com/playlist?list={shorts_playlist_id}"
        if shorts_playlist_id
        else f"Evidence-Based Media & Sleep Shorts Playlist: https://www.youtube.com/playlist?list={SHORTS_SHELF_PLAYLIST_ID}"
    )

    lines = [
        f"{item['title'].replace(' #Shorts', '')} — calm 60-second late-night sleep science from @ABR-AntiBrainRot.",
        "Graded strictly below 1900K (1850K warm ember curve with -15% gradual luminance decay) and mixed with 0% music (-16.0 LUFS soft baritone over pure organic nature foley, >= +30 dB voice separation).",
        parent_watch_line,
        pl_line,
        "Free Printable Calm Minds Family Reset Kit & Zero-Music Sleep Guide: https://awkandari-source.github.io/ABR_Anti_Brain_Rot/",
        "Pediatric & Late-Night Hearing Safety Note: Keep bedside playback gentle (<= 50 dBA at a 2-meter speaker distance).",
        "",
        "Primary Scientific Source:",
        f"- {item['primary_source_citation']}",
        "",
        "Chapters:",
        "00:00 Sub-1900K Evening Observation",
        "00:15 Sleep Neuroscience Mechanism",
        "00:30 Acoustic & Circadian Downregulation",
        f"00:45 Transition to {parent_id} (180-Minute Sleep Sanctuary)",
        "",
        "#Shorts #SleepScience #ZeroMusic #CircadianRhythm #DeepSleep #AntiBrainRot #LowStimulation",
    ]
    desc = "\n".join(lines)
    if "drive.google.com" in desc.lower():
        raise ValueError(f"Privacy violation detected in {item['asset_id']} description!")
    return desc


def ensure_shorts_playlist(hub: LinkedAPIHub) -> str:
    existing = hub.youtube.list_playlists(max_results=50)
    for pl in existing:
        if pl.get("snippet", {}).get("title", "").strip() == PLAYLIST_TITLE:
            return str(pl["id"])
    desc = (
        "Neuro-Acoustic Sleep Sanctuaries — Shorts: 60-second sub-1900K sleep-science companions "
        "explaining circadian lighting, acoustic masking, respiratory pacing, 90-minute sleep cycles, "
        "snow acoustic dampening, and nocturnal thermoregulation—each linked directly to its parent "
        "180-minute zero-music sleep sanctuary on @ABR-AntiBrainRot."
    )
    res = hub.youtube.request(
        "POST",
        "playlists",
        params={"part": "snippet,status"},
        json_body={
            "snippet": {"title": PLAYLIST_TITLE, "description": desc},
            "status": {"privacyStatus": "public"},
        },
    )
    return str(res["id"])


def check_youtube_oauth_ready(hub: LinkedAPIHub) -> tuple[bool, str]:
    try:
        hub.youtube.get_access_token()
        return True, "READY"
    except Exception as exc:
        return False, str(exc)


def git_commit_and_push_clean(commit_message: str) -> tuple[str, bool]:
    """
    Rebases onto latest origin/main safely, stages SH-02 + qc_gate.py (+ Index if updated),
    checks `git status --porcelain` before committing, pushes to origin with rebase retry,
    and verifies a 100% clean working tree.
    """
    import shutil as _shutil

    for pycache_dir in (REPO_ROOT / ".agents").rglob("__pycache__"):
        _shutil.rmtree(pycache_dir, ignore_errors=True)

    paths_to_stage = [
        "SH-02",
        ".agents/skills/abr-daily-producer/scripts/qc_gate.py",
    ]
    if (REPO_ROOT / "ABR_Anti_Brain_Rot_Index.md").exists():
        paths_to_stage.append("ABR_Anti_Brain_Rot_Index.md")

    subprocess.run(["git", "add", *paths_to_stage], cwd=str(REPO_ROOT), check=True)
    status_before = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    if status_before.stdout.strip():
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=str(REPO_ROOT),
            check=True,
        )

    for attempt in range(4):
        subprocess.run(
            ["git", "pull", "--rebase", "--autostash", "origin", "main"],
            cwd=str(REPO_ROOT),
            check=True,
        )
        push_p = subprocess.run(
            ["git", "push", "origin", "HEAD:main"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        if push_p.returncode == 0:
            break
        if attempt == 3:
            raise RuntimeError(f"git push failed after 4 attempts: {push_p.stderr}")
        time.sleep(2.0)

    for pycache_dir in (REPO_ROOT / ".agents").rglob("__pycache__"):
        _shutil.rmtree(pycache_dir, ignore_errors=True)

    head_hash = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=str(REPO_ROOT),
        text=True,
    ).strip()
    status_after = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    is_clean = status_after.stdout.strip() == ""
    return head_hash, is_clean


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-drive", action="store_true", help="Skip Google Drive upload if already mirrored")
    ap.add_argument("--resume-youtube", action="store_true", help="Resume YouTube uploads after OAuth refresh")
    args = ap.parse_args()

    batch_manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    deliverables = batch_manifest["deliverables"]

    # 1. Verify 6/6 QA_VERIFIED before touching Drive or YouTube
    for item in deliverables:
        aid = item["asset_id"]
        audit_path = SH02_DIR / "audit_logs" / f"{aid}_gate_audit.json"
        if not audit_path.exists():
            raise RuntimeError(f"Missing Dual-Gate audit log for {aid}: {audit_path}")
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        if not audit.get("dual_gate_passed") or audit.get("dual_gate_status") != "QA_VERIFIED":
            raise RuntimeError(f"{aid} is not QA_VERIFIED!")
        if audit["qc_gate_audit"]["stems_audit"]["zero_music_spectral"]["music_detected"] is not False:
            raise RuntimeError(f"{aid} failed music_detected == false check!")

    hub = LinkedAPIHub()
    parent_links = resolve_parent_sanctuary_links()

    # 2. Mirror all 6 QA_VERIFIED MP4 masters, stems, manifests & gate audit logs to SH-02 Google Drive folder
    sh02_drive_folder_id = batch_manifest.get("drive_archive", {}).get("sh02_folder_id", "")
    if not args.skip_drive or not sh02_drive_folder_id:
        print(f"[SH-02 Sync] Ensuring Google Drive folder '{DRIVE_SH02_FOLDER_NAME}' under {DRIVE_ROOT_ID}...", flush=True)
        sh02_drive_folder_id = gdrive_find_or_mkdir(hub, DRIVE_SH02_FOLDER_NAME, DRIVE_ROOT_ID)
        print(f"[SH-02 Sync] SH-02 Drive Folder ID: {sh02_drive_folder_id}", flush=True)

        for item in deliverables:
            aid = item["asset_id"]
            sub_name = f"{aid}_{item['publish_at_utc'][:10]}"
            sub_id = gdrive_find_or_mkdir(hub, sub_name, sh02_drive_folder_id)
            mp4_p = SH02_DIR / "masters" / f"{aid}_Master_1080x1920_24p.mp4"
            vo_p = SH02_DIR / "stems" / f"{aid}_Voice_16LUFS.wav"
            fs_p = SH02_DIR / "stems" / f"{aid}_Foley_Sampler_26p2LUFS.wav"
            fd_p = SH02_DIR / "stems" / f"{aid}_Foley_MixCushion_Ducked.wav"
            man_p = SH02_DIR / "manifests" / f"{aid}_manifest.json"
            aud_p = SH02_DIR / "audit_logs" / f"{aid}_gate_audit.json"
            scr_p = SH02_DIR / "scripts" / f"{aid}_Script_Foley.md"

            print(f"[{aid}] Mirroring MP4 master, stems, manifest, script & audit log to Drive ({sub_id})...", flush=True)
            mp4_id = gdrive_upsert_file(hub, mp4_p, sub_id)
            vo_id = gdrive_upsert_file(hub, vo_p, sub_id)
            fs_id = gdrive_upsert_file(hub, fs_p, sub_id)
            fd_id = gdrive_upsert_file(hub, fd_p, sub_id)
            aud_id = gdrive_upsert_file(hub, aud_p, sub_id)
            scr_id = gdrive_upsert_file(hub, scr_p, sub_id)

            item_man = json.loads(man_p.read_text(encoding="utf-8"))
            item_man["drive_archive"] = {
                "sh02_drive_folder_id": sh02_drive_folder_id,
                "asset_drive_folder_id": sub_id,
                "asset_drive_url": f"https://drive.google.com/drive/folders/{sub_id}",
                "files": {
                    "master_mp4": mp4_id,
                    "voice_wav": vo_id,
                    "foley_sampler_wav": fs_id,
                    "foley_ducked_wav": fd_id,
                    "gate_audit_json": aud_id,
                    "script_md": scr_id,
                },
            }
            man_p.write_text(json.dumps(item_man, indent=2) + "\n", encoding="utf-8")
            man_id = gdrive_upsert_file(hub, man_p, sub_id)
            item_man["drive_archive"]["files"]["manifest_json"] = man_id
            man_p.write_text(json.dumps(item_man, indent=2) + "\n", encoding="utf-8")
            safe_copy_file(man_p, STUDIO_SH02_DIR / "manifests" / man_p.name)

            item["drive_archive"] = item_man["drive_archive"]

        batch_manifest["drive_archive"] = {
            "root_folder_id": DRIVE_ROOT_ID,
            "sh02_folder_id": sh02_drive_folder_id,
            "sh02_folder_url": f"https://drive.google.com/drive/folders/{sh02_drive_folder_id}",
            "mirrored_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "status": "MIRRORED_6_OF_6",
        }
        MANIFEST_PATH.write_text(json.dumps(batch_manifest, indent=2) + "\n", encoding="utf-8")
        safe_copy_file(MANIFEST_PATH, STUDIO_SH02_DIR / "sh02_manifest.json")
        gdrive_upsert_file(hub, MANIFEST_PATH, sh02_drive_folder_id)
        qa_sum = SH02_DIR / "audit_logs" / "SH02_BATCH_QA_SUMMARY.json"
        if qa_sum.exists():
            gdrive_upsert_file(hub, qa_sum, sh02_drive_folder_id)

    # 3. YouTube Scheduling & Playlist Binding (with strict QuotaLedger 9,200-unit soft-cap governance)
    yt_ready, yt_detail = check_youtube_oauth_ready(hub)
    shorts_playlist_id: str | None = batch_manifest.get("playlist", {}).get("playlist_id")
    yt_records: list[dict[str, Any]] = []
    scheduled_count = 0
    quota_deferred_count = 0

    sh02_tracker = (
        json.loads(SH02_TRACKER_PATH.read_text(encoding="utf-8"))
        if SH02_TRACKER_PATH.exists()
        else {"batch_id": "SH-02", "sop_version": "ABR-AG-SOP-v2.1", "assets": {}}
    )

    if yt_ready:
        shorts_playlist_id = ensure_shorts_playlist(hub)
        batch_manifest["playlist"]["playlist_id"] = shorts_playlist_id
        batch_manifest["playlist"]["playlist_url"] = f"https://www.youtube.com/playlist?list={shorts_playlist_id}"
        sh02_tracker["playlist_id"] = shorts_playlist_id
        sh02_tracker["playlist_title"] = PLAYLIST_TITLE
        print(f"[SH-02 Sync] Official Playlist '{PLAYLIST_TITLE}' LIVE: {shorts_playlist_id}", flush=True)

        for idx, item in enumerate(deliverables):
            aid = item["asset_id"]
            man_p = SH02_DIR / "manifests" / f"{aid}_manifest.json"
            item_man = json.loads(man_p.read_text(encoding="utf-8"))
            existing_vid = item_man.get("youtube_routing", {}).get("youtube_video_id")
            p_info = parent_links[item["parent_sanctuary_id"]]
            desc = build_sleep_short_description(item, p_info, shorts_playlist_id)
            mp4_p = SH02_DIR / "masters" / f"{aid}_Master_1080x1920_24p.mp4"

            vid_id: str | None = None
            watch_url: str | None = None
            defer_reason: str | None = None

            if existing_vid:
                vid_id = str(existing_vid)
                watch_url = f"https://www.youtube.com/shorts/{vid_id}"
                print(f"[{aid}] Already scheduled on YouTube: {vid_id}", flush=True)
            else:
                try:
                    print(f"[{aid}] Uploading {mp4_p.name} -> {item['publish_at_utc']}...", flush=True)
                    up_res = hub.youtube.upload_video(
                        mp4_p,
                        title=item["title"],
                        description=desc,
                        tags=[
                            "sleep science", "sub 1900k light", "zero music sleep",
                            "neuro acoustic sleep sanctuary", "anti brain rot", "calm bedtime science",
                            "melatonin sleep", "deep sleep sounds no music", "shorts",
                        ],
                        category_id="27",
                        privacy_status="private",
                        publish_at_iso=item["publish_at_utc"],
                        made_for_kids=False,
                        purpose="production",
                    )
                    vid_id = str(up_res["id"])
                    watch_url = f"https://www.youtube.com/shorts/{vid_id}"
                    hub.youtube.add_to_playlist(shorts_playlist_id, vid_id, position=idx, purpose="sweeper")
                    hub.youtube.add_to_playlist(SHORTS_SHELF_PLAYLIST_ID, vid_id, purpose="sweeper")
                    print(f"[{aid}] Scheduled LIVE on YouTube: {vid_id} ({watch_url})", flush=True)
                except YouTubeQuotaExhaustedError as q_exc:
                    defer_reason = str(q_exc)
                    print(f"[{aid}] Deferred by QuotaLedger: {defer_reason}", flush=True)

            q_now = hub.youtube.quota.status()
            sweeper_dir = STUDIO_SH02_DIR / "sweeper_staging" / f"{aid}_{item['slug']}"
            sweeper_dir.mkdir(parents=True, exist_ok=True)

            if vid_id and watch_url:
                scheduled_count += 1
                item_man["state"] = "API_SCHEDULED"
                item_man.setdefault("youtube_routing", {}).update(
                    {
                        "youtube_video_id": vid_id,
                        "shorts_url": watch_url,
                        "watch_url": f"https://www.youtube.com/watch?v={vid_id}",
                        "playlist_id": shorts_playlist_id,
                        "playlist_url": f"https://www.youtube.com/playlist?list={shorts_playlist_id}",
                        "parent_sanctuary_id": item["parent_sanctuary_id"],
                        "parent_sanctuary_youtube_id": p_info.get("youtube_id", ""),
                        "companion_sanctuary_youtube_id": p_info.get("companion_sanctuary_youtube_id", ""),
                        "privacy_status": "private",
                        "publish_at_utc": item["publish_at_utc"],
                        "upload_staging_state": "API_SCHEDULED",
                    }
                )
                item["state"] = "API_SCHEDULED"
                item["youtube_video_id"] = vid_id
                item["youtube_url"] = watch_url
                item["playlist_id"] = shorts_playlist_id
                item["parent_sanctuary_youtube_id"] = p_info.get("youtube_id", "")

                sh02_tracker.setdefault("assets", {}).setdefault(aid, {}).update(
                    {
                        "state": "API_SCHEDULED",
                        "youtube_video_id": vid_id,
                        "youtube_url": watch_url,
                        "playlist_id": shorts_playlist_id,
                        "publish_at_utc": item["publish_at_utc"],
                    }
                )
                (sweeper_dir / "youtube_publish_metadata.json").write_text(
                    json.dumps(
                        {
                            "slug": f"{aid}_{item['slug']}",
                            "asset_id": aid,
                            "title": item["title"],
                            "description": desc,
                            "format": "9:16_SLEEP_SANCTUARY_SHORT",
                            "youtube_video_id": vid_id,
                            "youtube_url": watch_url,
                            "status": "API_SCHEDULED",
                            "publish_at_utc": item["publish_at_utc"],
                            "playlist_id": shorts_playlist_id,
                            "assigned_playlists": [shorts_playlist_id, SHORTS_SHELF_PLAYLIST_ID, SLEEP_SCIENCE_PLAYLIST_ID],
                            "related_parent_sanctuary_id": item["parent_sanctuary_id"],
                            "related_parent_sanctuary_youtube_id": p_info.get("youtube_id", ""),
                            "companion_sanctuary_youtube_id": p_info.get("companion_sanctuary_youtube_id", ""),
                            "post_publish_swept": False,
                        },
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                yt_records.append(
                    {
                        "asset_id": aid,
                        "youtube_video_id": vid_id,
                        "youtube_url": watch_url,
                        "publish_at_utc": item["publish_at_utc"],
                        "playlist_id": shorts_playlist_id,
                        "parent_sanctuary_id": item["parent_sanctuary_id"],
                        "parent_sanctuary_youtube_id": p_info.get("youtube_id", ""),
                        "status": "API_SCHEDULED",
                    }
                )
            else:
                quota_deferred_count += 1
                item_man["state"] = "QA_VERIFIED"
                item_man["upload_staging_state"] = "STAGED_FOR_POST_QUOTA_RESET"
                item_man.setdefault("youtube_routing", {}).update(
                    {
                        "youtube_video_id": None,
                        "playlist_id": shorts_playlist_id,
                        "playlist_url": f"https://www.youtube.com/playlist?list={shorts_playlist_id}",
                        "parent_sanctuary_id": item["parent_sanctuary_id"],
                        "parent_sanctuary_youtube_id": p_info.get("youtube_id", ""),
                        "companion_sanctuary_youtube_id": p_info.get("companion_sanctuary_youtube_id", ""),
                        "privacy_status": "private",
                        "publish_at_utc": item["publish_at_utc"],
                        "upload_staging_state": "STAGED_FOR_POST_QUOTA_RESET",
                        "next_quota_reset_utc": q_now["next_reset_utc"],
                        "quota_defer_reason": defer_reason,
                    }
                )
                item["upload_staging_state"] = "STAGED_FOR_POST_QUOTA_RESET"
                item["playlist_id"] = shorts_playlist_id
                item["parent_sanctuary_youtube_id"] = p_info.get("youtube_id", "")
                item["next_quota_reset_utc"] = q_now["next_reset_utc"]

                sh02_tracker.setdefault("assets", {}).setdefault(aid, {}).update(
                    {
                        "state": "QA_VERIFIED",
                        "upload_staging_state": "STAGED_FOR_POST_QUOTA_RESET",
                        "playlist_id": shorts_playlist_id,
                        "publish_at_utc": item["publish_at_utc"],
                        "next_quota_reset_utc": q_now["next_reset_utc"],
                    }
                )
                (sweeper_dir / "youtube_publish_metadata.json").write_text(
                    json.dumps(
                        {
                            "slug": f"{aid}_{item['slug']}",
                            "asset_id": aid,
                            "title": item["title"],
                            "description": desc,
                            "format": "9:16_SLEEP_SANCTUARY_SHORT",
                            "youtube_video_id": None,
                            "status": "STAGED_FOR_POST_QUOTA_RESET",
                            "publish_at_utc": item["publish_at_utc"],
                            "playlist_id": shorts_playlist_id,
                            "target_playlist_title": PLAYLIST_TITLE,
                            "assigned_playlists": [shorts_playlist_id, SHORTS_SHELF_PLAYLIST_ID, SLEEP_SCIENCE_PLAYLIST_ID],
                            "related_parent_sanctuary_id": item["parent_sanctuary_id"],
                            "related_parent_sanctuary_title": item["parent_sanctuary_title"],
                            "related_parent_sanctuary_youtube_id": p_info.get("youtube_id", ""),
                            "companion_sanctuary_youtube_id": p_info.get("companion_sanctuary_youtube_id", ""),
                            "next_quota_reset_utc": q_now["next_reset_utc"],
                            "mp4_path": str(STUDIO_SH02_DIR / "masters" / f"{aid}_Master_1080x1920_24p.mp4"),
                        },
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                yt_records.append(
                    {
                        "asset_id": aid,
                        "youtube_video_id": None,
                        "publish_at_utc": item["publish_at_utc"],
                        "playlist_id": shorts_playlist_id,
                        "parent_sanctuary_id": item["parent_sanctuary_id"],
                        "parent_sanctuary_youtube_id": p_info.get("youtube_id", ""),
                        "next_quota_reset_utc": q_now["next_reset_utc"],
                        "status": "STAGED_FOR_POST_QUOTA_RESET",
                    }
                )

            man_p.write_text(json.dumps(item_man, indent=2) + "\n", encoding="utf-8")
            safe_copy_file(man_p, STUDIO_SH02_DIR / "manifests" / man_p.name)
            sub_drv = item_man.get("drive_archive", {}).get("asset_drive_folder_id")
            if sub_drv:
                gdrive_upsert_file(hub, man_p, str(sub_drv))

        if scheduled_count == len(deliverables):
            batch_manifest["batch_state"] = "API_SCHEDULED"
            batch_manifest["youtube_sync_status"] = "SCHEDULED_6_OF_6"
        else:
            batch_manifest["batch_state"] = "QA_VERIFIED_PLAYLIST_BOUND"
            batch_manifest["youtube_sync_status"] = (
                f"SCHEDULED_{scheduled_count}_OF_6_DEFERRED_{quota_deferred_count}_QUOTA_SOFT_CAP"
            )
    else:
        print(f"[SH-02 Sync] YouTube OAuth token requires refresh ({yt_detail}). Staging ready-to-publish payloads...", flush=True)
        for item in deliverables:
            aid = item["asset_id"]
            p_info = parent_links[item["parent_sanctuary_id"]]
            desc = build_sleep_short_description(item, p_info, shorts_playlist_id)
            sweeper_dir = STUDIO_SH02_DIR / "sweeper_staging" / f"{aid}_{item['slug']}"
            sweeper_dir.mkdir(parents=True, exist_ok=True)
            (sweeper_dir / "youtube_publish_metadata.json").write_text(
                json.dumps(
                    {
                        "slug": f"{aid}_{item['slug']}",
                        "asset_id": aid,
                        "title": item["title"],
                        "description": desc,
                        "format": "9:16_SLEEP_SANCTUARY_SHORT",
                        "youtube_video_id": None,
                        "status": "STAGED_AWAITING_OAUTH_REFRESH",
                        "publish_at_utc": item["publish_at_utc"],
                        "target_playlist_title": PLAYLIST_TITLE,
                        "assigned_playlists": [SHORTS_SHELF_PLAYLIST_ID, SLEEP_SCIENCE_PLAYLIST_ID],
                        "related_parent_sanctuary_id": item["parent_sanctuary_id"],
                        "related_parent_sanctuary_title": item["parent_sanctuary_title"],
                        "related_parent_sanctuary_youtube_id": p_info.get("youtube_id", ""),
                        "mp4_path": str(STUDIO_SH02_DIR / "masters" / f"{aid}_Master_1080x1920_24p.mp4"),
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            yt_records.append(
                {
                    "asset_id": aid,
                    "youtube_video_id": None,
                    "publish_at_utc": item["publish_at_utc"],
                    "playlist_title": PLAYLIST_TITLE,
                    "parent_sanctuary_id": item["parent_sanctuary_id"],
                    "status": "STAGED_AWAITING_OAUTH_REFRESH",
                }
            )
        batch_manifest["youtube_sync_status"] = "STAGED_AWAITING_OAUTH_REFRESH"

    sh02_tracker["quota_ledger_snapshot"] = hub.youtube.quota.status()
    SH02_TRACKER_PATH.write_text(json.dumps(sh02_tracker, indent=2) + "\n", encoding="utf-8")
    safe_copy_file(SH02_TRACKER_PATH, STUDIO_SH02_DIR / "sh02_tracker.json")

    if SHARED_TRACKER_PATH.exists():
        try:
            shared_tr = json.loads(SHARED_TRACKER_PATH.read_text(encoding="utf-8"))
            if shorts_playlist_id:
                shared_tr.setdefault("official_series_playlists", {})["SH02_SLEEP_SHORTS"] = shorts_playlist_id
            for rec in yt_records:
                aid = rec["asset_id"]
                if aid in shared_tr.get("assets", {}):
                    shared_tr["assets"][aid].update(
                        {
                            "playlist_id": shorts_playlist_id,
                            "parent_sanctuary_youtube_id": rec.get("parent_sanctuary_youtube_id", ""),
                            "upload_staging_state": rec["status"],
                        }
                    )
                    if rec.get("youtube_video_id"):
                        shared_tr["assets"][aid]["state"] = "API_SCHEDULED"
                        shared_tr["assets"][aid]["youtube_video_id"] = rec["youtube_video_id"]
                        shared_tr["assets"][aid]["youtube_url"] = rec["youtube_url"]
            SHARED_TRACKER_PATH.write_text(json.dumps(shared_tr, indent=2) + "\n", encoding="utf-8")
        except Exception as exc:
            print(f"[SH-02 Sync] Note: shared INDEX_Tracker.json update skipped: {exc}", flush=True)

    MANIFEST_PATH.write_text(json.dumps(batch_manifest, indent=2) + "\n", encoding="utf-8")
    safe_copy_file(MANIFEST_PATH, STUDIO_SH02_DIR / "sh02_manifest.json")
    if sh02_drive_folder_id:
        gdrive_upsert_file(hub, MANIFEST_PATH, sh02_drive_folder_id)

    receipt_path = SH02_DIR / "audit_logs" / "SH02_SYNC_RECEIPT.json"
    receipt = {
        "batch_id": "SH-02",
        "playlist_title": PLAYLIST_TITLE,
        "playlist_id": shorts_playlist_id,
        "playlist_url": f"https://www.youtube.com/playlist?list={shorts_playlist_id}" if shorts_playlist_id else None,
        "drive_sh02_folder_id": sh02_drive_folder_id,
        "drive_sh02_folder_url": f"https://drive.google.com/drive/folders/{sh02_drive_folder_id}" if sh02_drive_folder_id else None,
        "youtube_oauth_ready": yt_ready,
        "youtube_oauth_detail": yt_detail,
        "scheduled_count": scheduled_count,
        "quota_deferred_count": quota_deferred_count,
        "quota_ledger": hub.youtube.quota.status(),
        "synced_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "records": yt_records,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    safe_copy_file(receipt_path, STUDIO_SH02_DIR / "audit_logs" / receipt_path.name)
    if sh02_drive_folder_id:
        gdrive_upsert_file(hub, receipt_path, sh02_drive_folder_id)

    # Mirror updated script into studio copies
    this_script = Path(__file__).resolve()
    safe_copy_file(this_script, STUDIO_DIR / "sh02_youtube_drive_sync.py")
    safe_copy_file(this_script, STUDIO_SH02_DIR / "sh02_youtube_drive_sync.py")

    # 4. Clean GitHub commit & push (preserving git status --porcelain working-tree check)
    if not yt_ready:
        commit_msg = "feat(sh-02): add SH-02 Neuro-Acoustic Sleep Sanctuaries Shorts pipeline, manifests, and 6/6 QA_VERIFIED audit logs"
    elif scheduled_count == len(deliverables):
        commit_msg = f"feat(sh-02): schedule 6/6 SH-02 Neuro-Acoustic Sleep Sanctuaries Shorts ({shorts_playlist_id}) & sync Drive/QA logs"
    else:
        commit_msg = (
            f"feat(sh-02): bind live playlist {shorts_playlist_id} & ABR_NS03 (psEs90dgdcU), "
            f"schedule {scheduled_count}/6 Shorts & stage {quota_deferred_count}/6 for PT quota reset"
        )
    commit_hash, git_clean = git_commit_and_push_clean(commit_msg)
    print(f"[SH-02 Sync] GitHub Commit: {commit_hash} | Working tree clean: {git_clean}", flush=True)
    if not git_clean:
        raise RuntimeError("Git working tree is not clean after SH-02 sync!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
