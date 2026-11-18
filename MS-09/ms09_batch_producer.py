#!/usr/bin/env python3
"""
MS-09 ("Earth's Slowest Clocks — Volume II") End-to-End Batch Producer & Dual-Gate QA
=====================================================================================
Isolated MS-09 production orchestrator (leaving MS-08 completely untouched):
1. Synthesizes continuous uniform baritone narration (`0.75 * bm_george + 0.25 * bm_daniel`
   via Kokoro ONNX neural TTS) normalized to `-14.0 LUFS` with zero unintended dead-air gaps
   (`max_narration_silence_sec <= 1.5s`, `vocal_duty_cycle_pct >= 88%`).
2. Filters & calibrates Two-Layer Zero-Music organic environmental foley stems to `-26.2 LUFS`
   and mixes sidechain-ducked foley maintaining `>= +30.0 dB` net voice-over-foley separation,
   True Peak strictly `< -2.0 dBFS` via 4x-oversampled `alimiter=limit=0.72`, and `0%` music.
3. Renders 56 decoupled `<2700K` macro watercolor scenes per episode (`901.00s` / `15:01`,
   `1920x1080`, `24/1` fps, `libx264` High Profile with explicit `8x8dct=1:cabac=1`, `BT.709`
   color metadata, ABR watermark, and `+faststart` with `moov` atom at front).
4. Builds `MS09_COMP_75m_FullSeries.mp4` (`4505.00s` / `75:05`) via lossless `-c copy`
   concatenation from the 5 `QA_VERIFIED` episode masters with `+faststart` and embedded
   chapter metadata (`00:00:00`, `00:15:01`, `00:30:02`, `00:45:03`, `01:00:04`).
5. Executes both `verify_asset_gate.py` (`CHK-01`..`CHK-07`) and `qc_gate.py`, quarantining
   and rebuilding from checkpoint if any gate check fails, and persists audit reports to
   `MS-09/gate_audit_reports/` and `ms09_manifest.json`.
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

sys.path.insert(0, "/shared/user/.gemini/raw_video_studio")
sys.path.insert(0, "/home/antigravity/awkandari-source/ABR_Anti_Brain_Rot/.agents/skills/abr-daily-producer/scripts")

import ms09_scripts_ep1_ep3 as s13
import ms09_scripts_ep4_ep5 as s45
import qc_gate
from linked_api_hub import (
    clamp_narration_silence,
    count_spoken_words,
    sanitize_tts_script,
    validate_sop_v21_word_budget,
)

WORKSPACE = Path("/home/antigravity/ABR_AntiGravity_Workspace")
SERIES_DIR = Path("/home/antigravity/MS-09")
GITHUB_MS09_DIR = Path("/home/antigravity/awkandari-source/ABR_Anti_Brain_Rot/MS-09")
FOLEY_LIB = WORKSPACE / "03_Verified_Foley_Library"
VERIFY_SCRIPT = WORKSPACE / "05_Verification_Scripts" / "verify_asset_gate.py"
TRACKER_PATH = WORKSPACE / "INDEX_Tracker.json"
WATERMARK_PNG = Path("/shared/user/.gemini/raw_video_studio/channel_branding/ABR_Video_Watermark_150x150.png")

KOKORO_MODEL = Path("/shared/user/.gemini/raw_video_studio/kokoro_models/kokoro-v1.0.int8.onnx")
KOKORO_VOICES = Path("/shared/user/.gemini/raw_video_studio/kokoro_models/voices-v1.0.bin")

BUILD_ROOT = Path("/tmp/abr_ms09_build")

EPISODE_SPECS: list[dict[str, Any]] = [
    {
        "asset_id": "MS09_E01",
        "episode_index": 1,
        "title": "Earth's Slowest Clocks Vol. II Ep. 1: The 500-Year Clams of the North Atlantic | 15-Min Calm Documentary",
        "youtube_title": "Earth's Slowest Clocks Vol. II Ep. 1: 500-Year Clams of the North Atlantic | Calm Documentary",
        "publish_at_utc": "2026-12-01T15:00:00Z",
        "lines": s13.MS09_E01_LINES,
        "durations": s13.SCENE_DURATIONS_56_MS09,
        "foley_a": "ms03_s02_ch06_coastal_bluff_pine_shingle_tide_48k24b.wav",
        "foley_b": "ms01_e04_twilight_oak_timber_48k24b.wav",
        "foley_filter": "highpass=f=70,lowpass=f=680,acompressor=threshold=-32dB:ratio=10:attack=25:release=250",
        "hero_plate": 1,
    },
    {
        "asset_id": "MS09_E02",
        "episode_index": 2,
        "title": "Earth's Slowest Clocks Vol. II Ep. 2: Lake Suigetsu & The 50,000-Year Mud Calendar | 15-Min Calm Documentary",
        "youtube_title": "Earth's Slowest Clocks Vol. II Ep. 2: Lake Suigetsu & The 50,000-Year Mud Calendar | Documentary",
        "publish_at_utc": "2026-12-04T15:00:00Z",
        "lines": s13.MS09_E02_LINES,
        "durations": s13.SCENE_DURATIONS_56_MS09,
        "foley_a": "ms01_e03_pond_ripples_reeds_48k24b.wav",
        "foley_b": "ms03_e02_greenhouse_soft_rain_48k24b.wav",
        "foley_filter": "highpass=f=70,lowpass=f=780,acompressor=threshold=-32dB:ratio=10:attack=25:release=250",
        "hero_plate": 1,
    },
    {
        "asset_id": "MS09_E03",
        "episode_index": 3,
        "title": "Earth's Slowest Clocks Vol. II Ep. 3: Chalk Cliffs & Earth's 100,000-Year Orbital Pendulum | 15-Min Calm Documentary",
        "youtube_title": "Earth's Slowest Clocks Vol. II Ep. 3: Chalk Cliffs & Earth's 100,000-Year Orbital Pendulum",
        "publish_at_utc": "2026-12-08T15:00:00Z",
        "lines": s13.MS09_E03_LINES,
        "durations": s13.SCENE_DURATIONS_56_MS09,
        "foley_a": "ms03_ch02_soft_coastal_tide_shorebirds_48k24b.wav",
        "foley_b": "ms03_s03_ch05_coastal_pine_bluff_interleaved_tide_48k24b.wav",
        "foley_filter": "highpass=f=70,lowpass=f=900,acompressor=threshold=-32dB:ratio=10:attack=25:release=250",
        "hero_plate": 1,
    },
    {
        "asset_id": "MS09_E04",
        "episode_index": 4,
        "title": "Earth's Slowest Clocks Vol. II Ep. 4: Magnetic Stripes & The Ocean Floor Tape Recorder | 15-Min Documentary",
        "youtube_title": "Earth's Slowest Clocks Vol. II Ep. 4: Magnetic Stripes & The Ocean Floor Tape Recorder",
        "publish_at_utc": "2026-12-11T15:00:00Z",
        "lines": s45.MS09_E04_LINES,
        "durations": s13.SCENE_DURATIONS_56_MS09,
        "foley_a": "ms02_e04_waterwheel_millpond_dusk_48k24b.wav",
        "foley_b": "ms03_ch08_warm_hearth_crackle_night_wind_48k24b.wav",
        "foley_filter": "highpass=f=70,lowpass=f=420,acompressor=threshold=-32dB:ratio=10:attack=25:release=250",
        "hero_plate": 1,
    },
    {
        "asset_id": "MS09_E05",
        "episode_index": 5,
        "title": "Earth's Slowest Clocks Vol. II Ep. 5: Stromatolites — The 3.5-Billion-Year Living Stone | 15-Min Finale",
        "youtube_title": "Earth's Slowest Clocks Vol. II Ep. 5: Stromatolites — The 3.5-Billion-Year Living Stone | Finale",
        "publish_at_utc": "2026-12-15T15:00:00Z",
        "lines": s45.MS09_E05_LINES,
        "durations": s13.SCENE_DURATIONS_56_MS09,
        "foley_a": "ms03_s02_ch07_dusk_millpond_ripples_reeds_48k24b.wav",
        "foley_b": "ms03_s02_ch05_open_meadow_wind_pebble_brook_48k24b.wav",
        "foley_filter": "highpass=f=70,lowpass=f=860,acompressor=threshold=-32dB:ratio=10:attack=25:release=250",
        "hero_plate": 1,
    },
]

COMP_CHAPTERS = [
    (0, 901000, "Ep. 1: The 500-Year Clams of the North Atlantic"),
    (901000, 1802000, "Ep. 2: Lake Suigetsu & The 50,000-Year Mud Calendar"),
    (1802000, 2703000, "Ep. 3: Chalk Cliffs & Earth's 100,000-Year Orbital Pendulum"),
    (2703000, 3604000, "Ep. 4: Magnetic Stripes & The Ocean Floor Tape Recorder"),
    (3604000, 4505000, "Ep. 5: Stromatolites — The 3.5-Billion-Year Living Stone"),
]


def measure_ebur128(path: Path) -> dict[str, float]:
    p = subprocess.run(
        ["ffmpeg", "-nostats", "-vn", "-i", str(path), "-filter_complex", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    m_i = re.findall(r"I:\s*([-\d.]+)\s*LUFS", p.stderr)
    m_lra = re.findall(r"LRA:\s*([-\d.]+)\s*LU", p.stderr)
    m_tp = re.findall(r"Peak:\s*([-\d.]+)\s*dBFS", p.stderr)
    return {
        "integrated_lufs": float(m_i[-1]) if m_i else -99.0,
        "lra_lu": float(m_lra[-1]) if m_lra else 0.0,
        "true_peak_dbtp": float(m_tp[-1]) if m_tp else 0.0,
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def trim_and_fade_speech(audio: np.ndarray, sr: int) -> np.ndarray:
    idx = np.where(np.abs(audio) > 0.0025)[0]
    if len(idx) == 0:
        return np.zeros(int(0.1 * sr), dtype=np.float32)
    s = max(0, int(idx[0]) - int(0.02 * sr))
    e = min(len(audio), int(idx[-1]) + int(0.04 * sr))
    clipped = audio[s:e].astype(np.float32, copy=True)
    fade_n = min(int(0.025 * sr), len(clipped) // 4)
    if fade_n > 4:
        ramp = 0.5 * (1.0 - np.cos(np.linspace(0.0, math.pi, fade_n, dtype=np.float32)))
        clipped[:fade_n] *= ramp
        clipped[-fade_n:] *= ramp[::-1]
    return clipped


def get_audio_duration(path: Path) -> float:
    return float(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
            text=True,
        ).strip()
    )


def quarantine_failed_asset(asset_id: str, paths_to_move: list[Path], wdir: Path) -> None:
    qdir = SERIES_DIR / "quarantine" / f"{asset_id}_{int(time.time())}"
    qdir.mkdir(parents=True, exist_ok=True)
    for p in paths_to_move:
        if p.exists():
            shutil.copyfile(p, qdir / p.name)
            p.unlink(missing_ok=True)
    for transient in ("Master_Audio.m4a", "Voice_Stem.wav", "Foley_Stem.wav", "Foley_Ducked_Stem.wav"):
        tp = wdir / transient
        tp.unlink(missing_ok=True)
    print(f"    [QUARANTINE] Moved failed {asset_id} artifacts to {qdir} for clean rebuild.", flush=True)


def ensure_tracker_registration() -> None:
    if not TRACKER_PATH.exists():
        return
    tracker = json.loads(TRACKER_PATH.read_text())
    assets = tracker.setdefault("assets", {})
    for spec in EPISODE_SPECS:
        aid = spec["asset_id"]
        assets.setdefault(
            aid,
            {
                "asset_id": aid,
                "series_id": "MS-09",
                "title": spec["title"],
                "format": "16:9_LONG_FORM",
                "state": "REGISTERED",
                "publish_at_utc": spec["publish_at_utc"],
            },
        )
    assets.setdefault(
        "MS09_COMP",
        {
            "asset_id": "MS09_COMP",
            "series_id": "MS-09",
            "title": "Earth's Slowest Clocks — Volume II | Complete 75-Minute Calm Documentary (Ep. 1–5)",
            "format": "16:9_LONG_FORM",
            "state": "REGISTERED",
            "publish_at_utc": "2026-12-18T15:00:00Z",
        },
    )
    TRACKER_PATH.write_text(json.dumps(tracker, indent=2))


def write_episode_script_markdown(spec: dict[str, Any], ep_out_dir: Path) -> Path:
    aid = spec["asset_id"]
    md_path = ep_out_dir / f"{aid}_Script_Foley.md"
    sanitized_lines = [sanitize_tts_script(t, for_engine=True) for _, t in spec["lines"]]
    total_words = count_spoken_words(" ".join(sanitized_lines))
    rows = [
        f"# {aid} — {spec['title']}",
        "",
        "- **SOP Authority**: `ABR-AG-SOP-v2.1` (Continuous Narration & Dead-Air Elimination)",
        f"- **Spoken Word Count**: `{total_words}` words (Budget: `1,650–1,850` words @ `110–120 WPM`)",
        "- **Audio Architecture**: Continuous Master Voice Stem (`-14.0 LUFS` centered-mono, `alimiter=limit=0.72` `< -2.0 dBFS`, `0` per-scene `apad`) + Two-Layer Nature Foley (`-26.2 LUFS` stem, `>= +30.0 dB` separation, `0%` music)",
        "- **Visual Architecture**: `56` decoupled `<2700K` watercolor holds (`>= 15.0s` net hold) joined via `1.0s` `xfade=transition=fade` cross-dissolves (`901.00s` / `15:01` total)",
        f"- **Foley Beds**: `{spec['foley_a']}` + `{spec['foley_b']}`",
        "",
        "## Continuous Narration Script (56 Visual Beats)",
        "",
    ]
    for idx, ((p_idx, _), s_txt, dur_s) in enumerate(zip(spec["lines"], sanitized_lines, spec["durations"]), start=1):
        rows.append(f"{idx:02d}. `[Plate {p_idx:02d} | {dur_s:.2f}s hold]` {s_txt}")
    md_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    gh_ep_dir = GITHUB_MS09_DIR / aid
    gh_ep_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(md_path, gh_ep_dir / md_path.name)
    return md_path


def synthesize_episode_voice_stem(
    kokoro: Kokoro,
    voice_vec: np.ndarray,
    lines: list[tuple[int, str]],
    durations: list[float],
    wdir: Path,
) -> Path:
    voice_stem = wdir / "Voice_Stem.wav"
    if voice_stem.exists() and voice_stem.stat().st_size > 10_000_000:
        return voice_stem

    total_dur = round(sum(durations), 2)
    sanitized_scenes = [sanitize_tts_script(text, for_engine=True) for _, text in lines]
    full_sanitized_script = " ".join(sanitized_scenes)
    word_count = validate_sop_v21_word_budget(full_sanitized_script, is_short=False)
    print(f"    [SOP-v2.1] Sanitized continuous script validated: {word_count} spoken words", flush=True)

    sr = 24000
    raw_24k = wdir / "_voice_raw_24k.wav"
    if not (raw_24k.exists() and raw_24k.stat().st_size > 10_000_000):
        tts_cache = wdir / "tts_cache_v21"
        tts_cache.mkdir(parents=True, exist_ok=True)

        chunks: list[np.ndarray] = []
        base_speed = 0.87
        for idx, s_text in enumerate(sanitized_scenes, start=1):
            cache_npy = tts_cache / f"scene_{idx:02d}.npy"
            if cache_npy.exists():
                wav = np.load(str(cache_npy))
            else:
                wav, _ = kokoro.create(s_text, voice=voice_vec, speed=base_speed, lang="en-us")
                wav = trim_and_fade_speech(wav, sr)
                np.save(str(cache_npy), wav)
            chunks.append(wav)
            if idx < len(sanitized_scenes):
                breath_s = 0.48 if idx in (7, 26, 45) else 0.28
                chunks.append(np.zeros(int(round(breath_s * sr)), dtype=np.float32))

        continuous_buf = np.concatenate(chunks)
        sf.write(str(raw_24k), continuous_buf, sr, subtype="PCM_16")

    raw_48k = wdir / "_voice_raw_48k.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(raw_24k),
            "-af", (
                "aresample=48000,"
                "silenceremove=start_periods=1:start_duration=0.02:start_threshold=-45dB,"
                "areverse,silenceremove=start_periods=1:start_duration=0.03:start_threshold=-45dB,areverse"
            ),
            "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le",
            str(raw_48k),
        ],
        check=True,
        capture_output=True,
    )
    clamped_48k = wdir / "_voice_clamped_48k.wav"
    clamp_narration_silence(raw_48k, clamped_48k, is_short=False)

    tight_48k = wdir / "_voice_tight_48k.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(clamped_48k),
            "-af", (
                "silenceremove=stop_periods=-1:stop_duration=0.42:stop_threshold=-45dB,"
                "areverse,silenceremove=start_periods=1:start_duration=0.02:start_threshold=-45dB,areverse"
            ),
            "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le",
            str(tight_48k),
        ],
        check=True,
        capture_output=True,
    )
    tight_dur = get_audio_duration(tight_48k)

    # 0.35s lead-in + speech + 0.45s tail = 0.80s episode-seam pause in -c copy compilation (<= 1.5s CHK-07!)
    target_speech_span = total_dur - 0.80
    atempo = max(0.84, min(1.18, tight_dur / target_speech_span))
    print(
        f"    [SOP-v2.1] Clamped continuous voice: tight_dur={tight_dur:.2f}s -> target={target_speech_span:.2f}s (atempo={atempo:.5f})",
        flush=True,
    )

    leveled_wav = wdir / "_voice_leveled_48k.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(tight_48k),
            "-af",
            (
                f"atempo={atempo:.6f},"
                "highpass=f=68,lowpass=f=11200,"
                "dynaudnorm=f=120:g=7:p=0.75:m=6.0:s=15.0,"
                "acompressor=threshold=-24dB:ratio=5.0:attack=4:release=110:makeup=3.5dB,"
                "aresample=192000,alimiter=limit=0.72:attack=4:release=50:level=false,aresample=48000,"
                "adelay=350,"
                f"apad=whole_dur={total_dur:.2f},"
                "pan=stereo|c0=c0|c1=c0"
            ),
            "-t", f"{total_dur:.2f}",
            "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(leveled_wav),
        ],
        check=True,
        capture_output=True,
    )
    eb = measure_ebur128(leveled_wav)
    gain_db = -14.0 - eb["integrated_lufs"]
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(leveled_wav),
            "-af", f"volume={gain_db:.3f}dB,aresample=192000,alimiter=limit=0.72:attack=4:release=50:level=false,aresample=48000",
            "-t", f"{total_dur:.2f}",
            "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(voice_stem),
        ],
        check=True,
        capture_output=True,
    )
    eb2 = measure_ebur128(voice_stem)
    if abs(eb2["integrated_lufs"] - (-14.0)) > 0.15:
        corr_db = -14.0 - eb2["integrated_lufs"]
        corr_wav = wdir / "_voice_corr_48k.wav"
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(voice_stem),
                "-af", f"volume={corr_db:.3f}dB,aresample=192000,alimiter=limit=0.72:attack=4:release=50:level=false,aresample=48000",
                "-t", f"{total_dur:.2f}",
                "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
                str(corr_wav),
            ],
            check=True,
            capture_output=True,
        )
        shutil.copyfile(corr_wav, voice_stem)
        corr_wav.unlink(missing_ok=True)

    for tmp_f in (raw_24k, raw_48k, clamped_48k, tight_48k, leveled_wav):
        tmp_f.unlink(missing_ok=True)
    return voice_stem


def build_episode_foley_and_master_audio(
    spec: dict[str, Any],
    voice_stem: Path,
    total_dur: float,
    wdir: Path,
) -> tuple[Path, Path, Path]:
    foley_stem = wdir / "Foley_Stem.wav"
    foley_ducked = wdir / "Foley_Ducked_Stem.wav"
    master_m4a = wdir / "Master_Audio.m4a"
    if master_m4a.exists() and foley_stem.exists() and foley_ducked.exists():
        return foley_stem, foley_ducked, master_m4a

    src_a = FOLEY_LIB / spec["foley_a"]
    src_b = FOLEY_LIB / spec["foley_b"]
    filt = spec["foley_filter"]

    if not foley_stem.exists():
        raw_foley = wdir / "_foley_pre_48k.wav"
        fade_out_st = total_dur - 1.8
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-stream_loop", "-1", "-ss", "3.0", "-t", f"{total_dur + 1:.2f}", "-i", str(src_a),
                "-stream_loop", "-1", "-ss", "37.0", "-t", f"{total_dur + 1:.2f}", "-i", str(src_b),
                "-filter_complex",
                (
                    f"[0:a]volume=0.72[a0];[1:a]volume=0.58[a1];"
                    f"[a0][a1]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
                    f"{filt},"
                    f"dynaudnorm=f=150:g=7:p=0.90:m=5.0,"
                    f"acompressor=threshold=-26dB:ratio=8:attack=15:release=250,"
                    f"afade=t=in:st=0:d=1.2,afade=t=out:st={fade_out_st:.2f}:d=1.8[fout]"
                ),
                "-map", "[fout]", "-t", f"{total_dur:.2f}",
                "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
                str(raw_foley),
            ],
            check=True,
            capture_output=True,
        )
        feb = measure_ebur128(raw_foley)
        fgain_db = -26.2 - feb["integrated_lufs"]
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(raw_foley),
                "-af", f"volume={fgain_db:.3f}dB,alimiter=limit=0.35:attack=5:release=60:level=false",
                "-t", f"{total_dur:.2f}", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
                str(foley_stem),
            ],
            check=True,
            capture_output=True,
        )
        feb2 = measure_ebur128(foley_stem)
        if abs(feb2["integrated_lufs"] - (-26.2)) > 0.15:
            fcorr_db = -26.2 - feb2["integrated_lufs"]
            fcorr_wav = wdir / "_foley_corr_48k.wav"
            subprocess.run(
                [
                    "ffmpeg", "-y", "-i", str(foley_stem),
                    "-af", f"volume={fcorr_db:.3f}dB,alimiter=limit=0.35:attack=5:release=60:level=false",
                    "-t", f"{total_dur:.2f}", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
                    str(fcorr_wav),
                ],
                check=True,
                capture_output=True,
            )
            shutil.copyfile(fcorr_wav, foley_stem)
            fcorr_wav.unlink(missing_ok=True)
        raw_foley.unlink(missing_ok=True)

    # Sidechain-ducked foley bus (-19.0 dB base attenuation + 8:1 speech ducking -> >= +33 dB separation)
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(foley_stem),
            "-i", str(voice_stem),
            "-filter_complex",
            (
                "[0:a]volume=-19.0dB[f_att];"
                "[f_att][1:a]sidechaincompress=threshold=0.012:ratio=8:attack=10:release=380:level_sc=1.0[f_duck]"
            ),
            "-map", "[f_duck]", "-t", f"{total_dur:.2f}",
            "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(foley_ducked),
        ],
        check=True,
        capture_output=True,
    )

    # Sum Voice + Ducked Foley + -70 dBFS stereo TPDF dither -> calibrate exact -14.0 LUFS master AAC 384k
    pre_master = wdir / "_master_pre.wav"
    seed_a = 100 + spec["episode_index"] * 7
    seed_b = 200 + spec["episode_index"] * 13
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(voice_stem),
            "-i", str(foley_ducked),
            "-f", "lavfi", "-i", f"anoisesrc=color=white:r=48000:d={total_dur:.2f}:seed={seed_a}",
            "-f", "lavfi", "-i", f"anoisesrc=color=white:r=48000:d={total_dur:.2f}:seed={seed_b}",
            "-filter_complex",
            (
                "[2:a]volume=0.0003,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=mono[dl];"
                "[3:a]volume=0.0003,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=mono[dr];"
                "[dl][dr]amerge=inputs=2[dither];"
                "[0:a][1:a][dither]amix=inputs=3:duration=first:dropout_transition=0:normalize=0,"
                "aresample=192000,alimiter=limit=0.72:attack=4:release=50:level=false,aresample=48000[mout]"
            ),
            "-map", "[mout]", "-t", f"{total_dur:.2f}",
            "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(pre_master),
        ],
        check=True,
        capture_output=True,
    )
    meb = measure_ebur128(pre_master)
    mgain_db = -14.0 - meb["integrated_lufs"]
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(pre_master),
            "-af", f"volume={mgain_db:.3f}dB,aresample=192000,alimiter=limit=0.72:attack=4:release=50:level=false,aresample=48000",
            "-t", f"{total_dur:.2f}",
            "-c:a", "aac", "-aac_coder", "fast", "-b:a", "384k", "-ar", "48000", "-ac", "2",
            str(master_m4a),
        ],
        check=True,
        capture_output=True,
    )
    pre_master.unlink(missing_ok=True)
    return foley_stem, foley_ducked, master_m4a


def prepare_watermark(wm_out: Path) -> Path:
    if not wm_out.exists():
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(WATERMARK_PNG),
                "-vf", "scale=112:112,format=rgba,colorchannelmixer=aa=0.52",
                str(wm_out),
            ],
            check=True,
            capture_output=True,
        )
    return wm_out


X264_STITCHABLE_ARGS = [
    "-c:v", "libx264", "-profile:v", "high", "-level:v", "4.0",
    "-preset", "ultrafast", "-tune", "stillimage", "-crf", "22",
    "-maxrate", "2400k", "-bufsize", "4800k",
    "-pix_fmt", "yuv420p", "-field_order", "progressive",
    "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
    "-x264-params", "stitchable=1:colorprim=bt709:transfer=bt709:colormatrix=bt709:keyint=48:min-keyint=24:scenecut=0:8x8dct=1:cabac=1",
    "-video_track_timescale", "12288", "-r", "24", "-an",
]


def _crop_expr_for_drift(drift_style: int, start_frame: int, span_frames: int) -> str:
    if drift_style == 0:
        return f"crop=1920:1080:'40+240*(({start_frame}+n)/{span_frames})':'25+130*(({start_frame}+n)/{span_frames})'"
    return f"crop=1920:1080:'280-240*(({start_frame}+n)/{span_frames})':'155-130*(({start_frame}+n)/{span_frames})'"


def _render_body_segment(job: tuple[Path, Path, int, int, int, str, Path]) -> Path:
    plate_2240, wm_rgba, body_frames, start_f, span_f, edge_fade, out_mp4 = job
    if out_mp4.exists() and out_mp4.stat().st_size > 15_000:
        return out_mp4
    tmp_mp4 = out_mp4.with_suffix(".tmp.mp4")
    loop_n = body_frames + 4
    drift_style = int(out_mp4.stem.split("_d")[-1].split("_")[0])
    crop_expr = _crop_expr_for_drift(drift_style, start_f, span_f)
    fade_part = f",{edge_fade}" if edge_fade else ""
    vf = (
        f"[0:v]loop=loop={loop_n}:size=1:start=0,setpts=N/(24*TB),{crop_expr}[bg];"
        f"[1:v]loop=loop={loop_n}:size=1:start=0,setpts=N/(24*TB)[wm];"
        f"[bg][wm]overlay=W-w-28:H-h-24{fade_part},fps=24,format=yuv420p,setfield=prog[vout]"
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-threads", "1",
            "-i", str(plate_2240), "-i", str(wm_rgba),
            "-filter_complex", vf,
            "-map", "[vout]", "-frames:v", str(body_frames),
            *X264_STITCHABLE_ARGS, str(tmp_mp4),
        ],
        check=True,
        capture_output=True,
    )
    tmp_mp4.replace(out_mp4)
    return out_mp4


def _render_xfade_bridge_24f(job: tuple[Path, int, int, int, Path, int, int, Path, Path]) -> Path:
    p_a, drift_a, start_a, span_a, p_b, drift_b, span_b, wm_rgba, out_mp4 = job
    if out_mp4.exists() and out_mp4.stat().st_size > 8_000:
        return out_mp4
    tmp_mp4 = out_mp4.with_suffix(".tmp.mp4")
    crop_a = _crop_expr_for_drift(drift_a, start_a, span_a)
    crop_b = _crop_expr_for_drift(drift_b, 0, span_b)
    vf = (
        f"[0:v]loop=loop=28:size=1:start=0,setpts=N/(24*TB),{crop_a},trim=end_frame=24,fps=24,format=yuv420p[va];"
        f"[1:v]loop=loop=28:size=1:start=0,setpts=N/(24*TB),{crop_b},trim=end_frame=24,fps=24,format=yuv420p[vb];"
        f"[va][vb]xfade=transition=fade:duration=1.0:offset=0.0[vxf];"
        f"[2:v]loop=loop=28:size=1:start=0,setpts=N/(24*TB)[wm];"
        f"[vxf][wm]overlay=W-w-28:H-h-24,fps=24,format=yuv420p,setfield=prog[vout]"
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-threads", "1",
            "-i", str(p_a), "-i", str(p_b), "-i", str(wm_rgba),
            "-filter_complex", vf,
            "-map", "[vout]", "-frames:v", "24",
            *X264_STITCHABLE_ARGS, str(tmp_mp4),
        ],
        check=True,
        capture_output=True,
    )
    tmp_mp4.replace(out_mp4)
    return out_mp4


def render_episode_video_and_mux(
    spec: dict[str, Any],
    master_m4a: Path,
    wm_rgba: Path,
    wdir: Path,
    ep_out_dir: Path,
) -> tuple[Path, Path]:
    asset_id = spec["asset_id"]
    master_mp4 = ep_out_dir / f"{asset_id}_15m_Master.mp4"
    thumb_jpg = ep_out_dir / f"{asset_id}_Thumbnail_1280x720.jpg"
    plates_dir = ep_out_dir / "plates"

    if not thumb_jpg.exists():
        hero_src = plates_dir / f"plate_{spec['hero_plate']:02d}.jpg"
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(hero_src),
                "-vf",
                (
                    "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
                    "eq=contrast=1.04:saturation=0.95:brightness=0.01,"
                    "colorbalance=rs=0.04:gs=0.01:bs=-0.05"
                ),
                "-q:v", "3", str(thumb_jpg),
            ],
            check=True,
            capture_output=True,
        )

    graded_dir = wdir / "plates_2240"
    graded_dir.mkdir(parents=True, exist_ok=True)
    plate_map: dict[int, Path] = {}
    for p_idx in range(1, 9):
        src_p = plates_dir / f"plate_{p_idx:02d}.jpg"
        dst_p = graded_dir / f"plate_{p_idx:02d}_2240.png"
        if not dst_p.exists():
            subprocess.run(
                [
                    "ffmpeg", "-y", "-i", str(src_p),
                    "-vf",
                    (
                        "scale=2240:1260:force_original_aspect_ratio=increase,crop=2240:1260,"
                        "eq=contrast=1.02:saturation=0.92:brightness=-0.01,"
                        "colorbalance=rs=0.04:gs=0.01:bs=-0.05"
                    ),
                    str(dst_p),
                ],
                check=True,
                capture_output=True,
            )
        plate_map[p_idx] = dst_p

    # Stitchable single-pass decoupled holds + 1.0s (24-frame) xfade bridges -> exact 21,624 frames (901.00s)
    seg_dir = wdir / "stitch_xfade_v21"
    seg_dir.mkdir(parents=True, exist_ok=True)

    n_scenes = len(spec["durations"])
    net_frames = [int(round(d * 24)) for d in spec["durations"]]
    total_frames = sum(net_frames)
    assert total_frames == 21624, f"Expected 21624 frames (901.00s), got {total_frames}"

    body_jobs: dict[str, tuple[Path, Path, int, int, int, str, Path]] = {}
    bridge_jobs: dict[str, tuple[Path, int, int, int, Path, int, int, Path, Path]] = {}
    concat_seq: list[Path] = []
    scene_meta: list[tuple[int, int, int, int, int]] = []

    for idx0, ((p_idx, _), nf) in enumerate(zip(spec["lines"], net_frames)):
        s_idx = idx0 + 1
        drift = s_idx % 2
        if idx0 == 0:
            body_f = nf - 12
            start_f = 0
            span_f = nf + 12
        elif idx0 == n_scenes - 1:
            body_f = nf - 12
            start_f = 24
            span_f = nf + 12
        else:
            body_f = nf - 24
            start_f = 24
            span_f = nf + 24
        scene_meta.append((p_idx, drift, body_f, start_f, span_f))

    for idx0, (p_idx, drift, body_f, start_f, span_f) in enumerate(scene_meta):
        tag = "open" if idx0 == 0 else ("close" if idx0 == n_scenes - 1 else "mid")
        b_name = f"body_p{p_idx:02d}_d{drift}_f{body_f:04d}_{tag}.mp4"
        b_path = seg_dir / b_name
        if b_name not in body_jobs:
            if idx0 == 0:
                ef = "fade=t=in:st=0:d=0.80"
            elif idx0 == n_scenes - 1:
                ef = f"fade=t=out:st={max(0.5, (body_f - 24) / 24.0):.3f}:d=1.00"
            else:
                ef = ""
            body_jobs[b_name] = (plate_map[p_idx], wm_rgba, body_f, start_f, span_f, ef, b_path)
        concat_seq.append(b_path)

        if idx0 < n_scenes - 1:
            p_b, drift_b, _, _, span_b = scene_meta[idx0 + 1]
            tail_start_a = start_f + body_f
            xf_name = f"xf_p{p_idx:02d}d{drift}s{tail_start_a}m{span_f}_to_p{p_b:02d}d{drift_b}m{span_b}.mp4"
            xf_path = seg_dir / xf_name
            if xf_name not in bridge_jobs:
                bridge_jobs[xf_name] = (
                    plate_map[p_idx], drift, tail_start_a, span_f,
                    plate_map[p_b], drift_b, span_b,
                    wm_rgba, xf_path,
                )
            concat_seq.append(xf_path)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(_render_body_segment, body_jobs.values()))
        list(pool.map(_render_xfade_bridge_24f, bridge_jobs.values()))

    if not master_mp4.exists():
        total_dur = total_frames / 24.0
        concat_list = seg_dir / "concat_list.txt"
        concat_list.write_text("\n".join(f"file '{p}'" for p in concat_seq) + "\n", encoding="utf-8")
        tmp_out = wdir / f"_{asset_id}_15m_Master.mp4"
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0", "-i", str(concat_list),
                "-i", str(master_m4a),
                "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "copy", "-c:a", "copy",
                "-field_order", "progressive",
                "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                "-t", f"{total_dur:.2f}",
                "-movflags", "+faststart",
                str(tmp_out),
            ],
            check=True,
            capture_output=True,
        )
        shutil.copyfile(tmp_out, master_mp4)
        tmp_out.unlink(missing_ok=True)

    return master_mp4, thumb_jpg


def verify_asset_dual_gates(
    *,
    asset_id: str,
    format_type: str,
    episode_index: int,
    title: str,
    youtube_title: str,
    publish_at_utc: str,
    master_mp4: Path,
    voice_stem: Path,
    foley_stem: Path,
    foley_ducked: Path,
    manifest_path: Path,
    min_dur: float,
    max_dur: float,
) -> dict[str, Any]:
    init_manifest = {
        "asset_id": asset_id,
        "sop_version": "ABR-AG-SOP-v2.1",
        "format_type": format_type,
        "series_id": "MS-09",
        "series_title": "Earth's Slowest Clocks — Volume II",
        "playlist_title": "Earth's Slowest Clocks — Volume II",
        "episode_index": episode_index,
        "title": title,
        "youtube_title": youtube_title,
        "narrator_name": "George-Daniel Baritone",
        "narrator_voice_id": "kokoro_bm_george_daniel_blend_v1",
        "narrator_gender": "male",
        "state": "RENDERED",
        "sha256": sha256_file(master_mp4),
        "stream_metrics": {},
        "youtube_routing": {
            "privacy_status": "private",
            "publish_at_utc": publish_at_utc,
            "series_playlist_id": None,
            "made_for_kids": False,
            "ad_policy": "PRE_MID_POST",
        },
    }
    manifest_path.write_text(json.dumps(init_manifest, indent=2))

    # Gate 1: SOP-03 verify_asset_gate.py (CHK-01 .. CHK-07)
    p = subprocess.run(
        [
            sys.executable,
            str(VERIFY_SCRIPT),
            "--master", str(master_mp4),
            "--voice-stem", str(voice_stem),
            "--foley-stem", str(foley_stem),
            "--manifest", str(manifest_path),
            "--tracker", str(TRACKER_PATH),
            "--declared-min-hold", "15.0",
            "--require-male-narrator",
        ],
        capture_output=True,
        text=True,
    )
    if p.returncode != 0:
        raise RuntimeError(f"SOP-03 verify_asset_gate FAILED for {asset_id}:\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")
    sop03_res = json.loads(p.stdout)

    # Gate 2: Daily Producer qc_gate.py
    qc_res = qc_gate.run_qc_gate(
        master_mp4,
        expected_width=1920,
        expected_height=1080,
        min_duration_sec=min_dur,
        max_duration_sec=max_dur,
        voice_wav=voice_stem,
        foley_wav=foley_ducked,
        narrated=True,
    )
    failed_qc = [k for k, v in qc_res["gates"].items() if not v]
    if failed_qc:
        raise RuntimeError(f"qc_gate FAILED for {asset_id} on {failed_qc}:\n{json.dumps(qc_res, indent=2)}")

    # Explicit strict True Peak (< -2.0 dBFS), H.264 High + BT.709, +faststart, and Zero-Music assertions
    m_tp = float(sop03_res["checks"]["CHK-03"]["master"]["true_peak_dbtp"])
    v_tp = float(sop03_res["checks"]["CHK-03"]["voice"]["true_peak_dbtp"])
    if m_tp >= -2.0 or v_tp >= -2.0:
        raise RuntimeError(f"True Peak ceiling (< -2.0 dBFS) violated for {asset_id}: master={m_tp} dBFS, voice={v_tp} dBFS")
    if sop03_res["checks"]["CHK-04"]["music_detected"] is not False:
        raise RuntimeError(f"Zero-Music violation for {asset_id}: music_detected != False")

    audit_payload = {
        "asset_id": asset_id,
        "title": title,
        "verified_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "state": "QA_VERIFIED",
        "file_size_bytes": master_mp4.stat().st_size,
        "sha256": init_manifest["sha256"],
        "sop03_verify_asset_gate": sop03_res,
        "daily_producer_qc_gate": qc_res,
    }

    audit_dir_ws = SERIES_DIR / "gate_audit_reports"
    audit_dir_gh = GITHUB_MS09_DIR / "gate_audit_reports"
    audit_dir_ws.mkdir(parents=True, exist_ok=True)
    audit_dir_gh.mkdir(parents=True, exist_ok=True)

    audit_ws_file = audit_dir_ws / f"{asset_id}_dual_gate_audit.json"
    audit_ws_file.write_text(json.dumps(audit_payload, indent=2))
    shutil.copyfile(audit_ws_file, audit_dir_gh / audit_ws_file.name)

    manifest_final = json.loads(manifest_path.read_text())
    manifest_final["qc_gate_audit"] = qc_res
    manifest_path.write_text(json.dumps(manifest_final, indent=2))

    # Mirror individual manifest into GitHub repo MS-09/
    if asset_id == "MS09_COMP":
        shutil.copyfile(manifest_path, GITHUB_MS09_DIR / manifest_path.name)
    else:
        gh_ep_dir = GITHUB_MS09_DIR / asset_id
        gh_ep_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(manifest_path, gh_ep_dir / manifest_path.name)

    return {"sop03": sop03_res, "qc_gate": qc_res}


def update_master_ms09_manifest_deliverable(asset_id: str, master_mp4: Path, gate_res: dict[str, Any]) -> None:
    master_manifest_path = SERIES_DIR / "ms09_manifest.json"
    if not master_manifest_path.exists():
        return
    mdata = json.loads(master_manifest_path.read_text())
    sop03 = gate_res["sop03"]["checks"]
    qc = gate_res["qc_gate"]
    for entry in mdata.get("deliverables", []):
        if entry.get("asset_id") == asset_id:
            entry["status"] = "QA_VERIFIED"
            entry["file_size_bytes"] = master_mp4.stat().st_size
            entry["file_size_mb"] = round(master_mp4.stat().st_size / (1024 * 1024), 2)
            entry["sha256"] = sha256_file(master_mp4)
            entry["qa_metrics"] = {
                "duration_sec": qc["duration_sec"],
                "video_codec": qc["video_stream"]["codec_name"],
                "video_profile": qc["video_stream"]["profile"],
                "resolution": f"{qc['video_stream']['width']}x{qc['video_stream']['height']}",
                "r_frame_rate": qc["video_stream"]["r_frame_rate"],
                "color_space": qc["video_stream"]["color_space"],
                "color_primaries": qc["video_stream"]["color_primaries"],
                "color_transfer": qc["video_stream"]["color_transfer"],
                "faststart_verified": qc["container_atoms"]["faststart_verified"],
                "integrated_lufs": sop03["CHK-03"]["master"]["integrated_lufs"],
                "voice_lufs": sop03["CHK-03"]["voice"]["integrated_lufs"],
                "foley_stem_lufs": sop03["CHK-03"]["foley"]["integrated_lufs"],
                "true_peak_dbfs": sop03["CHK-03"]["master"]["true_peak_dbtp"],
                "net_voice_separation_db": sop03["CHK-03"]["net_voice_over_foley_separation_db"],
                "effective_qc_separation_db": qc["stems_audit"]["effective_separation_db"],
                "max_narration_silence_sec": sop03["CHK-07"]["max_narration_silence_sec"],
                "vocal_duty_cycle_pct": sop03["CHK-07"]["vocal_duty_cycle_pct"],
                "music_detected": sop03["CHK-04"]["music_detected"],
                "audit_report": f"gate_audit_reports/{asset_id}_dual_gate_audit.json",
            }
            break
    master_manifest_path.write_text(json.dumps(mdata, indent=2))
    GITHUB_MS09_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(master_manifest_path, GITHUB_MS09_DIR / "ms09_manifest.json")


def build_75m_compilation_lossless(ep_results: list[dict[str, Any]]) -> dict[str, Any]:
    comp_id = "MS09_COMP"
    comp_title = "Earth's Slowest Clocks — Volume II | Complete 75-Minute Calm Documentary (Ep. 1–5)"
    comp_pub = "2026-12-18T15:00:00Z"
    comp_mp4 = SERIES_DIR / "MS09_COMP_75m_FullSeries.mp4"
    comp_manifest = SERIES_DIR / "MS09_COMP_Manifest.json"
    thumb_a = SERIES_DIR / "MS09_COMP_Thumb_Variant_A_1280x720.jpg"
    thumb_b = SERIES_DIR / "MS09_COMP_Thumb_Variant_B_1280x720.jpg"

    wdir = BUILD_ROOT / comp_id
    wdir.mkdir(parents=True, exist_ok=True)

    for hero_src, dst_jpg in [
        (SERIES_DIR / "MS09_COMP_Hero_A_1920x1080.jpg", thumb_a),
        (SERIES_DIR / "MS09_COMP_Hero_B_1920x1080.jpg", thumb_b),
    ]:
        if not dst_jpg.exists():
            subprocess.run(
                [
                    "ffmpeg", "-y", "-i", str(hero_src),
                    "-vf",
                    (
                        "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
                        "eq=contrast=1.04:saturation=0.95:brightness=0.01,"
                        "colorbalance=rs=0.04:gs=0.01:bs=-0.05"
                    ),
                    "-q:v", "3", str(dst_jpg),
                ],
                check=True,
                capture_output=True,
            )

    existing_cm = json.loads(comp_manifest.read_text()) if comp_manifest.exists() else {}
    if comp_mp4.exists() and existing_cm.get("state") == "QA_VERIFIED":
        print("[MS09_COMP] Already QA_VERIFIED — reusing checkpoint!", flush=True)
        return {
            "asset_id": comp_id,
            "master_mp4": str(comp_mp4),
            "manifest": str(comp_manifest),
            "thumb_a": str(thumb_a),
            "thumb_b": str(thumb_b),
            "gates": {"sop03": {"checks": existing_cm.get("sop03_verification", {})}, "qc_gate": existing_cm.get("qc_gate_audit", {})},
        }

    for attempt in range(1, 3):
        try:
            # 1. Concatenate audited episode Voice_Stem, Foley_Stem & Foley_Ducked_Stem to match -c copy compilation
            comp_voice = wdir / "Voice_Stem.wav"
            comp_foley = wdir / "Foley_Stem.wav"
            comp_foley_ducked = wdir / "Foley_Ducked_Stem.wav"

            for out_stem, key in [
                (comp_voice, "voice_stem"),
                (comp_foley, "foley_stem"),
                (comp_foley_ducked, "foley_ducked"),
            ]:
                if not out_stem.exists():
                    s_inputs: list[str] = []
                    for r in ep_results:
                        s_inputs.extend(["-i", str(r[key])])
                    subprocess.run(
                        [
                            "ffmpeg", "-y", *s_inputs,
                            "-filter_complex", "[0:a][1:a][2:a][3:a][4:a]concat=n=5:v=0:a=1[aout]",
                            "-map", "[aout]",
                            "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
                            str(out_stem),
                        ],
                        check=True,
                        capture_output=True,
                    )

            # 2. Write FFMETADATA1 chapter file (00:00:00, 00:15:01, 00:30:02, 00:45:03, 01:00:04)
            ffmeta_path = wdir / "ms09_comp_chapters.ffmetadata"
            meta_lines = [
                ";FFMETADATA1",
                "title=Earth's Slowest Clocks — Volume II | Complete 75-Minute Calm Documentary (Ep. 1–5)",
                "artist=ABR Anti-Brain Rot",
                "",
            ]
            for start_ms, end_ms, ch_title in COMP_CHAPTERS:
                meta_lines.extend(
                    [
                        "[CHAPTER]",
                        "TIMEBASE=1/1000",
                        f"START={start_ms}",
                        f"END={end_ms}",
                        f"title={ch_title}",
                        "",
                    ]
                )
            ffmeta_path.write_text("\n".join(meta_lines), encoding="utf-8")

            # 3. Lossless -c copy concatenation from the 5 QA_VERIFIED episode masters + embedded chapters + +faststart
            if not comp_mp4.exists():
                ep_concat_txt = wdir / "ep_masters_concat.txt"
                ep_concat_txt.write_text(
                    "\n".join(f"file '{r['master_mp4']}'" for r in ep_results) + "\n",
                    encoding="utf-8",
                )
                tmp_comp = wdir / "_MS09_COMP_75m_FullSeries.mp4"
                subprocess.run(
                    [
                        "ffmpeg", "-y",
                        "-f", "concat", "-safe", "0", "-i", str(ep_concat_txt),
                        "-i", str(ffmeta_path),
                        "-map", "0:v:0", "-map", "0:a:0",
                        "-map_metadata", "1", "-map_chapters", "1",
                        "-c", "copy",
                        "-field_order", "progressive",
                        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                        "-movflags", "+faststart",
                        str(tmp_comp),
                    ],
                    check=True,
                    capture_output=True,
                )
                shutil.copyfile(tmp_comp, comp_mp4)
                tmp_comp.unlink(missing_ok=True)

            # Verify 5 embedded chapters via ffprobe
            ch_probe = json.loads(
                subprocess.check_output(
                    ["ffprobe", "-v", "error", "-show_chapters", "-of", "json", str(comp_mp4)],
                    text=True,
                )
            )
            chapters_found = ch_probe.get("chapters", [])
            if len(chapters_found) != 5:
                raise RuntimeError(f"Expected 5 embedded chapters in {comp_mp4.name}, found {len(chapters_found)}")

            gate_res = verify_asset_dual_gates(
                asset_id=comp_id,
                format_type="MASTER_COMPILATION_75M",
                episode_index=6,
                title=comp_title,
                youtube_title=comp_title,
                publish_at_utc=comp_pub,
                master_mp4=comp_mp4,
                voice_stem=comp_voice,
                foley_stem=comp_foley,
                foley_ducked=comp_foley_ducked,
                manifest_path=comp_manifest,
                min_dur=4425.0,
                max_dur=4650.0,
            )
            update_master_ms09_manifest_deliverable(comp_id, comp_mp4, gate_res)
            return {
                "asset_id": comp_id,
                "master_mp4": str(comp_mp4),
                "manifest": str(comp_manifest),
                "thumb_a": str(thumb_a),
                "thumb_b": str(thumb_b),
                "gates": gate_res,
            }
        except Exception as exc:
            print(f"[MS09_COMP] Attempt {attempt} failed gate: {exc}", flush=True)
            quarantine_failed_asset(comp_id, [comp_mp4, comp_manifest], wdir)
            if attempt >= 2:
                raise
    raise RuntimeError("Unreachable")


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="Comma-separated episode IDs to process (e.g. MS09_E01)")
    ap.add_argument("--audio-only", action="store_true", help="Synthesize voice + foley + master audio only")
    ap.add_argument("--skip-comp", action="store_true", help="Skip 75m compilation step")
    args = ap.parse_args()

    only_set = {x.strip() for x in args.only.split(",") if x.strip()}

    t0 = time.time()
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    SERIES_DIR.mkdir(parents=True, exist_ok=True)
    GITHUB_MS09_DIR.mkdir(parents=True, exist_ok=True)
    ensure_tracker_registration()
    wm_rgba = prepare_watermark(BUILD_ROOT / "wm_rgba_112.png")

    print("[MS-09] Loading Kokoro ONNX neural baritone model...", flush=True)
    kokoro = Kokoro(str(KOKORO_MODEL), str(KOKORO_VOICES))
    voice_vec = 0.75 * kokoro.get_voice_style("bm_george") + 0.25 * kokoro.get_voice_style("bm_daniel")

    ep_results: list[dict[str, Any]] = []
    for spec in EPISODE_SPECS:
        ep_t0 = time.time()
        aid = spec["asset_id"]
        wdir = BUILD_ROOT / aid
        wdir.mkdir(parents=True, exist_ok=True)
        ep_out_dir = SERIES_DIR / aid
        ep_out_dir.mkdir(parents=True, exist_ok=True)

        if only_set and aid not in only_set:
            ep_results.append(
                {
                    "asset_id": aid,
                    "master_mp4": ep_out_dir / f"{aid}_15m_Master.mp4",
                    "thumb_jpg": ep_out_dir / f"{aid}_Thumbnail_1280x720.jpg",
                    "manifest": ep_out_dir / f"{aid}_Manifest.json",
                    "voice_stem": ep_out_dir / f"{aid}_Voice_Stem.wav",
                    "foley_stem": ep_out_dir / f"{aid}_Foley_Stem.wav",
                    "foley_ducked": ep_out_dir / f"{aid}_Foley_Ducked_Stem.wav",
                    "gates": {},
                }
            )
            continue

        write_episode_script_markdown(spec, ep_out_dir)
        total_dur = round(sum(spec["durations"]), 2)
        manifest_path = ep_out_dir / f"{aid}_Manifest.json"
        master_mp4_cand = ep_out_dir / f"{aid}_15m_Master.mp4"
        ep_voice_out = ep_out_dir / f"{aid}_Voice_Stem.wav"
        ep_foley_out = ep_out_dir / f"{aid}_Foley_Stem.wav"
        ep_foley_ducked_out = ep_out_dir / f"{aid}_Foley_Ducked_Stem.wav"

        existing_m = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
        if (
            not args.audio_only
            and manifest_path.exists()
            and master_mp4_cand.exists()
            and ep_voice_out.exists()
            and ep_foley_out.exists()
            and ep_foley_ducked_out.exists()
            and existing_m.get("state") == "QA_VERIFIED"
            and existing_m.get("sop_version") == "ABR-AG-SOP-v2.1"
        ):
            print(f"[{aid}] Already SOP-v2.1 QA_VERIFIED — reusing checkpoint!", flush=True)
            ep_results.append(
                {
                    "asset_id": aid,
                    "master_mp4": master_mp4_cand,
                    "thumb_jpg": ep_out_dir / f"{aid}_Thumbnail_1280x720.jpg",
                    "manifest": manifest_path,
                    "voice_stem": ep_voice_out,
                    "foley_stem": ep_foley_out,
                    "foley_ducked": ep_foley_ducked_out,
                    "gates": {"sop03": {"checks": existing_m.get("sop03_verification", {})}, "qc_gate": existing_m.get("qc_gate_audit", {})},
                }
            )
            continue

        for attempt in range(1, 3):
            try:
                print(f"\n[{aid}] 1/4 Synthesizing continuous SOP-v2.1 baritone narration ({total_dur:.2f}s)...", flush=True)
                voice_stem = synthesize_episode_voice_stem(kokoro, voice_vec, spec["lines"], spec["durations"], wdir)

                print(f"[{aid}] 2/4 Filtering organic foley (-26.2 LUFS) & sidechain master audio (-14.0 LUFS, zero music)...", flush=True)
                foley_stem, foley_ducked, master_m4a = build_episode_foley_and_master_audio(spec, voice_stem, total_dur, wdir)

                shutil.copyfile(voice_stem, ep_voice_out)
                shutil.copyfile(foley_stem, ep_foley_out)
                shutil.copyfile(foley_ducked, ep_foley_ducked_out)

                if args.audio_only:
                    print(f"[{aid}] Audio stems ready in {time.time() - ep_t0:.1f}s!", flush=True)
                    break

                print(f"[{aid}] 3/4 Rendering 56 decoupled <2700K watercolor scenes w/ 1.0s xfade & muxing +faststart MP4...", flush=True)
                master_mp4, thumb_jpg = render_episode_video_and_mux(spec, master_m4a, wm_rgba, wdir, ep_out_dir)

                print(f"[{aid}] 4/4 Running SOP-03 verify_asset_gate.py (CHK-01..07) + qc_gate.py...", flush=True)
                gate_res = verify_asset_dual_gates(
                    asset_id=aid,
                    format_type="MINI_SERIES_EPISODE",
                    episode_index=spec["episode_index"],
                    title=spec["title"],
                    youtube_title=spec["youtube_title"],
                    publish_at_utc=spec["publish_at_utc"],
                    master_mp4=master_mp4,
                    voice_stem=ep_voice_out,
                    foley_stem=ep_foley_out,
                    foley_ducked=ep_foley_ducked_out,
                    manifest_path=manifest_path,
                    min_dur=885.0,
                    max_dur=930.0,
                )
                update_master_ms09_manifest_deliverable(aid, master_mp4, gate_res)

                chk03 = gate_res["sop03"]["checks"]["CHK-03"]
                chk04 = gate_res["sop03"]["checks"]["CHK-04"]
                chk07 = gate_res["sop03"]["checks"]["CHK-07"]
                print(
                    f"[{aid}] QA_VERIFIED in {time.time() - ep_t0:.1f}s! "
                    f"Size={master_mp4.stat().st_size / 1e6:.1f}MB | "
                    f"Master={chk03['master']['integrated_lufs']} LUFS (TP={chk03['master']['true_peak_dbtp']} dBFS) | "
                    f"Foley={chk03['foley']['integrated_lufs']} LUFS | "
                    f"Sep=+{chk03['net_voice_over_foley_separation_db']} dB | "
                    f"MaxSilence={chk07['max_narration_silence_sec']}s | "
                    f"VocalDuty={chk07['vocal_duty_cycle_pct']}% | "
                    f"MusicDetected={chk04['music_detected']}",
                    flush=True,
                )
                ep_results.append(
                    {
                        "asset_id": aid,
                        "master_mp4": master_mp4,
                        "thumb_jpg": thumb_jpg,
                        "manifest": manifest_path,
                        "voice_stem": ep_voice_out,
                        "foley_stem": ep_foley_out,
                        "foley_ducked": ep_foley_ducked_out,
                        "gates": gate_res,
                    }
                )
                break
            except Exception as exc:
                print(f"[{aid}] Attempt {attempt} failed gate: {exc}", flush=True)
                quarantine_failed_asset(aid, [master_mp4_cand, manifest_path], wdir)
                if attempt >= 2:
                    raise

    if args.audio_only or args.skip_comp:
        print(f"\n[MS-09] Stage completed in {time.time() - t0:.1f}s!", flush=True)
        return 0

    print("\n[MS09_COMP] Assembling 75-minute Full-Series Compilation via lossless -c copy + embedded chapters...", flush=True)
    comp_res = build_75m_compilation_lossless(ep_results)
    c_chk03 = comp_res["gates"]["sop03"]["checks"]["CHK-03"]
    c_chk04 = comp_res["gates"]["sop03"]["checks"]["CHK-04"]
    c_chk02 = comp_res["gates"]["sop03"]["checks"]["CHK-02"]
    print(
        f"[MS09_COMP] QA_VERIFIED! Duration={c_chk02['duration_sec']}s | "
        f"Master={c_chk03['master']['integrated_lufs']} LUFS (TP={c_chk03['master']['true_peak_dbtp']} dBFS) | "
        f"Sep=+{c_chk03['net_voice_over_foley_separation_db']} dB | MusicDetected={c_chk04['music_detected']}",
        flush=True,
    )
    print(f"\n[MS-09] ALL 6 ASSETS PRODUCED & DUAL-GATE QA_VERIFIED IN {time.time() - t0:.1f}s!", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
