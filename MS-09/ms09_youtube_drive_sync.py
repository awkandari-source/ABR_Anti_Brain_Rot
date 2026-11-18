#!/usr/bin/env python3
"""
MS-09 ("Earth's Slowest Clocks — Volume II") Multi-Platform Sync Orchestrator
=============================================================================
Adapted from `ms08_youtube_drive_sync.py` for isolated workspace `MS-09`
(leaving all `MS-08` files and artifacts completely untouched):
1. Pre-flight Dual-Gate QA verification across all 6 deliverables (`MS09_E01`..`MS09_E05`
   and `MS09_COMP_75m_FullSeries.mp4`), asserting `QA_VERIFIED` / `API_SCHEDULED`,
   `music_detected == False`, True Peak `< -2.0 dBFS`, and `>= +30.0 dB` voice separation.
2. Idempotent Google Drive Volume II archive sync (`--drive-only` or full mode):
   syncs all 6 `QA_VERIFIED` MP4 masters, thumbnails, scripts, individual manifests,
   `ms09_manifest.json`, and `gate_audit_reports/*.json` to `MS09_Earths_Slowest_Clocks_Vol2`
   under Google Drive root folder `1mlAlS_xpEn11gUGyKi_zuQiDZ0Co9Ay9`.
3. Quota-governed YouTube Data API v3 upload, scheduling (`publishAt`), and official
   playlist binding (`Earth's Slowest Clocks — Volume II`) on `@ABR-AntiBrainRot`
   within the daily 10,000-unit `QuotaLedger` budget (`51 + 9,600 + 300 = 9,951` units),
   with graceful sweeper deferral (`youtube_publish_metadata.json`) if optional
   thumbnail/secondary-shelf calls hit the daily quota ceiling.
4. Updates `ABR_Anti_Brain_Rot_Videos_Index.csv`, `INDEX_Tracker.json`, and
   `ABR_Anti_Brain_Rot_Index.md` locally + on Google Drive `01 Baseline`, and commits/pushes
   all `MS-09` scripts, manifests, and audit logs cleanly to GitHub (`git status --porcelain` empty).
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

sys.path.insert(0, "/shared/user/.gemini/raw_video_studio")
from linked_api_hub import LinkedAPIHub, YouTubeQuotaExhaustedError

STUDIO_DIR = Path("/shared/user/.gemini/raw_video_studio")
WORKSPACE = Path("/home/antigravity/ABR_AntiGravity_Workspace")
BASELINE_DIR = Path("/home/antigravity/01 Baseline")
GITHUB_REPO = Path("/home/antigravity/awkandari-source/ABR_Anti_Brain_Rot")
GITHUB_MS09_DIR = GITHUB_REPO / "MS-09"
SERIES_DIR = Path("/home/antigravity/MS-09")

DRIVE_ROOT_ID = "1mlAlS_xpEn11gUGyKi_zuQiDZ0Co9Ay9"
DRIVE_BASELINE_FOLDER_ID = "1wM-kzfBfWaZF0QnnjOwI-UAOB9Vdf4by"
DRIVE_CSV_FILE_ID = "1oW7pcWZeFF9Y2DKUzazDlftBadIOyL3R"
DRIVE_TRACKER_FILE_ID = "1wVzUDCNGIfLPuo7AgX1R-0_wBjKZwnVp"
DRIVE_INDEX_MD_FILE_ID = "1h1ooQbmzyjdGZZh1JfbgMb5ySNj0KZUT"
DRIVE_SERIES_FOLDER_NAME = "MS09_Earths_Slowest_Clocks_Vol2"

HISTORY_CORE_PLAYLIST_ID = "PLfO4Y6xIR8iU"
SEASON1_PLAYLIST_ID = "PLdWSOapYjkZc"
SERIES_TITLE = "Earth's Slowest Clocks — Volume II"
SERIES_PLAYLIST_TITLE = "Earth's Slowest Clocks — Volume II"

GDRIVE_BIN = "/opt/antigravity/plugins/gdrive/skills/gdrive/scripts/gdrive"

MS09_UPLOAD_PLAN: list[dict[str, Any]] = [
    {
        "asset_id": "MS09_E01",
        "slug": "MS09_E01_500_Year_Clams_North_Atlantic",
        "position": 0,
        "title": "Earth's Slowest Clocks Vol. II Ep. 1: The 500-Year Clams of the North Atlantic | 15-Min Calm Documentary",
        "youtube_title": "Earth's Slowest Clocks Vol. II Ep. 1: 500-Year Clams of the North Atlantic | Calm Documentary",
        "publish_at": "2026-12-01T15:00:00Z",
        "duration_display": "15:01",
        "mp4_path": SERIES_DIR / "MS09_E01" / "MS09_E01_15m_Master.mp4",
        "thumb_path": SERIES_DIR / "MS09_E01" / "MS09_E01_Thumbnail_1280x720.jpg",
        "manifest_path": SERIES_DIR / "MS09_E01" / "MS09_E01_Manifest.json",
        "script_path": SERIES_DIR / "MS09_E01" / "MS09_E01_Script_Foley.md",
        "audit_path": SERIES_DIR / "gate_audit_reports" / "MS09_E01_dual_gate_audit.json",
        "premise_1": "Eighty meters beneath the cold North Icelandic Shelf, ocean quahog clams (Arctica islandica) lay down one microscopic band of aragonite crystal each year across more than five centuries.",
        "premise_2": "Unwind with Episode 1 of Earth's Slowest Clocks — Volume II: a 15-minute low-stimulation marine sclerochronology documentary narrated over cold North Atlantic deep currents, soft seabed gravel shifts, and distant wooden hull creaks with 0% music.",
        "chapters": [
            "00:00 Cold North Icelandic Shelf & Living Seabed Gravel",
            "02:15 Sclerochronology: Reading Annual Aragonite Growth Increments",
            "06:15 Ming the 507-Year Clam & Cross-Dating a 1,357-Year Ocean Archive",
            "10:00 Oxygen-18 Isotopes, Volcanic Cooling & the Little Ice Age",
            "12:45 Metabolic Stillness & Bridge to Japan's Lake Suigetsu",
            "15:00 Deep North Atlantic Current Calm",
        ],
        "citations": [
            "NOAA National Centers for Environmental Information (NCEI) Paleoclimatology Study 14609: North Icelandic Shelf 1,357-Year Arctica islandica Master Shell Chronology. https://www.ncei.noaa.gov/access/paleo-search/study/14609",
            "Butler, P. G., Wanamaker, A. D., Scourse, J. D., Richardson, C. A., & Reynolds, D. J. (2013). Variability of marine climate on the North Icelandic Shelf in a 1357-year proxy archive based on growth increments in the bivalve Arctica islandica. Palaeogeography, Palaeoclimatology, Palaeoecology, 373, 141-151. https://doi.org/10.1016/j.palaeo.2012.01.016",
        ],
        "question_hook": "Imagine a living shell quietly recording every winter on the North Atlantic seafloor from 1499 to today—which century in that 507-year span fascinates you most? When you're ready for uninterrupted sleep, drift into our 3-Hour Midnight Ocean Waves Soundscape (https://www.youtube.com/watch?v=xcAo79qLcLc).",
        "tags": [
            "arctica islandica", "500 year old clam", "sclerochronology",
            "earth slowest clocks", "calm ocean documentary", "no music documentary",
            "paleoclimatology", "sleep science documentary", "anti brain rot", "deep time",
        ],
    },
    {
        "asset_id": "MS09_E02",
        "slug": "MS09_E02_Lake_Suigetsu_50000_Year_Mud_Calendar",
        "position": 1,
        "title": "Earth's Slowest Clocks Vol. II Ep. 2: Lake Suigetsu & The 50,000-Year Mud Calendar | 15-Min Calm Documentary",
        "youtube_title": "Earth's Slowest Clocks Vol. II Ep. 2: Lake Suigetsu & The 50,000-Year Mud Calendar | Documentary",
        "publish_at": "2026-12-04T15:00:00Z",
        "duration_display": "15:01",
        "mp4_path": SERIES_DIR / "MS09_E02" / "MS09_E02_15m_Master.mp4",
        "thumb_path": SERIES_DIR / "MS09_E02" / "MS09_E02_Thumbnail_1280x720.jpg",
        "manifest_path": SERIES_DIR / "MS09_E02" / "MS09_E02_Manifest.json",
        "script_path": SERIES_DIR / "MS09_E02" / "MS09_E02_Script_Foley.md",
        "audit_path": SERIES_DIR / "gate_audit_reports" / "MS09_E02_dual_gate_audit.json",
        "premise_1": "Beneath the sheltered, oxygen-free waters of Lake Suigetsu on Japan's Wakasa Bay coast, seasonal diatom blooms and winter clay settle undisturbed into sub-millimeter annual varve couplets spanning more than 50,000 years.",
        "premise_2": "Explore Episode 2 of Earth's Slowest Clocks — Volume II: narrated in calm baritone over gentle lake shoreline ripples, soft rain on still water, and subtle underwater silt settling with strictly zero music.",
        "chapters": [
            "00:00 Dawn Mist Over Sheltered Lake Suigetsu, Japan",
            "02:15 Meromictic Stillness & Seasonal Diatom-Clay Varve Couplets",
            "06:15 Overlapping Sediment Cores & Preserved Autumn Leaves",
            "10:00 Calibrating the 50,000-Year IntCal Radiocarbon Ruler",
            "12:45 Evening Rain on Still Water & Bridge to Coastal Chalk Cliffs",
            "15:00 Quiet Lakebed Settling",
        ],
        "citations": [
            "Bronk Ramsey, C., Staff, R. A., Bryant, C. L., Brock, F., Kitagawa, H., van der Plicht, J., Schlolaut, G., Marshall, M. H., Brauer, A., Lamb, H. F., Payne, R. L., Tarasov, P. E., Haraguchi, T., Gotanda, K., Yonenobu, H., Yokoyama, Y., Tada, R., & Nakagawa, T. (2012). A Complete Terrestrial Radiocarbon Record for 11.2 to 52.8 kyr B.P. Science, 338(6105), 370-374. https://doi.org/10.1126/science.1226660",
            "Nakagawa, T., Gotanda, K., Haraguchi, T., Danhara, T., Yonenobu, H., Brauer, A., Yokoyama, Y., Tada, R., Takemura, K., Staff, R. A., Payne, R., Bronk Ramsey, C., Bryant, C., Brock, F., Schlolaut, G., Marshall, M., Tarasov, P., & Lamb, H. (2012). SG06, a fully continuous and varved sediment core from Lake Suigetsu, Japan: stratigraphy and potential for improving the radiocarbon calibration model and understanding of late Quaternary climate changes. Quaternary Science Reviews / Cambridge Core Radiocarbon Chronology, 36, 164-176.",
        ],
        "question_hook": "Every paper-thin pair of pale diatom silica and dark winter clay at the bottom of Lake Suigetsu holds a single year of quiet weather—how does a 50,000-page mud calendar feel compared to a busy week? Drift into sleep afterward with our 3-Hour Clearing Dusk Rain Soundscape (https://www.youtube.com/watch?v=cuEEJ6NH-tE).",
        "tags": [
            "lake suigetsu", "varve chronology", "radiocarbon calibration",
            "50000 year calendar", "calm geology documentary", "no music documentary",
            "earth slowest clocks", "sleep documentary", "anti brain rot", "deep time",
        ],
    },
    {
        "asset_id": "MS09_E03",
        "slug": "MS09_E03_Chalk_Cliffs_100000_Year_Orbital_Pendulum",
        "position": 2,
        "title": "Earth's Slowest Clocks Vol. II Ep. 3: Chalk Cliffs & Earth's 100,000-Year Orbital Pendulum | 15-Min Calm Documentary",
        "youtube_title": "Earth's Slowest Clocks Vol. II Ep. 3: Chalk Cliffs & Earth's 100,000-Year Orbital Pendulum",
        "publish_at": "2026-12-08T15:00:00Z",
        "duration_display": "15:01",
        "mp4_path": SERIES_DIR / "MS09_E03" / "MS09_E03_15m_Master.mp4",
        "thumb_path": SERIES_DIR / "MS09_E03" / "MS09_E03_Thumbnail_1280x720.jpg",
        "manifest_path": SERIES_DIR / "MS09_E03" / "MS09_E03_Manifest.json",
        "script_path": SERIES_DIR / "MS09_E03" / "MS09_E03_Script_Foley.md",
        "audit_path": SERIES_DIR / "gate_audit_reports" / "MS09_E03_dual_gate_audit.json",
        "premise_1": "Along pale Cretaceous coastal bluffs, rhythmic bands of microscopic coccolith chalk, grey marl, and dark flint nodules preserve the slow gravitational heartbeat of Earth's orbital eccentricity and axial tilt.",
        "premise_2": "Settle into Episode 3 of Earth's Slowest Clocks — Volume II: narrated over steady coastal breeze across chalk bluffs, slow ocean swells, and distant gull calls with 0% background music.",
        "chapters": [
            "00:00 Pale Coastal Chalk Bluffs & Slow Swells",
            "02:15 Microscopic Coccolithophore Marine Snow & Cretaceous Seas",
            "06:15 Milutin Milankovitch: Precession, Axial Tilt & 100,000-Year Eccentricity",
            "10:00 Chalk-Marl Couplets, Flint Horizons & Astrochronology",
            "12:45 Celestial Metronome Wind-Down & Bridge to the Mid-Ocean Ridge",
            "15:00 Evening Chalk Headland Breeze",
        ],
        "citations": [
            "NASA Earth Science — Milankovitch (Orbital) Cycles and Their Role in Earth's Climate. https://science.nasa.gov/science-research/earth-science/milankovitch-orbital-cycles-and-their-role-in-earths-climate/",
            "Gale, A. S., Hardenbol, J., Hathway, B., Kennedy, W. J., Young, J. R., & Phansalkar, V. (2002). Global correlation of Cenomanian (Upper Cretaceous) sequences: Evidence for Milankovitch control on sea level. Geology, 30(4), 291-294. https://doi.org/10.1130/0091-7613(2002)030%3C0291:GCOCUC%3E2.0.CO;2",
        ],
        "question_hook": "Looking up at a white chalk cliff knowing its horizontal bands mirror Jupiter and Saturn gently tugging Earth's orbit every 100,000 years—what detail stood out most to you tonight? Continue resting with our 3-Hour Ebbing Tide Pool Soundscape (https://www.youtube.com/watch?v=iLX9zmr9VEU).",
        "tags": [
            "milankovitch cycles", "chalk cliffs geology", "orbital eccentricity",
            "cyclostratigraphy", "calm earth science documentary", "no music sleep documentary",
            "earth slowest clocks", "anti brain rot", "deep time",
        ],
    },
    {
        "asset_id": "MS09_E04",
        "slug": "MS09_E04_Magnetic_Stripes_Ocean_Floor_Tape_Recorder",
        "position": 3,
        "title": "Earth's Slowest Clocks Vol. II Ep. 4: Magnetic Stripes & The Ocean Floor Tape Recorder | 15-Min Documentary",
        "youtube_title": "Earth's Slowest Clocks Vol. II Ep. 4: Magnetic Stripes & The Ocean Floor Tape Recorder",
        "publish_at": "2026-12-11T15:00:00Z",
        "duration_display": "15:01",
        "mp4_path": SERIES_DIR / "MS09_E04" / "MS09_E04_15m_Master.mp4",
        "thumb_path": SERIES_DIR / "MS09_E04" / "MS09_E04_Thumbnail_1280x720.jpg",
        "manifest_path": SERIES_DIR / "MS09_E04" / "MS09_E04_Manifest.json",
        "script_path": SERIES_DIR / "MS09_E04" / "MS09_E04_Script_Foley.md",
        "audit_path": SERIES_DIR / "gate_audit_reports" / "MS09_E04_dual_gate_audit.json",
        "premise_1": "Along Earth's 65,000-kilometer mid-ocean ridge system, cooling pillow basalts lock titanomagnetite crystals below the Curie point—archiving 180 million years of geomagnetic polarity reversals in twin seafloor stripes.",
        "premise_2": "Experience Episode 4 of Earth's Slowest Clocks — Volume II: paired with a low abyssal current hum, distant hydrothermal vent rumble, and subtle mineral cooling crackles with 0% music.",
        "chapters": [
            "00:00 Descending Into the Mid-Ocean Axial Rift Valley",
            "02:15 Pillow Basalt Glass & Locking the 580 C Curie Point",
            "06:15 Vine, Matthews & Symmetrical Magnetic Stripes Across Reykjanes Ridge",
            "10:00 Reading 180 Million Years of Seafloor Spreading & the Brunhes Reversal",
            "12:45 Abyssal Crustal Drift & Bridge to Shark Bay's Living Stromatolites",
            "15:00 Deep Abyssal Current Stillness",
        ],
        "citations": [
            "USGS — Kious, W. J., & Tilling, R. I. This Dynamic Earth: The Story of Plate Tectonics (Developing the Theory: Seafloor Spreading & Magnetic Stripes). U.S. Geological Survey. https://pubs.usgs.gov/gip/dynamic/developing.html",
            "Vine, F. J., & Matthews, D. H. (1963). Magnetic anomalies over oceanic ridges. Nature, 199(4897), 947-949. https://doi.org/10.1038/199947a0",
        ],
        "question_hook": "The Atlantic Ocean widens at roughly the speed your fingernails grow, writing Earth's magnetic field into solid basalt millimeter by millimeter—does that slow planetary pace feel grounding tonight? Drift deeper with our 3-Hour Midnight Ocean Waves Soundscape (https://www.youtube.com/watch?v=xcAo79qLcLc).",
        "tags": [
            "magnetic stripes seafloor", "seafloor spreading", "vine and matthews",
            "geomagnetic reversal", "mid ocean ridge documentary", "calm geology no music",
            "earth slowest clocks", "sleep documentary", "anti brain rot", "deep time",
        ],
    },
    {
        "asset_id": "MS09_E05",
        "slug": "MS09_E05_Stromatolites_3_5_Billion_Year_Living_Stone",
        "position": 4,
        "title": "Earth's Slowest Clocks Vol. II Ep. 5: Stromatolites — The 3.5-Billion-Year Living Stone | 15-Min Finale",
        "youtube_title": "Earth's Slowest Clocks Vol. II Ep. 5: Stromatolites — The 3.5-Billion-Year Living Stone | Finale",
        "publish_at": "2026-12-15T15:00:00Z",
        "duration_display": "15:01",
        "mp4_path": SERIES_DIR / "MS09_E05" / "MS09_E05_15m_Master.mp4",
        "thumb_path": SERIES_DIR / "MS09_E05" / "MS09_E05_Thumbnail_1280x720.jpg",
        "manifest_path": SERIES_DIR / "MS09_E05" / "MS09_E05_Manifest.json",
        "script_path": SERIES_DIR / "MS09_E05" / "MS09_E05_Script_Foley.md",
        "audit_path": SERIES_DIR / "gate_audit_reports" / "MS09_E05_dual_gate_audit.json",
        "premise_1": "In the warm hypersaline shallows of Hamelin Pool at Shark Bay, Western Australia, photosynthetic cyanobacteria trap sand grains and precipitate aragonite laminae just as their ancestors did 3.5 billion years ago.",
        "premise_2": "Join us for the Series Finale of Earth's Slowest Clocks — Volume II: narrated over warm shallow tidal wash at Shark Bay, salt-flat wind, and faint oxygen bubble fizz with strictly 0% music.",
        "chapters": [
            "00:00 Amber Sunset Over Hamelin Pool, Shark Bay",
            "02:15 Cyanobacteria Biofilms, Trapped Grains & Sub-Millimeter Laminae",
            "06:15 Microscopic Oxygen Bubbles & Earth's Great Oxidation Event",
            "10:00 Pilbara's 3.43-Billion-Year Strelley Pool Fossil Reefs",
            "12:45 Volume II Finale Synthesis: Five Clocks Across Deep Time",
            "15:00 Warm Lagoon Twilight Wash",
        ],
        "citations": [
            "USGS Stromatolites Archive & Western Australia Archaean-Modern Biosedimentation Reference Collection, U.S. Geological Survey.",
            "Reid, R. P., Visscher, P. T., Decho, A. W., Stolz, J. F., Bebout, B. M., Dupraz, C., Macintyre, I. G., Paerl, H. W., Pinckney, J. L., Prufert-Bebout, L., Steppe, T. F., & DesMarais, D. J. (2000). The role of microbes in accretion, lamination and early lithification of modern marine stromatolites. Nature, 406(6799), 989-992. https://doi.org/10.1038/35023158",
            "Allwood, A. C., Walter, M. R., Kamber, B. S., Marshall, C. P., & Burch, I. W. (2006). Stromatolite reef from the Early Archaean era of Australia. Nature, 441(7094), 714-718. https://doi.org/10.1038/nature04764",
        ],
        "question_hook": "From 500-year North Atlantic clams to 3.5-billion-year living stromatolites breathing oxygen into warm shallows—which of Volume II's five clocks brought you the deepest sense of calm? Transition into sleep with our 3-Hour Night Pine Forest Soundscape (https://www.youtube.com/watch?v=OwMTPuornpo).",
        "tags": [
            "stromatolites", "shark bay hamelin pool", "3.5 billion year fossils",
            "cyanobacteria oxygen", "calm earth history documentary", "no music documentary",
            "earth slowest clocks", "sleep documentary", "anti brain rot", "deep time",
        ],
    },
    {
        "asset_id": "MS09_COMP",
        "slug": "MS09_COMP_75m_Earths_Slowest_Clocks_Vol2_FullSeries",
        "position": 5,
        "title": "Earth's Slowest Clocks — Volume II | Complete 75-Minute Calm Documentary (Ep. 1–5)",
        "youtube_title": "Earth's Slowest Clocks — Volume II | Complete 75-Minute Calm Documentary (Ep. 1–5)",
        "publish_at": "2026-12-18T15:00:00Z",
        "duration_display": "01:15:05",
        "mp4_path": SERIES_DIR / "MS09_COMP_75m_FullSeries.mp4",
        "thumb_path": SERIES_DIR / "MS09_COMP_Thumb_Variant_A_1280x720.jpg",
        "manifest_path": SERIES_DIR / "MS09_COMP_Manifest.json",
        "script_path": None,
        "audit_path": SERIES_DIR / "gate_audit_reports" / "MS09_COMP_dual_gate_audit.json",
        "premise_1": "Settle in for the complete 75-minute edition of Earth's Slowest Clocks — Volume II (Episodes 1–5), journeying seamlessly from century-old seabed shells to 3.5-billion-year living stone.",
        "premise_2": "Featuring North Atlantic 500-year Arctica islandica clams, Japan's 50,000-year Lake Suigetsu varve calendar, 100,000-year Milankovitch chalk cliffs, 180-million-year seafloor magnetic stripes, and Shark Bay's living stromatolites—narrated at -14.0 LUFS over organic nature foley with 0% background music.",
        "chapters": [
            "00:00:00 Ep. 1: The 500-Year Clams of the North Atlantic",
            "00:15:01 Ep. 2: Lake Suigetsu & The 50,000-Year Mud Calendar",
            "00:30:02 Ep. 3: Chalk Cliffs & Earth's 100,000-Year Orbital Pendulum",
            "00:45:03 Ep. 4: Magnetic Stripes & The Ocean Floor Tape Recorder",
            "01:00:04 Ep. 5: Stromatolites — The 3.5-Billion-Year Living Stone",
        ],
        "citations": [
            "NOAA NCEI Paleo Study 14609; Butler, P. G., et al. (2013). Palaeogeography, Palaeoclimatology, Palaeoecology, 373, 141-151.",
            "Bronk Ramsey, C., et al. (2012). Science, 338(6105), 370-374; Nakagawa, T., et al. (2012). Lake Suigetsu SG06 Varve Chronology.",
            "NASA Earth Science — Milankovitch Orbital Cycles; Gale, A. S., et al. (2002). Geology, 30(4), 291-294.",
            "USGS This Dynamic Earth — Magnetic Stripes; Vine, F. J., & Matthews, D. H. (1963). Nature, 199(4897), 947-949.",
            "USGS Stromatolites Archive; Reid, R. P., et al. (2000). Nature, 406, 989-992; Allwood, A. C., et al. (2006). Nature, 441, 714-718.",
        ],
        "question_hook": "Thank you for spending 75 calm, music-free minutes with Earth's Slowest Clocks — Volume II. Which of the five natural timekeepers are you drifting off to tonight? Continue into 3 full hours of dark-screen ocean rest at https://www.youtube.com/watch?v=xcAo79qLcLc.",
        "tags": [
            "earth slowest clocks volume 2", "75 minute calm documentary", "sleep documentary no music",
            "arctica islandica", "lake suigetsu varves", "milankovitch chalk cliffs",
            "seafloor magnetic stripes", "shark bay stromatolites", "anti brain rot", "deep time",
        ],
    },
]


def build_sop04_description(item: dict[str, Any], series_playlist_id: str) -> str:
    """Builds SOP-04 compliant timestamped description + scientific source citations (zero Drive links)."""
    lines = [
        item["premise_1"],
        item["premise_2"],
        f"Watch the Full Series Playlist ({SERIES_PLAYLIST_TITLE}): https://www.youtube.com/playlist?list={series_playlist_id}",
        f"Explore Earth's Slowest Clocks Volume I Playlist: https://www.youtube.com/playlist?list={SEASON1_PLAYLIST_ID}",
        "ABR Zero-Music Audio Standard: Narrated in calm baritone at -14.0 LUFS with organic environmental foley calibrated to -26.2 LUFS (over +30.0 dB net voice separation, True Peak below -2.0 dBFS, 0% music, 0% synth drones).",
        "Continue into 3-Hour Deep Sleep Nature Ambience (Night Pine Forest): https://www.youtube.com/watch?v=OwMTPuornpo",
        "Explore Free Printable Family Screen-Reset Tools: https://awkandari-source.github.io/ABR_Anti_Brain_Rot/",
        "Disclosure: ABR Anti-Brain Rot is viewer-supported; any recommended screen-free family resources follow strict FTC disclosure guidelines (#antiBrainRot).",
        "",
        "Timestamps & Chapters:",
        *item["chapters"],
        "",
        "Scientific Sources & Peer-Reviewed Citations:",
        *[f"- {c}" for c in item["citations"]],
        "",
        "#EarthsSlowestClocks #CalmDocumentary #DeepTime #ZeroMusic #SleepDocumentary #AntiBrainRot #SlowScience",
    ]
    desc = "\n".join(lines).replace("<", "(").replace(">", ")")
    if "drive.google.com" in desc.lower():
        raise ValueError(f"Privacy violation in {item['asset_id']} description!")
    if len(desc.encode("utf-8")) > 4850:
        raise ValueError(f"Description UTF-8 byte length exceeds safe ceiling for {item['asset_id']}!")
    return desc


def _parse_gdrive_id(out_str: str) -> str | None:
    import re
    m = re.search(r"\(ID:\s*([A-Za-z0-9_-]+)\)", out_str)
    if m:
        return m.group(1)
    m2 = re.search(r"\(([A-Za-z0-9_-]{25,})\)", out_str)
    if m2:
        return m2.group(1)
    return None


def gdrive_mkdir_id(hub: LinkedAPIHub, folder_name: str, parent_id: str) -> str:
    p = subprocess.run(
        [GDRIVE_BIN, "mutate", "mkdir", folder_name, "--parent", parent_id],
        capture_output=True,
        text=True,
    )
    if p.returncode != 0:
        raise RuntimeError(f"gdrive mutate mkdir {folder_name} failed: {p.stderr or p.stdout}")
    parsed = _parse_gdrive_id(p.stdout + "\n" + p.stderr)
    if parsed:
        return parsed
    found = hub.gdrive.search(folder_name, parent_id=parent_id)
    if isinstance(found, list):
        for entry in found:
            if entry.get("name") == folder_name and "folder" in entry.get("mimeType", "").lower():
                return entry["id"]
    raise RuntimeError(f"Could not resolve Drive folder ID for {folder_name}: {p.stdout}")


def gdrive_upload_id(hub: LinkedAPIHub, local_path: Path, parent_id: str) -> str:
    p = subprocess.run(
        [GDRIVE_BIN, "mutate", "upload", str(local_path), "--parent", parent_id],
        capture_output=True,
        text=True,
    )
    if p.returncode != 0:
        raise RuntimeError(f"gdrive mutate upload {local_path.name} failed: {p.stderr or p.stdout}")
    parsed = _parse_gdrive_id(p.stdout + "\n" + p.stderr)
    if parsed:
        return parsed
    found = hub.gdrive.search(local_path.name, parent_id=parent_id)
    if isinstance(found, list):
        for entry in found:
            if entry.get("name") == local_path.name and "folder" not in entry.get("mimeType", "").lower():
                return entry["id"]
    raise RuntimeError(f"Could not resolve Drive file ID for {local_path.name}: {p.stdout}")


def gdrive_update_file(file_id: str, local_path: Path) -> str:
    p = subprocess.run(
        [GDRIVE_BIN, "mutate", "update", file_id, str(local_path)],
        capture_output=True,
        text=True,
    )
    if p.returncode != 0:
        raise RuntimeError(f"gdrive mutate update {file_id} failed: {p.stderr or p.stdout}")
    return p.stdout.strip()


def ensure_drive_folder(hub: LinkedAPIHub, folder_name: str, parent_id: str) -> str:
    existing = hub.gdrive.search(folder_name, parent_id=parent_id)
    if isinstance(existing, list):
        for entry in existing:
            if (
                entry.get("name") == folder_name
                and "folder" in entry.get("mimeType", "").lower()
            ):
                return entry["id"]
    return gdrive_mkdir_id(hub, folder_name, parent_id)


def upsert_drive_file(hub: LinkedAPIHub, local_path: Path, parent_id: str, existing_id: str | None = None) -> str:
    if existing_id:
        try:
            gdrive_update_file(existing_id, local_path)
            return existing_id
        except Exception:
            pass
    found = hub.gdrive.search(local_path.name, parent_id=parent_id)
    if isinstance(found, list):
        for entry in found:
            if entry.get("name") == local_path.name and "folder" not in entry.get("mimeType", "").lower():
                gdrive_update_file(entry["id"], local_path)
                return entry["id"]
    return gdrive_upload_id(hub, local_path, parent_id)


def ensure_series_playlist(hub: LinkedAPIHub, master_manifest: dict[str, Any]) -> str:
    saved_pl = master_manifest.get("youtube_series_playlist", {}).get("playlist_id")
    if saved_pl:
        return saved_pl

    existing = hub.youtube.list_playlists(max_results=50, purpose="probe")
    for pl in existing:
        if pl.get("snippet", {}).get("title", "").strip() == SERIES_PLAYLIST_TITLE:
            return pl["id"]

    desc = (
        "Earth's Slowest Clocks — Volume II: A 5-part calm deep-time science documentary series "
        "plus full 75-minute compilation exploring natural archives across centuries, millennia, "
        "and billions of years (500-Year North Atlantic Arctica islandica Clams, Lake Suigetsu's "
        "50,000-Year Varve Calendar, 100,000-Year Milankovitch Chalk Cliffs, 180-Million-Year "
        "Seafloor Magnetic Stripes, and 3.5-Billion-Year Living Stromatolites). "
        "Engineered to the ABR Zero-Music Standard (-14.0 LUFS baritone voice, -26.2 LUFS foley stem, "
        ">= +30 dB voice separation, True Peak < -2.0 dBFS, 0% music)."
    )
    res = hub.youtube.request(
        "POST",
        "playlists",
        params={"part": "snippet,status"},
        json_body={
            "snippet": {"title": SERIES_PLAYLIST_TITLE, "description": desc},
            "status": {"privacyStatus": "public"},
        },
        purpose="production",
    )
    return res["id"]


def verify_all_6_qa_gates() -> dict[str, dict[str, Any]]:
    manifests: dict[str, dict[str, Any]] = {}
    for item in MS09_UPLOAD_PLAN:
        aid = item["asset_id"]
        mp = item["manifest_path"]
        mp4 = item["mp4_path"]
        ap = item["audit_path"]
        if not mp.exists():
            raise RuntimeError(f"[{aid}] Missing manifest: {mp}")
        if not mp4.exists():
            raise RuntimeError(f"[{aid}] Missing master MP4: {mp4}")
        if not ap.exists():
            raise RuntimeError(f"[{aid}] Missing dual-gate audit JSON: {ap}")

        m = json.loads(mp.read_text(encoding="utf-8"))
        if m.get("state") not in ("QA_VERIFIED", "API_SCHEDULED"):
            raise RuntimeError(f"[{aid}] Asset has not passed QA gate (state={m.get('state')})!")

        sop03 = m.get("sop03_verification", {})
        if sop03.get("CHK-04", {}).get("music_detected") is not False:
            raise RuntimeError(f"[{aid}] Failed zero-music assertion (music_detected != False)!")
        tp = float(sop03.get("CHK-03", {}).get("master", {}).get("true_peak_dbtp", 0.0))
        if tp >= -2.0:
            raise RuntimeError(f"[{aid}] True Peak {tp} dBFS violates < -2.0 dBFS ceiling!")
        sep = float(sop03.get("CHK-03", {}).get("net_voice_over_foley_separation_db", 0.0))
        if sep < 30.0:
            raise RuntimeError(f"[{aid}] Voice separation {sep} dB violates >= +30.0 dB floor!")
        manifests[aid] = m
    return manifests


def sync_google_drive_volume2(hub: LinkedAPIHub, master_manifest_path: Path) -> tuple[str, str]:
    master_manifest = json.loads(master_manifest_path.read_text(encoding="utf-8"))
    series_drive_folder_id = master_manifest.get("drive_series_archive", {}).get("folder_id")
    if not series_drive_folder_id:
        series_drive_folder_id = ensure_drive_folder(hub, DRIVE_SERIES_FOLDER_NAME, DRIVE_ROOT_ID)
    print(f"[Drive] Volume II Root Folder Ready: {series_drive_folder_id} ({DRIVE_SERIES_FOLDER_NAME})", flush=True)

    audit_drive_folder_id = master_manifest.get("drive_series_archive", {}).get("audit_reports_folder_id")
    if not audit_drive_folder_id:
        audit_drive_folder_id = ensure_drive_folder(hub, "gate_audit_reports", series_drive_folder_id)

    audit_file_ids: dict[str, str] = dict(master_manifest.get("drive_series_archive", {}).get("audit_report_files", {}))
    for item in MS09_UPLOAD_PLAN:
        aid = item["asset_id"]
        ap: Path = item["audit_path"]
        audit_id = upsert_drive_file(hub, ap, audit_drive_folder_id, audit_file_ids.get(aid))
        audit_file_ids[aid] = audit_id

    for item in MS09_UPLOAD_PLAN:
        aid = item["asset_id"]
        m_path: Path = item["manifest_path"]
        manifest = json.loads(m_path.read_text(encoding="utf-8"))
        drv_arch = manifest.get("drive_archive", {})
        ep_drive_folder_id = drv_arch.get("asset_drive_folder_id")
        if not ep_drive_folder_id:
            ep_drive_folder_id = ensure_drive_folder(hub, f"{aid}_{item['publish_at'][:10]}", series_drive_folder_id)
        drive_folder_url = f"https://drive.google.com/drive/folders/{ep_drive_folder_id}"

        prev_files = dict(drv_arch.get("files", {}))
        if prev_files.get("master_mp4"):
            mp4_drv = prev_files["master_mp4"]
            print(f"[{aid}] Reusing already-synced MP4 on Drive: {mp4_drv}", flush=True)
        else:
            print(f"[{aid}] Uploading {item['mp4_path'].name} to Drive folder {ep_drive_folder_id}...", flush=True)
            mp4_drv = upsert_drive_file(hub, item["mp4_path"], ep_drive_folder_id)

        th_drv = (
            prev_files["thumbnail_jpg"]
            if prev_files.get("thumbnail_jpg")
            else upsert_drive_file(hub, item["thumb_path"], ep_drive_folder_id)
        )
        extra_files: dict[str, str] = {}
        if item["script_path"] and item["script_path"].exists():
            extra_files["script_md"] = upsert_drive_file(
                hub, item["script_path"], ep_drive_folder_id, prev_files.get("script_md")
            )
        if aid == "MS09_COMP":
            vb = SERIES_DIR / "MS09_COMP_Thumb_Variant_B_1280x720.jpg"
            if vb.exists():
                extra_files["thumb_variant_b_jpg"] = upsert_drive_file(
                    hub, vb, ep_drive_folder_id, prev_files.get("thumb_variant_b_jpg")
                )
        extra_files["dual_gate_audit_json"] = audit_file_ids[aid]

        manifest["drive_archive"] = {
            "series_drive_folder_id": series_drive_folder_id,
            "asset_drive_folder_id": ep_drive_folder_id,
            "asset_drive_url": drive_folder_url,
            "files": {
                **prev_files,
                "master_mp4": mp4_drv,
                "thumbnail_jpg": th_drv,
                **extra_files,
            },
        }
        m_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        man_drv = upsert_drive_file(hub, m_path, ep_drive_folder_id, prev_files.get("manifest_json"))
        manifest["drive_archive"]["files"]["manifest_json"] = man_drv
        m_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        # Mirror updated episode manifest to GitHub MS-09/
        if aid == "MS09_COMP":
            shutil.copyfile(m_path, GITHUB_MS09_DIR / m_path.name)
        else:
            gh_ep_dir = GITHUB_MS09_DIR / aid
            gh_ep_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(m_path, gh_ep_dir / m_path.name)

        # Update deliverable entry inside ms09_manifest.json
        for d_entry in master_manifest.get("deliverables", []):
            if d_entry.get("asset_id") == aid:
                d_entry["drive_archive"] = {
                    "asset_drive_folder_id": ep_drive_folder_id,
                    "asset_drive_url": drive_folder_url,
                    "master_mp4_file_id": mp4_drv,
                    "manifest_file_id": man_drv,
                    "dual_gate_audit_file_id": audit_file_ids[aid],
                }
                break

    master_manifest["drive_series_archive"] = {
        "folder_name": DRIVE_SERIES_FOLDER_NAME,
        "folder_id": series_drive_folder_id,
        "url": f"https://drive.google.com/drive/folders/{series_drive_folder_id}",
        "audit_reports_folder_id": audit_drive_folder_id,
        "audit_report_files": audit_file_ids,
        "manifest_file_id": master_manifest.get("drive_series_archive", {}).get("manifest_file_id"),
    }
    master_manifest_path.write_text(json.dumps(master_manifest, indent=2), encoding="utf-8")
    m_drv_id = upsert_drive_file(
        hub,
        master_manifest_path,
        series_drive_folder_id,
        master_manifest["drive_series_archive"].get("manifest_file_id"),
    )
    master_manifest["drive_series_archive"]["manifest_file_id"] = m_drv_id
    master_manifest_path.write_text(json.dumps(master_manifest, indent=2), encoding="utf-8")
    shutil.copyfile(master_manifest_path, GITHUB_MS09_DIR / "ms09_manifest.json")
    return series_drive_folder_id, audit_drive_folder_id


def mirror_all_ms09_metadata_to_github() -> None:
    GITHUB_MS09_DIR.mkdir(parents=True, exist_ok=True)
    for src_script in (
        STUDIO_DIR / "ms09_batch_producer.py",
        STUDIO_DIR / "ms09_youtube_drive_sync.py",
        STUDIO_DIR / "ms09_scripts_ep1_ep3.py",
        STUDIO_DIR / "ms09_scripts_ep4_ep5.py",
    ):
        if src_script.exists():
            shutil.copyfile(src_script, GITHUB_MS09_DIR / src_script.name)
    for root_doc in (
        "ms09_manifest.json",
        "MS09_COMP_Manifest.json",
        "MS09_COMPLETION_RECEIPT.json",
        "ms09_post_reset_queue.json",
    ):
        rp = SERIES_DIR / root_doc
        if rp.exists():
            shutil.copyfile(rp, GITHUB_MS09_DIR / root_doc)
    audit_ws = SERIES_DIR / "gate_audit_reports"
    if audit_ws.exists():
        audit_gh = GITHUB_MS09_DIR / "gate_audit_reports"
        audit_gh.mkdir(parents=True, exist_ok=True)
        for jf in sorted(audit_ws.glob("*.json")):
            shutil.copyfile(jf, audit_gh / jf.name)
    for item in MS09_UPLOAD_PLAN:
        aid = item["asset_id"]
        if aid != "MS09_COMP":
            gh_ep = GITHUB_MS09_DIR / aid
            gh_ep.mkdir(parents=True, exist_ok=True)
            for p in (item["manifest_path"], item["script_path"]):
                if p and p.exists():
                    shutil.copyfile(p, gh_ep / p.name)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--drive-only", action="store_true", help="Run QA gate assertion + Google Drive Volume II sync only")
    ap.add_argument("--skip-git-push", action="store_true", help="Skip final git commit/push step")
    args = ap.parse_args()

    hub = LinkedAPIHub()
    GITHUB_MS09_DIR.mkdir(parents=True, exist_ok=True)
    master_manifest_path = SERIES_DIR / "ms09_manifest.json"
    if not master_manifest_path.exists():
        raise RuntimeError(f"Missing master manifest: {master_manifest_path}")

    # 1. Pre-flight Dual-Gate QA verification across all 6 deliverables
    verify_all_6_qa_gates()
    print("[MS-09 Sync] Pre-flight Dual-Gate QA assertion PASSED across all 6/6 deliverables!", flush=True)

    # 2. Idempotent Google Drive Volume II sync (MP4s, thumbnails, manifests, scripts, audit JSONs)
    series_drive_folder_id, _ = sync_google_drive_volume2(hub, master_manifest_path)
    print(f"[MS-09 Sync] Google Drive Volume II archive synced: https://drive.google.com/drive/folders/{series_drive_folder_id}", flush=True)

    if args.drive_only:
        mirror_all_ms09_metadata_to_github()
        print("[MS-09 Sync] --drive-only sync completed cleanly.", flush=True)
        return 0

    # 3. Verify YouTube OAuth + QuotaLedger status
    q_init = hub.youtube.quota.status()
    print(
        f"[MS-09 Sync] QuotaLedger Status ({q_init['pt_date']}): used={q_init['units_used']} / {q_init['hard_daily_cap']} "
        f"(total_remaining={q_init['total_units_remaining']})",
        flush=True,
    )

    master_manifest = json.loads(master_manifest_path.read_text(encoding="utf-8"))
    series_playlist_id = ensure_series_playlist(hub, master_manifest)
    master_manifest["youtube_series_playlist"] = {
        "playlist_id": series_playlist_id,
        "title": SERIES_PLAYLIST_TITLE,
        "url": f"https://www.youtube.com/playlist?list={series_playlist_id}",
    }
    master_manifest_path.write_text(json.dumps(master_manifest, indent=2), encoding="utf-8")
    print(f"[MS-09 Sync] Official Playlist Ready: {series_playlist_id} ({SERIES_PLAYLIST_TITLE})", flush=True)

    post_reset_tasks: list[dict[str, Any]] = []

    # 4A. Quota-Priority Step 1: Upload & schedule all 6 videos (production up to 9,200 soft cap, remediation_critical up to 10,000 hard cap)
    for item in MS09_UPLOAD_PLAN:
        aid = item["asset_id"]
        m_path = item["manifest_path"]
        manifest = json.loads(m_path.read_text(encoding="utf-8"))
        yt_route = manifest.setdefault("youtube_routing", {})
        existing_vid = yt_route.get("youtube_video_id")
        desc = build_sop04_description(item, series_playlist_id)

        # Adopt video ID if autonomous_scheduled_sweeper.py already uploaded a queued item after PT reset
        if not existing_vid:
            sw_meta_path = STUDIO_DIR / item["slug"] / "youtube_publish_metadata.json"
            if sw_meta_path.exists():
                try:
                    sw_data = json.loads(sw_meta_path.read_text(encoding="utf-8"))
                    if sw_data.get("youtube_video_id"):
                        existing_vid = sw_data["youtube_video_id"]
                        yt_route["youtube_video_id"] = existing_vid
                        yt_route["watch_url"] = f"https://www.youtube.com/watch?v={existing_vid}"
                        yt_route["studio_url"] = f"https://studio.youtube.com/video/{existing_vid}/edit"
                        yt_route["quota_deferred"] = False
                        if series_playlist_id in (sw_data.get("playlists_pre_inserted") or []):
                            yt_route["playlist_bound_series"] = True
                        manifest["state"] = "API_SCHEDULED"
                        m_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
                except Exception:
                    pass

        if existing_vid:
            print(f"[{aid}] Already uploaded to YouTube: {existing_vid}", flush=True)
            continue

        upload_purpose = (
            "production"
            if hub.youtube.quota.can_spend(1600, purpose="production")
            else "remediation_critical"
        )
        try:
            print(
                f"[{aid}] Uploading {item['mp4_path'].name} -> scheduled {item['publish_at']} (purpose={upload_purpose})...",
                flush=True,
            )
            up_res = hub.youtube.upload_video(
                item["mp4_path"],
                title=item["youtube_title"],
                description=desc,
                tags=item["tags"],
                category_id="27",
                privacy_status="private",
                publish_at_iso=item["publish_at"],
                made_for_kids=False,
                purpose=upload_purpose,
            )
            vid_id = up_res["id"]
            watch_url = up_res["watch_url"]
            yt_route.update(
                {
                    "privacy_status": "private",
                    "publish_at_utc": item["publish_at"],
                    "series_playlist_id": series_playlist_id,
                    "core_shelf_playlist_id": HISTORY_CORE_PLAYLIST_ID,
                    "made_for_kids": False,
                    "ad_policy": "PRE_MID_POST",
                    "youtube_video_id": vid_id,
                    "watch_url": watch_url,
                    "studio_url": f"https://studio.youtube.com/video/{vid_id}/edit",
                    "quota_deferred": False,
                    "quota_next_reset_utc": None,
                    "playlist_bound_series": False,
                    "playlist_bound_history_shelf": False,
                    "custom_thumbnail_applied": False,
                }
            )
            manifest["state"] = "API_SCHEDULED"
            m_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            print(f"[{aid}] Uploaded & Scheduled -> {watch_url} ({item['publish_at']})", flush=True)
        except YouTubeQuotaExhaustedError as q_exc:
            next_rst = hub.youtube.quota.next_reset_utc()
            yt_route.update(
                {
                    "privacy_status": "private",
                    "publish_at_utc": item["publish_at"],
                    "series_playlist_id": series_playlist_id,
                    "core_shelf_playlist_id": HISTORY_CORE_PLAYLIST_ID,
                    "made_for_kids": False,
                    "ad_policy": "PRE_MID_POST",
                    "youtube_video_id": None,
                    "watch_url": None,
                    "studio_url": None,
                    "quota_deferred": True,
                    "quota_next_reset_utc": next_rst,
                    "quota_deferral_reason": str(q_exc),
                    "playlist_bound_series": False,
                    "playlist_bound_history_shelf": False,
                    "custom_thumbnail_applied": False,
                }
            )
            manifest["state"] = "QA_VERIFIED"
            m_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            post_reset_tasks.append(
                {
                    "asset_id": aid,
                    "action": "upload_and_bind_playlist",
                    "publish_at_utc": item["publish_at"],
                    "playlist_id": series_playlist_id,
                    "position": item["position"],
                    "next_reset_utc": next_rst,
                    "reason": str(q_exc),
                }
            )
            print(f"[{aid}] Daily 10,000-unit quota cap reached; queued for automatic post-reset upload ({next_rst}): {q_exc}", flush=True)

    # 4B. Quota-Priority Step 2: Bind uploaded videos in order (0..5) to Earth's Slowest Clocks — Volume II (50 units each)
    for item in MS09_UPLOAD_PLAN:
        aid = item["asset_id"]
        m_path = item["manifest_path"]
        manifest = json.loads(m_path.read_text(encoding="utf-8"))
        yt_route = manifest["youtube_routing"]
        vid_id = yt_route.get("youtube_video_id")
        if not vid_id:
            print(f"[{aid}] Playlist binding queued behind post-reset video upload.", flush=True)
            continue
        if not yt_route.get("playlist_bound_series"):
            try:
                print(
                    f"[{aid}] Binding {vid_id} to '{SERIES_PLAYLIST_TITLE}' ({series_playlist_id}, position={item['position']})...",
                    flush=True,
                )
                hub.youtube.add_to_playlist(series_playlist_id, vid_id, position=item["position"], purpose="sweeper")
                yt_route["playlist_bound_series"] = True
                yt_route.pop("playlist_deferral_note", None)
                m_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            except YouTubeQuotaExhaustedError as q_exc:
                yt_route["playlist_bound_series"] = False
                yt_route["playlist_deferral_note"] = str(q_exc)
                m_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
                post_reset_tasks.append(
                    {
                        "asset_id": aid,
                        "video_id": vid_id,
                        "action": "bind_series_playlist",
                        "playlist_id": series_playlist_id,
                        "position": item["position"],
                        "next_reset_utc": hub.youtube.quota.next_reset_utc(),
                        "reason": str(q_exc),
                    }
                )
                print(f"[{aid}] Playlist binding deferred to post-reset sweeper: {q_exc}", flush=True)

    # 4C. Quota-Priority Step 3: Best-effort custom thumbnails & History shelf (gracefully deferred to sweeper if >10,000 units)
    for item in MS09_UPLOAD_PLAN:
        aid = item["asset_id"]
        m_path = item["manifest_path"]
        manifest = json.loads(m_path.read_text(encoding="utf-8"))
        yt_route = manifest["youtube_routing"]
        vid_id = yt_route.get("youtube_video_id")
        if not vid_id:
            continue

        if not yt_route.get("custom_thumbnail_applied"):
            if hub.youtube.quota.can_spend(50, purpose="sweeper"):
                try:
                    hub.youtube.set_thumbnail(vid_id, item["thumb_path"], purpose="sweeper")
                    yt_route["custom_thumbnail_applied"] = True
                    print(f"[{aid}] Custom 1280x720 thumbnail applied on {vid_id}.", flush=True)
                except YouTubeQuotaExhaustedError as q_exc:
                    print(f"[{aid}] Thumbnail deferred to post-reset sweeper: {q_exc}", flush=True)
            else:
                print(f"[{aid}] Thumbnail queued for post-reset window (<50 daily quota units remaining).", flush=True)

        if not yt_route.get("playlist_bound_history_shelf"):
            if hub.youtube.quota.can_spend(50, purpose="sweeper"):
                try:
                    hub.youtube.add_to_playlist(HISTORY_CORE_PLAYLIST_ID, vid_id, purpose="sweeper")
                    yt_route["playlist_bound_history_shelf"] = True
                    print(f"[{aid}] Bound {vid_id} to History Shelf {HISTORY_CORE_PLAYLIST_ID}.", flush=True)
                except YouTubeQuotaExhaustedError as q_exc:
                    print(f"[{aid}] Secondary shelf binding deferred to post-reset sweeper: {q_exc}", flush=True)

        m_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # 5. Finalize manifests, sweeper metadata, Drive manifest updates, and scheduled_records
    tracker_path = WORKSPACE / "INDEX_Tracker.json"
    tracker = json.loads(tracker_path.read_text(encoding="utf-8"))
    master_manifest = json.loads(master_manifest_path.read_text(encoding="utf-8"))
    scheduled_records: list[dict[str, Any]] = []

    for item in MS09_UPLOAD_PLAN:
        aid = item["asset_id"]
        m_path = item["manifest_path"]
        manifest = json.loads(m_path.read_text(encoding="utf-8"))
        yt_route = manifest["youtube_routing"]
        drv_arch = manifest["drive_archive"]
        vid_id = yt_route.get("youtube_video_id")
        watch_url = yt_route.get("watch_url")
        ep_drive_folder_id = drv_arch["asset_drive_folder_id"]
        drive_folder_url = drv_arch["asset_drive_url"]
        desc = build_sop04_description(item, series_playlist_id)

        # Update episode manifest on Google Drive with final YouTube Video ID & playlist binding
        upsert_drive_file(hub, m_path, ep_drive_folder_id, drv_arch["files"].get("manifest_json"))

        pre_inserted: list[str] = []
        if yt_route.get("playlist_bound_series"):
            pre_inserted.append(series_playlist_id)
        if yt_route.get("playlist_bound_history_shelf"):
            pre_inserted.append(HISTORY_CORE_PLAYLIST_ID)

        sweeper_status = "API_SCHEDULED" if vid_id else "QUEUED_FOR_QUOTA_RESET"
        sweeper_dir = STUDIO_DIR / item["slug"]
        sweeper_dir.mkdir(parents=True, exist_ok=True)
        sweeper_meta = {
            "slug": item["slug"],
            "asset_id": aid,
            "title": item["youtube_title"],
            "full_editorial_title": item["title"],
            "youtube_title": item["youtube_title"],
            "description": desc,
            "tags": item["tags"],
            "category_id": "27",
            "pillar": "Pillar 2B (Deep-Time Science & Calm History Documentary · MS-09)",
            "format": "16:9_LONG_FORM",
            "youtube_video_id": vid_id,
            "youtube_url": watch_url,
            "watch_url": watch_url,
            "status": sweeper_status,
            "quota_note": yt_route.get("quota_deferral_reason") if not vid_id else None,
            "publish_at_utc": item["publish_at"],
            "youtube_status": {
                "uploadStatus": "uploaded" if vid_id else "queued_for_quota_reset",
                "privacyStatus": "private",
                "publishAt": item["publish_at"],
                "selfDeclaredMadeForKids": False,
            },
            "custom_thumbnail_applied": bool(yt_route.get("custom_thumbnail_applied")),
            "thumbnail_path": str(item["thumb_path"]),
            "playlist_id": series_playlist_id,
            "playlist_position": item["position"],
            "assigned_playlists": [series_playlist_id, HISTORY_CORE_PLAYLIST_ID],
            "playlists_pre_inserted": pre_inserted,
            "question_hook": item["question_hook"],
            "post_publish_swept": False,
            "mp4_path": str(item["mp4_path"]),
            "drive_root_folder_id": DRIVE_ROOT_ID,
            "drive_archive_folder_id": ep_drive_folder_id,
            "drive_archive_url": drive_folder_url,
        }
        (sweeper_dir / "youtube_publish_metadata.json").write_text(json.dumps(sweeper_meta, indent=2), encoding="utf-8")

        sep_db = manifest["sop03_verification"]["CHK-03"]["net_voice_over_foley_separation_db"]
        lufs_i = manifest["sop03_verification"]["CHK-03"]["master"]["integrated_lufs"]
        tp_dbfs = manifest["sop03_verification"]["CHK-03"]["master"]["true_peak_dbtp"]
        dur_sec = manifest["sop03_verification"]["CHK-02"]["duration_sec"]

        asset_state = "API_SCHEDULED" if vid_id else "QA_VERIFIED_QUOTA_QUEUED"
        tracker.setdefault("assets", {})[aid] = {
            **tracker.get("assets", {}).get(aid, {}),
            "asset_id": aid,
            "slug": item["slug"],
            "series_id": "MS-09",
            "episode_index": item["position"] + 1,
            "title": item["title"],
            "state": asset_state,
            "youtube_id": vid_id,
            "youtube_video_id": vid_id,
            "youtube_url": watch_url,
            "publish_at_utc": item["publish_at"],
            "playlist_id": series_playlist_id,
            "playlist_bound": bool(yt_route.get("playlist_bound_series")),
            "drive_folder_id": ep_drive_folder_id,
            "drive_url": drive_folder_url,
            "duration_sec": dur_sec,
            "voice_separation_db": sep_db,
        }

        for d_entry in master_manifest.get("deliverables", []):
            if d_entry.get("asset_id") == aid:
                d_entry["status"] = asset_state
                d_entry["youtube"] = {
                    "video_id": vid_id,
                    "watch_url": watch_url,
                    "publish_at_utc": item["publish_at"],
                    "playlist_id": series_playlist_id,
                    "playlist_title": SERIES_PLAYLIST_TITLE,
                    "playlist_position": item["position"],
                    "playlist_bound": bool(yt_route.get("playlist_bound_series")),
                    "custom_thumbnail_applied": bool(yt_route.get("custom_thumbnail_applied")),
                    "quota_next_reset_utc": yt_route.get("quota_next_reset_utc"),
                }
                break

        scheduled_records.append(
            {
                "asset_id": aid,
                "slug": item["slug"],
                "title": item["title"],
                "youtube_title": item["youtube_title"],
                "duration_sec": dur_sec,
                "duration_display": item["duration_display"],
                "file_size_mb": round(item["mp4_path"].stat().st_size / (1024 * 1024), 2),
                "integrated_lufs": lufs_i,
                "true_peak_dbfs": tp_dbfs,
                "voice_sep_db": sep_db,
                "music_detected": False,
                "publish_at": item["publish_at"],
                "status": asset_state,
                "youtube_id": vid_id,
                "watch_url": watch_url,
                "playlist_id": series_playlist_id,
                "playlist_bound": bool(yt_route.get("playlist_bound_series")),
                "quota_next_reset_utc": yt_route.get("quota_next_reset_utc"),
                "drive_folder_id": ep_drive_folder_id,
                "drive_url": drive_folder_url,
            }
        )

    all_uploaded = all(bool(r["youtube_id"]) for r in scheduled_records)
    master_manifest["series_status"] = (
        "API_SCHEDULED_AND_ARCHIVED" if all_uploaded else "PARTIAL_API_SCHEDULED_QUOTA_QUEUED_AND_ARCHIVED"
    )
    master_manifest["youtube_series_playlist"] = {
        "playlist_id": series_playlist_id,
        "title": SERIES_PLAYLIST_TITLE,
        "url": f"https://www.youtube.com/playlist?list={series_playlist_id}",
    }
    master_manifest_path.write_text(json.dumps(master_manifest, indent=2), encoding="utf-8")
    shutil.copyfile(master_manifest_path, BASELINE_DIR / "ms09_manifest.json")
    upsert_drive_file(
        hub,
        master_manifest_path,
        series_drive_folder_id,
        master_manifest["drive_series_archive"].get("manifest_file_id"),
    )

    q_final = hub.youtube.quota.status()
    queue_payload = {
        "series_id": "MS-09",
        "series_playlist_id": series_playlist_id,
        "pt_date": q_final["pt_date"],
        "next_reset_utc": q_final["next_reset_utc"],
        "pending_tasks": post_reset_tasks,
        "resume_command": "PYTHONDONTWRITEBYTECODE=1 python3 /shared/user/.gemini/raw_video_studio/ms09_youtube_drive_sync.py",
    }
    for q_path in (STUDIO_DIR / "ms09_post_reset_queue.json", SERIES_DIR / "ms09_post_reset_queue.json"):
        q_path.write_text(json.dumps(queue_payload, indent=2), encoding="utf-8")

    receipt_path = SERIES_DIR / "MS09_COMPLETION_RECEIPT.json"
    receipt_payload = {
        "series_id": "MS-09",
        "series_title": SERIES_TITLE,
        "playlist_title": SERIES_PLAYLIST_TITLE,
        "series_playlist_id": series_playlist_id,
        "series_playlist_url": f"https://www.youtube.com/playlist?list={series_playlist_id}",
        "series_drive_folder_id": series_drive_folder_id,
        "series_drive_url": f"https://drive.google.com/drive/folders/{series_drive_folder_id}",
        "quota_ledger_after_batch": q_final,
        "post_reset_tasks": post_reset_tasks,
        "completed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "assets": scheduled_records,
    }
    receipt_path.write_text(json.dumps(receipt_payload, indent=2), encoding="utf-8")
    upsert_drive_file(hub, receipt_path, series_drive_folder_id)

    # 6. Upsert 6 MS-09 rows in ABR_Anti_Brain_Rot_Videos_Index.csv (idempotent by drive_folder_id / youtube_id)
    csv_paths = [
        BASELINE_DIR / "ABR_Anti_Brain_Rot_Videos_Index.csv",
        WORKSPACE / "ABR_Anti_Brain_Rot_Videos_Index.csv",
    ]
    with csv_paths[0].open("r", encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f))
    header, body = rows[0], rows[1:]

    drive_to_row_idx: dict[str, int] = {}
    yt_to_row_idx: dict[str, int] = {}
    for idx_r, row in enumerate(body):
        if len(row) > 9 and row[9].strip():
            drive_to_row_idx[row[9].strip()] = idx_r
        if len(row) > 1 and row[1].strip() and not row[1].startswith("PENDING"):
            yt_to_row_idx[row[1].strip()] = idx_r

    for r in scheduled_records:
        yt_cell = r["youtube_id"] or f"PENDING_RESET_{r['asset_id']}"
        status_cell = "Scheduled" if r["youtube_id"] else f"Queued ({q_final['next_reset_utc']})"
        url_cell = r["watch_url"] or f"https://www.youtube.com/playlist?list={series_playlist_id}"
        existing_i = drive_to_row_idx.get(r["drive_folder_id"])
        if existing_i is None and r["youtube_id"]:
            existing_i = yt_to_row_idx.get(r["youtube_id"])

        if existing_i is not None:
            row_num = body[existing_i][0]
            body[existing_i] = [
                row_num,
                yt_cell,
                r["title"],
                "longform_16x9",
                "Pillar 2B (History/Deep-Time · MS09)",
                r["duration_display"],
                status_cell,
                r["publish_at"],
                url_cell,
                r["drive_folder_id"],
            ]
        else:
            next_idx = len(body) + 1
            body.append(
                [
                    str(next_idx),
                    yt_cell,
                    r["title"],
                    "longform_16x9",
                    "Pillar 2B (History/Deep-Time · MS09)",
                    r["duration_display"],
                    status_cell,
                    r["publish_at"],
                    url_cell,
                    r["drive_folder_id"],
                ]
            )
            drive_to_row_idx[r["drive_folder_id"]] = len(body) - 1

    for cp in csv_paths:
        if cp.parent.exists():
            with cp.open("w", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                w.writerow(header)
                w.writerows(body)

    tracker["ms09_series_summary"] = {
        "updated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "series_title": SERIES_TITLE,
        "series_playlist_id": series_playlist_id,
        "series_drive_folder_id": series_drive_folder_id,
        "uploaded_count": sum(1 for r in scheduled_records if r["youtube_id"]),
        "total_deliverables": len(scheduled_records),
        "csv_total_rows": len(body),
    }
    tracker_path.write_text(json.dumps(tracker, indent=2), encoding="utf-8")
    shutil.copyfile(tracker_path, BASELINE_DIR / "INDEX_Tracker.json")

    print("[MS-09 Sync] Updating Baseline CSV, INDEX_Tracker.json, and ms09_manifest.json on Google Drive...", flush=True)
    gdrive_update_file(DRIVE_CSV_FILE_ID, BASELINE_DIR / "ABR_Anti_Brain_Rot_Videos_Index.csv")
    gdrive_update_file(DRIVE_TRACKER_FILE_ID, BASELINE_DIR / "INDEX_Tracker.json")
    upsert_drive_file(hub, BASELINE_DIR / "ms09_manifest.json", DRIVE_BASELINE_FOLDER_ID)

    # 7. Pull latest origin/main cleanly, then idempotently update GitHub ABR_Anti_Brain_Rot_Index.md + 01 Baseline Drive Index MD
    if not args.skip_git_push:
        subprocess.run(["git", "pull", "--rebase", "--autostash", "origin", "main"], cwd=str(GITHUB_REPO), check=True)
    idx_md_path = GITHUB_REPO / "ABR_Anti_Brain_Rot_Index.md"
    md_text = idx_md_path.read_text(encoding="utf-8")
    pl_anchor = "| *Mini-Series (`MS06`)* | `PLdWSOapYjkZc` | **Earth's Slowest Clocks \\| 5-Part Calm Deep-Time Documentary Series (Zero Music)** | 5 | https://www.youtube.com/playlist?list=PLdWSOapYjkZc |"
    pl_new_row = (
        f"| *Mini-Series (`MS-09`)* | `{series_playlist_id}` | **{SERIES_PLAYLIST_TITLE}** | 6 | "
        f"https://www.youtube.com/playlist?list={series_playlist_id} |"
    )
    if series_playlist_id not in md_text and pl_anchor in md_text:
        md_text = md_text.replace(pl_anchor, pl_anchor + "\n" + pl_new_row)

    ms09_header = "### 2.1 Mini-Series `MS-09`: *Earth's Slowest Clocks — Volume II* (`16:9` 15-Min & 75-Min Zero-Music)"
    ms09_lines = [
        ms09_header,
        "",
        f"- **Official Series Playlist:** [`{series_playlist_id}`](https://www.youtube.com/playlist?list={series_playlist_id}) (**{SERIES_PLAYLIST_TITLE}**)",
        f"- **Google Drive Volume II Archive:** [`{series_drive_folder_id}`](https://drive.google.com/drive/folders/{series_drive_folder_id})",
        "",
        "| Asset ID | Video Title | Runtime | Loudness / Peak | Voice Sep | Schedule (`15:00 UTC`) | YouTube Link | Drive Folder |",
        "| :--- | :--- | :---: | :---: | :--- | :--- | :--- | :--- |",
    ]
    for r in scheduled_records:
        t_esc = r["title"].replace("|", "\\|")
        yt_col = (
            f"[`{r['youtube_id']}`]({r['watch_url']})"
            if r["youtube_id"]
            else f"*Queued for PT Quota Reset (`{q_final['next_reset_utc']}`)*"
        )
        sched_col = (
            f"**Scheduled** (`{r['publish_at']}`)"
            if r["youtube_id"]
            else f"**Staged / Auto-Upload at PT Reset** (`{r['publish_at']}`)"
        )
        ms09_lines.append(
            f"| `{r['asset_id']}` | *{t_esc}* | `{r['duration_display']}` | `{r['integrated_lufs']} LUFS` / `{r['true_peak_dbfs']} dBFS` | "
            f"**`+{r['voice_sep_db']} dB`** (`0%` Music) | {sched_col} | "
            f"{yt_col} | [`{r['drive_folder_id']}`]({r['drive_url']}) |"
        )
    ms09_block = "\n".join(ms09_lines) + "\n"

    sec3_anchor = "\n---\n\n## 3. Complete `9:16` Zero-Music Shorts Catalog"
    if ms09_header in md_text and sec3_anchor in md_text:
        before, rest = md_text.split(ms09_header, 1)
        _, after_sec3 = rest.split(sec3_anchor, 1)
        md_text = before.rstrip() + "\n\n" + ms09_block + sec3_anchor + after_sec3
    elif sec3_anchor in md_text:
        md_text = md_text.replace(sec3_anchor, "\n\n" + ms09_block + sec3_anchor)
    else:
        md_text = md_text.rstrip() + "\n\n---\n\n" + ms09_block

    idx_md_path.write_text(md_text, encoding="utf-8")
    shutil.copyfile(idx_md_path, BASELINE_DIR / "ABR_Anti_Brain_Rot_Index.md")
    gdrive_update_file(DRIVE_INDEX_MD_FILE_ID, BASELINE_DIR / "ABR_Anti_Brain_Rot_Index.md")

    # 8. Mirror all MS-09 scripts, manifests, and audit reports to GitHub repo & commit/push cleanly
    mirror_all_ms09_metadata_to_github()

    # Remove any Python bytecode caches created under .agents/ so working tree stays clean
    agents_dir = GITHUB_REPO / ".agents"
    if agents_dir.exists():
        for pyc_dir in agents_dir.rglob("__pycache__"):
            shutil.rmtree(pyc_dir, ignore_errors=True)

    if not args.skip_git_push:
        subprocess.run(["git", "add", "-A", "MS-09", "ABR_Anti_Brain_Rot_Index.md"], cwd=str(GITHUB_REPO), check=True)
        diff_chk = subprocess.run(["git", "status", "--porcelain"], cwd=str(GITHUB_REPO), capture_output=True, text=True, check=True)
        if diff_chk.stdout.strip():
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    f"Add MS-09 Earth's Slowest Clocks Vol. II pipeline, manifests, QA audits & index ({series_playlist_id})",
                ],
                cwd=str(GITHUB_REPO),
                check=True,
            )
            subprocess.run(["git", "push", "origin", "HEAD"], cwd=str(GITHUB_REPO), check=True)
        clean_chk = subprocess.run(["git", "status", "--porcelain"], cwd=str(GITHUB_REPO), capture_output=True, text=True, check=True)
        if clean_chk.stdout.strip():
            raise RuntimeError(f"Git working tree is not clean after sync:\n{clean_chk.stdout}")
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(GITHUB_REPO), text=True).strip()
        print(f"[MS-09 Sync] GitHub commit pushed cleanly: {commit_sha} (git status clean)", flush=True)

    print(f"\n[MS-09 Sync] MULTI-PLATFORM SYNC COMPLETE! Receipt: {receipt_path}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
