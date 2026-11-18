#!/usr/bin/env python3
"""
SH-01 ("Quiet Wonders & Slow Science — Shorts") Multi-Platform Sync Orchestrator
================================================================================
Cloned and adapted from `ms08_youtube_drive_sync.py` with:
1. Pre-flight 6/6 `QA_VERIFIED` + `music_detected == false` + `TP < -2.0 dBFS` assertion.
2. Idempotent Google Drive mirroring under `SH-01_Quiet_Wonders_Slow_Science_Shorts`
   (parent `1mlAlS_xpEn11gUGyKi_zuQiDZ0Co9Ay9`): uploads all 6 `QA_VERIFIED` MP4 masters,
   posters, thumbnails, per-Short manifests, script/foley sheets, `sh01_manifest.json`,
   and `SH01_Dual_Gate_Audit_Log.json`.
3. YouTube Data API v3 upload, staggered daily `publishAt` scheduling (`2026-11-27`..`2026-12-02`),
   and binding to playlist `"Quiet Wonders & Slow Science — Shorts"` + Shelf 1 (`PLUt7V0-ta200`).
   Gracefully handles OAuth `invalid_grant` without fabricating Video IDs so `--youtube-only`
   resumes cleanly once re-authenticated.
4. Hardened GitHub sync preserving the `git status -uno` working-tree flag fix (`--git-dir` /
   `--work-tree` + `-uno` staged checks) so repository transitions leave `git status` 100% clean.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

STUDIO_DIR = Path("/shared/user/.gemini/raw_video_studio")
WS_ROOT = STUDIO_DIR / "ABR_AntiGravity_Workspace"
GITHUB_REPO = Path("/home/antigravity/awkandari-source/ABR_Anti_Brain_Rot")
REPO_SH01 = GITHUB_REPO / "SH-01"
MEDIA_SH01 = WS_ROOT / "02_Daily_Shorts_Queue" / "SH-01"

MANIFEST_PATH = REPO_SH01 / "sh01_manifest.json"
AUDIT_LOG_PATH = REPO_SH01 / "audit_logs" / "SH01_Dual_Gate_Audit_Log.json"
SYNC_RECEIPT_PATH = REPO_SH01 / "audit_logs" / "SH01_Sync_Receipt.json"

DRIVE_ROOT_ID = "1mlAlS_xpEn11gUGyKi_zuQiDZ0Co9Ay9"
DRIVE_SH01_FOLDER_NAME = "SH-01_Quiet_Wonders_Slow_Science_Shorts"
SHORTS_SHELF_PLAYLIST_ID = "PLUt7V0-ta200"
HISTORY_CORE_PLAYLIST_ID = "PLfO4Y6xIR8iU"
SH01_PLAYLIST_TITLE = "Quiet Wonders & Slow Science — Shorts"

sys.path.insert(0, str(STUDIO_DIR))
from linked_api_hub import LinkedAPIHub, YouTubeQuotaExhaustedError  # type: ignore


def gdrive_extract_id(res: Any) -> str:
    if isinstance(res, dict) and res.get("id"):
        return str(res["id"])
    s = str(res).strip()
    if s.startswith("{"):
        try:
            parsed = json.loads(s)
            if isinstance(parsed, dict) and parsed.get("id"):
                return str(parsed["id"])
        except Exception:
            pass
    # Match gdrive CLI output `... (ID: 1abc...)` or `... (1abc...)`
    import re as _re
    m = _re.findall(r"ID:\s*([A-Za-z0-9_-]{20,})", s)
    if m:
        return m[-1]
    m2 = _re.findall(r"\(([A-Za-z0-9_-]{20,})\)", s)
    if m2:
        return m2[-1]
    return s


def ensure_drive_folder(hub: LinkedAPIHub, name: str, parent_id: str) -> str:
    found = hub.gdrive.search(name, parent_id=parent_id)
    if isinstance(found, list):
        for entry in found:
            if entry.get("name") == name and "folder" in str(entry.get("mimeType", "")):
                return str(entry["id"])
    res = hub.gdrive._run(["mutate", "mkdir", name, "--parent", parent_id], parse_json=False)
    return gdrive_extract_id(res)


def upload_or_replace_drive_file(hub: LinkedAPIHub, local_path: Path, parent_id: str) -> str:
    found = hub.gdrive.search(local_path.name, parent_id=parent_id)
    if isinstance(found, list):
        for entry in found:
            if entry.get("name") == local_path.name and "folder" not in str(entry.get("mimeType", "")):
                fid = str(entry["id"])
                p = subprocess.run(
                    [hub.gdrive.bin_path, "mutate", "update", fid, str(local_path)],
                    capture_output=True,
                    text=True,
                )
                if p.returncode == 0:
                    return fid
    res = hub.gdrive._run(["mutate", "upload", str(local_path), "--parent", parent_id], parse_json=False)
    return gdrive_extract_id(res)


def build_short_description(item: dict[str, Any], playlist_id: str | None) -> str:
    pl_line = (
        f"Explore the Quiet Wonders & Slow Science — Shorts Playlist: https://www.youtube.com/playlist?list={playlist_id}"
        if playlist_id
        else "Part of the Quiet Wonders & Slow Science — Shorts Series on @ABR-AntiBrainRot"
    )
    lines = [
        item["premise_1"],
        item["premise_2"],
        "",
        pl_line,
        "Free 14-Day Family Reset & Screen-Free Parent Kit: https://awkandari-source.github.io/ABR_Anti_Brain_Rot/",
        "Continue into 3-Hour Deep Sleep Nature Ambience (Night Pine Forest): https://www.youtube.com/watch?v=OwMTPuornpo",
        "",
        "ABR Anti-Brain-Rot Audio & Visual Standard:",
        "- 1080x1920 @ 24 fps low-stimulation watercolor macro holds (<= 4 cuts, 1.0s cross-dissolves)",
        "- -14.0 LUFS calm baritone narration over -26.2 LUFS organic environmental foley (>= +30 dB voice separation, 0% music)",
        "",
        f"Primary Sources ({item['primary_source']}):",
        *[f"- {c}" for c in item["citations"]],
        "",
        "Disclosure: ABR Anti-Brain Rot is viewer-supported; any optional family printables follow strict FTC guidelines.",
        "#QuietWonders #SlowScience #AntiBrainRot #ZeroMusic #CalmScience #LowStimulation #shorts",
    ]
    desc = "\n".join(lines)
    if "drive.google.com" in desc.lower():
        raise ValueError(f"Privacy violation: drive.google.com link detected in {item['asset_id']} description!")
    return desc


def ensure_sh01_playlist(hub: LinkedAPIHub) -> str:
    existing = hub.youtube.list_playlists(max_results=50)
    for pl in existing:
        if pl.get("snippet", {}).get("title", "").strip() == SH01_PLAYLIST_TITLE:
            return str(pl["id"])
    desc = (
        "Quiet Wonders & Slow Science — Shorts (Batch SH-01): 60-second low-stimulation vertical "
        "explorations of deep-time biology, slow physics, historical engineering, gentle winter nature, "
        "medieval timekeeping, and restorative neuroscience. Engineered at 24 fps with <= 4 cuts, "
        "-14.0 LUFS calm narration, >= +30 dB voice-over-foley separation, and strictly 0% music."
    )
    res = hub.youtube.request(
        "POST",
        "playlists",
        params={"part": "snippet,status"},
        json_body={
            "snippet": {"title": SH01_PLAYLIST_TITLE, "description": desc},
            "status": {"privacyStatus": "public"},
        },
    )
    return str(res["id"])


def run_git(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    cmd = [
        "git",
        f"--git-dir={GITHUB_REPO / '.git'}",
        f"--work-tree={GITHUB_REPO}",
        *args,
    ]
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def sync_github_cleanly(commit_msg: str) -> tuple[str, str]:
    """
    Stages SH-01 scripts, manifests, and audit reports (plus ABR_Anti_Brain_Rot_Index.md if updated),
    uses `-uno` tracked working-tree check + `--cached` diff check to prevent untracked-file commit errors,
    pushes to origin/main, and verifies `git status --porcelain` is clean.
    """
    run_git(["add", "SH-01", "ABR_Anti_Brain_Rot_Index.md"])
    tracked_status = run_git(["status", "--porcelain", "-uno"]).stdout.strip()
    staged_diff = run_git(["diff", "--cached", "--quiet"], check=False)

    if tracked_status and staged_diff.returncode != 0:
        run_git(["commit", "-m", commit_msg])
        pull_res = run_git(["pull", "--rebase", "--autostash", "origin", "main"], check=False)
        if pull_res.returncode != 0:
            raise RuntimeError(f"git pull --rebase failed:\n{pull_res.stderr or pull_res.stdout}")
        run_git(["push", "origin", "HEAD:main"])

    head_sha = run_git(["rev-parse", "HEAD"]).stdout.strip()
    full_porcelain = run_git(["status", "--porcelain"]).stdout.strip()
    return head_sha, full_porcelain


def update_master_index_if_scheduled(all_rows: list[dict[str, Any]], playlist_id: str, drive_folder_id: str) -> None:
    if not all_rows:
        return
    import re as _re
    idx_md_path = GITHUB_REPO / "ABR_Anti_Brain_Rot_Index.md"
    md_text = idx_md_path.read_text(encoding="utf-8")
    block_lines = [
        "<!-- SH01_INDEX_START -->",
        "### 3.0 Batch SH-01: *Quiet Wonders & Slow Science — Shorts* (`9:16` 60s @ `24/1` fps Zero-Music)",
        "",
        f"- **Official Shorts Playlist:** [`{playlist_id}`](https://www.youtube.com/playlist?list={playlist_id})",
        f"- **Google Drive Batch Folder ID:** `{drive_folder_id}`",
        "",
        "| Asset ID | Short Title | Runtime | Voice Sep | Schedule (`UTC`) | YouTube ID | Drive Folder ID |",
        "| :--- | :--- | :---: | :--- | :--- | :--- | :--- |",
    ]
    for r in all_rows:
        t_esc = r["title"].replace("|", "\\|")
        yt_cell = (
            f"[`{r['youtube_video_id']}`]({r['shorts_url']})"
            if r.get("youtube_video_id")
            else f"`{r['youtube_sync_status']}`"
        )
        sched_label = "**Scheduled**" if r.get("youtube_video_id") else "**Queued (Next Quota Reset)**"
        block_lines.append(
            f"| `{r['asset_id']}` | *{t_esc}* | `60s` | **`+{r['voice_sep_db']} dB`** (`0%` Music) | "
            f"{sched_label} (`{r['publish_at_utc']}`) | {yt_cell} | `{r['asset_drive_folder_id']}` |"
        )
    block_lines.append("<!-- SH01_INDEX_END -->")
    new_block = "\n".join(block_lines)

    if "<!-- SH01_INDEX_START -->" in md_text and "<!-- SH01_INDEX_END -->" in md_text:
        md_text = _re.sub(
            r"<!-- SH01_INDEX_START -->.*?<!-- SH01_INDEX_END -->",
            new_block,
            md_text,
            count=1,
            flags=_re.DOTALL,
        )
        idx_md_path.write_text(md_text, encoding="utf-8")
        return

    m = _re.search(r"^## 3\. Complete `9:16` Zero-Music Shorts Catalog.*$", md_text, flags=_re.MULTILINE)
    if m:
        anchor_line = m.group(0)
        md_text = md_text.replace(anchor_line, anchor_line + "\n\n" + new_block, 1)
        idx_md_path.write_text(md_text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--youtube-only", action="store_true", help="Skip re-uploading already mirrored Drive files")
    args = ap.parse_args()

    hub = LinkedAPIHub()
    batch_manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    deliverables: list[dict[str, Any]] = batch_manifest["deliverables"]

    # 1. Pre-flight verification across all 6 Shorts
    for item in deliverables:
        aid = item["asset_id"]
        per_m = REPO_SH01 / "manifests" / f"{aid}_Manifest.json"
        if not per_m.exists():
            raise RuntimeError(f"Missing per-Short manifest: {per_m}")
        mdoc = json.loads(per_m.read_text(encoding="utf-8"))
        if mdoc.get("state") not in ("QA_VERIFIED", "API_SCHEDULED", "DRIVE_SYNCED_PENDING_YT_OAUTH"):
            raise RuntimeError(f"Asset {aid} is not QA_VERIFIED (state={mdoc.get('state')})!")
        if mdoc.get("sop03_verification", {}).get("CHK-04", {}).get("music_detected") is not False:
            raise RuntimeError(f"Asset {aid} failed zero-music assertion!")
        if float(mdoc.get("qc_gate_audit", {}).get("master_loudness", {}).get("true_peak_dbfs", 0.0)) >= -2.0:
            raise RuntimeError(f"Asset {aid} violated True Peak < -2.0 dBFS ceiling!")

    # 2. Check YouTube OAuth live readiness
    yt_ready = False
    yt_auth_error: str | None = None
    quota_note: str | None = None
    playlist_id: str | None = batch_manifest.get("youtube_playlist_id")
    try:
        ch_info = hub.youtube.get_channel_overview()
        print(f"[SH-01 Sync] YouTube OAuth ACTIVE for {ch_info.get('title')} ({ch_info.get('channel_id')})", flush=True)
        yt_ready = True
        playlist_id = ensure_sh01_playlist(hub)
        batch_manifest["youtube_playlist_id"] = playlist_id
        batch_manifest["youtube_playlist_url"] = f"https://www.youtube.com/playlist?list={playlist_id}"
        MANIFEST_PATH.write_text(json.dumps(batch_manifest, indent=2) + "\n", encoding="utf-8")
        print(f"[SH-01 Sync] Bound Playlist '{SH01_PLAYLIST_TITLE}': {playlist_id}", flush=True)
    except Exception as exc:
        yt_auth_error = str(exc)
        print(f"[SH-01 Sync] YouTube OAuth unavailable ({yt_auth_error}). Proceeding with 100% Drive + GitHub sync and staging YouTube schedule.", flush=True)

    # 3. Mirror all 6 QA_VERIFIED MP4 masters + manifests + audit logs to Google Drive SH-01 folder
    cached_dfid = batch_manifest.get("drive_folder_id")
    if cached_dfid and cached_dfid != DRIVE_SH01_FOLDER_NAME:
        sh01_drive_folder_id = cached_dfid
    else:
        sh01_drive_folder_id = ensure_drive_folder(hub, DRIVE_SH01_FOLDER_NAME, DRIVE_ROOT_ID)
    sh01_drive_url = f"https://drive.google.com/drive/folders/{sh01_drive_folder_id}"
    batch_manifest["drive_folder_id"] = sh01_drive_folder_id
    batch_manifest["drive_folder_url"] = sh01_drive_url
    print(f"[SH-01 Sync] Google Drive SH-01 Root Folder: {sh01_drive_folder_id} ({sh01_drive_url})", flush=True)

    scheduled_rows: list[dict[str, Any]] = []
    sync_items_summary: list[dict[str, Any]] = []

    for item in deliverables:
        aid = item["asset_id"]
        mp4_path = Path(item["mp4_path"])
        poster_path = Path(item["poster_path"])
        thumb_path = Path(item["thumb_path"])
        per_m_path = REPO_SH01 / "manifests" / f"{aid}_Manifest.json"
        md_path = REPO_SH01 / "manifests" / f"{aid}_Script_Foley.md"
        mdoc = json.loads(per_m_path.read_text(encoding="utf-8"))

        # Upload asset bundle to Drive subfolder if not already mirrored
        existing_drv = mdoc.get("drive_archive", {})
        if args.youtube_only and existing_drv.get("files", {}).get("master_mp4"):
            sub_folder_id = existing_drv["asset_drive_folder_id"]
            drv_files = existing_drv["files"]
            print(f"[{aid}] Reusing mirrored Drive subfolder {sub_folder_id}", flush=True)
        else:
            sub_name = f"{aid}_{item['publish_at_utc'][:10]}"
            sub_folder_id = ensure_drive_folder(hub, sub_name, sh01_drive_folder_id)
            print(f"[{aid}] Uploading {mp4_path.name}, poster, thumbnail, stems & script to Drive {sub_folder_id}...", flush=True)
            voice_stem_path = MEDIA_SH01 / "stems" / aid / "Voice_Stem.wav"
            foley_stem_path = MEDIA_SH01 / "stems" / aid / "Foley_Ducked_Stem.wav"
            drv_files = {
                "master_mp4": upload_or_replace_drive_file(hub, mp4_path, sub_folder_id),
                "poster_1080x1920_jpg": upload_or_replace_drive_file(hub, poster_path, sub_folder_id),
                "thumbnail_1280x720_jpg": upload_or_replace_drive_file(hub, thumb_path, sub_folder_id),
                "voice_stem_wav": upload_or_replace_drive_file(hub, voice_stem_path, sub_folder_id),
                "foley_ducked_stem_wav": upload_or_replace_drive_file(hub, foley_stem_path, sub_folder_id),
                "script_foley_md": upload_or_replace_drive_file(hub, md_path, sub_folder_id),
            }

        desc = build_short_description(item, playlist_id)
        vid_id = mdoc.get("youtube_routing", {}).get("youtube_video_id")
        shorts_url = f"https://www.youtube.com/shorts/{vid_id}" if vid_id else None
        yt_item_status = "API_SCHEDULED" if vid_id else ("READY_TO_UPLOAD" if yt_ready else "OAUTH_REFRESH_REQUIRED")

        assigned_pls = [pl for pl in [playlist_id, SHORTS_SHELF_PLAYLIST_ID] if pl]
        if item["category"] in ("Historical Engineering", "Historical Timekeeping", "Deep-Time Biology"):
            assigned_pls.append(HISTORY_CORE_PLAYLIST_ID)

        if yt_ready and not vid_id:
            try:
                print(f"[{aid}] Uploading vertical Short to @ABR-AntiBrainRot -> publishAt={item['publish_at_utc']}...", flush=True)
                up_res = hub.youtube.upload_video(
                    mp4_path,
                    title=item["youtube_title"],
                    description=desc,
                    tags=item["tags"],
                    category_id="27",
                    privacy_status="private",
                    publish_at_iso=item["publish_at_utc"],
                    made_for_kids=False,
                )
                vid_id = str(up_res["id"])
                shorts_url = f"https://www.youtube.com/shorts/{vid_id}"
                yt_item_status = "API_SCHEDULED"
                assert playlist_id is not None
                hub.youtube.add_to_playlist(playlist_id, vid_id, position=int(item["position"]))
                hub.youtube.add_to_playlist(SHORTS_SHELF_PLAYLIST_ID, vid_id)
                print(f"[{aid}] SCHEDULED -> {shorts_url} ({item['publish_at_utc']}) | Bound to playlist {playlist_id}", flush=True)
            except YouTubeQuotaExhaustedError as q_exc:
                next_rst = hub.youtube.quota.next_reset_utc()
                quota_note = f"{q_exc} (next PT quota reset: {next_rst})"
                yt_item_status = "QUOTA_CAP_QUEUED_NEXT_RESET"
                print(f"[{aid}] QuotaLedger 9,200-unit daily production cap reached ({quota_note}); staged for automatic release on next reset.", flush=True)

        sweeper_dir = STUDIO_DIR / item["slug"]
        sweeper_dir.mkdir(parents=True, exist_ok=True)
        sweeper_meta = {
            "slug": item["slug"],
            "asset_id": aid,
            "title": item["youtube_title"],
            "pillar": item["pillar"],
            "format": "9:16_YOUTUBE_SHORT",
            "youtube_video_id": vid_id,
            "youtube_url": shorts_url,
            "watch_url": f"https://www.youtube.com/watch?v={vid_id}" if vid_id else None,
            "status": yt_item_status,
            "publish_at_utc": item["publish_at_utc"],
            "youtube_status": {
                "uploadStatus": "uploaded" if vid_id else "queued_next_quota_reset",
                "privacyStatus": "private",
                "publishAt": item["publish_at_utc"],
                "selfDeclaredMadeForKids": False,
            },
            "playlist_id": playlist_id,
            "assigned_playlists": assigned_pls,
            "question_hook": item["question_hook"],
            "post_publish_swept": False,
            "mp4_path": str(mp4_path),
            "drive_root_folder_id": DRIVE_ROOT_ID,
            "drive_archive_folder_id": sub_folder_id,
            "drive_archive_url": f"https://drive.google.com/drive/folders/{sub_folder_id}",
        }
        (sweeper_dir / "youtube_publish_metadata.json").write_text(json.dumps(sweeper_meta, indent=2) + "\n")

        new_state = "API_SCHEDULED" if vid_id else "QA_VERIFIED"
        mdoc["state"] = new_state
        mdoc["youtube_routing"].update({
            "privacy_status": "private",
            "publish_at_utc": item["publish_at_utc"],
            "playlist_title": SH01_PLAYLIST_TITLE,
            "series_playlist_id": playlist_id,
            "shelf_playlist_id": SHORTS_SHELF_PLAYLIST_ID,
            "made_for_kids": False,
            "youtube_video_id": vid_id,
            "shorts_url": shorts_url,
            "youtube_sync_status": yt_item_status,
            "prepared_description": desc,
        })
        mdoc["drive_archive"] = {
            "batch_drive_folder_id": sh01_drive_folder_id,
            "batch_drive_url": sh01_drive_url,
            "asset_drive_folder_id": sub_folder_id,
            "asset_drive_url": f"https://drive.google.com/drive/folders/{sub_folder_id}",
            "files": drv_files,
        }
        per_m_path.write_text(json.dumps(mdoc, indent=2) + "\n", encoding="utf-8")
        drv_files["manifest_json"] = upload_or_replace_drive_file(hub, per_m_path, sub_folder_id)
        per_m_path.write_text(json.dumps(mdoc, indent=2) + "\n", encoding="utf-8")
        shutil.copyfile(per_m_path, MEDIA_SH01 / "manifests" / per_m_path.name)

        item["state"] = new_state
        item["youtube_video_id"] = vid_id
        item["shorts_url"] = shorts_url
        item["youtube_sync_status"] = yt_item_status
        item["drive_archive"] = mdoc["drive_archive"]

        rec = {
            "asset_id": aid,
            "title": item["title"],
            "youtube_title": item["youtube_title"],
            "publish_at_utc": item["publish_at_utc"],
            "youtube_video_id": vid_id,
            "shorts_url": shorts_url,
            "youtube_sync_status": yt_item_status,
            "asset_drive_folder_id": sub_folder_id,
            "master_mp4_drive_id": drv_files["master_mp4"],
            "voice_sep_db": mdoc["stream_metrics"]["net_voice_separation_db"],
        }
        sync_items_summary.append(rec)
        if vid_id:
            scheduled_rows.append(rec)

    # Save updated sh01_manifest.json and mirror batch manifest + audit log to SH-01 Drive root
    if len(scheduled_rows) == 6:
        batch_manifest["youtube_sync_status"] = "ALL_6_SCHEDULED"
    elif len(scheduled_rows) > 0:
        batch_manifest["youtube_sync_status"] = f"SCHEDULED_{len(scheduled_rows)}_OF_6_QUOTA_QUEUED_{6 - len(scheduled_rows)}"
    else:
        batch_manifest["youtube_sync_status"] = "PENDING_OAUTH_REFRESH"
    if yt_auth_error:
        batch_manifest["youtube_oauth_note"] = yt_auth_error
    else:
        batch_manifest.pop("youtube_oauth_note", None)
    if quota_note:
        batch_manifest["youtube_quota_note"] = quota_note
    batch_manifest["drive_sync_status"] = "MIRRORED_6_OF_6"
    MANIFEST_PATH.write_text(json.dumps(batch_manifest, indent=2) + "\n", encoding="utf-8")
    shutil.copyfile(MANIFEST_PATH, MEDIA_SH01 / "sh01_manifest.json")

    manifest_drv_id = upload_or_replace_drive_file(hub, MANIFEST_PATH, sh01_drive_folder_id)
    audit_drv_id = upload_or_replace_drive_file(hub, AUDIT_LOG_PATH, sh01_drive_folder_id)
    print(f"[SH-01 Sync] Mirrored sh01_manifest.json ({manifest_drv_id}) & audit log ({audit_drv_id}) to Drive.", flush=True)

    if len(scheduled_rows) >= 1 and playlist_id:
        update_master_index_if_scheduled(sync_items_summary, playlist_id, sh01_drive_folder_id)

    q_state = hub.youtube.quota._load_today()
    receipt = {
        "batch_id": "SH-01",
        "playlist_title": SH01_PLAYLIST_TITLE,
        "youtube_playlist_id": playlist_id,
        "youtube_playlist_url": f"https://www.youtube.com/playlist?list={playlist_id}" if playlist_id else None,
        "youtube_sync_status": batch_manifest["youtube_sync_status"],
        "youtube_oauth_error": yt_auth_error,
        "youtube_quota_note": quota_note,
        "quota_ledger_units_used": q_state.get("units_used"),
        "quota_ledger_production_soft_cap": q_state.get("production_soft_cap"),
        "quota_ledger_next_reset_utc": hub.youtube.quota.next_reset_utc(),
        "drive_folder_id": sh01_drive_folder_id,
        "drive_folder_url": sh01_drive_url,
        "drive_manifest_file_id": manifest_drv_id,
        "drive_audit_log_file_id": audit_drv_id,
        "synced_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "assets": sync_items_summary,
    }
    SYNC_RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    shutil.copyfile(SYNC_RECEIPT_PATH, MEDIA_SH01 / "audit_logs" / SYNC_RECEIPT_PATH.name)
    upload_or_replace_drive_file(hub, SYNC_RECEIPT_PATH, sh01_drive_folder_id)

    # 4. Commit and push cleanly to GitHub (preserving -uno working-tree check)
    commit_msg = (
        f"feat(sh-01): schedule Batch SH-01 Shorts on @ABR-AntiBrainRot and sync indices ({batch_manifest['youtube_sync_status']})"
    )
    head_sha, porcelain = sync_github_cleanly(commit_msg)
    print(f"[SH-01 Sync] GitHub HEAD: {head_sha} | git status clean: {porcelain == ''}", flush=True)
    if porcelain:
        raise RuntimeError(f"Git working tree not clean after sync:\n{porcelain}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
