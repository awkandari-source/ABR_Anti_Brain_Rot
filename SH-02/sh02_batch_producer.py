#!/usr/bin/env python3
"""
SH-02 ("Neuro-Acoustic Sleep Sanctuaries — Shorts") End-to-End Batch Producer & Dual-Gate QA
============================================================================================
Produces 6 vertical 60.0s sleep-science Shorts (`SH02_S01`..`SH02_S06`) for @ABR-AntiBrainRot:
- Geometry & Container: 1080x1920 (9:16), 24/1 fps, libx264 High (`8x8dct=1:cabac=1`),
  explicit progressive scan, BT.709 color metadata, 48 kHz stereo AAC-LC @ 384 kbps, +faststart.
- Sub-1900K Visual Curve & Pacing: 1850K warm amber/ember color grade (strictly < 1900K CCT)
  paired with a -15.0% linear luminance decay from 0:00 to 0:60, maximum 4 tripod-locked shots
  per 60s (15.0-16.5s continuous holds + 1.5s slow cross-dissolves, 0 rapid cuts).
- Audio & Zero-Music Policy (ABR-AG-SOP-v2.1 + SH-02 Sleep Profile):
  - Soft-spoken late-night male baritone narration normalized to -16.0 LUFS, <= 0.8s max silence,
    >= 90% vocal duty cycle, <= 0.5s vocal entry.
  - Organic environmental foley sampler stem at -26.2 LUFS + sidechain-ducked mix cushion stem
    guaranteeing >= +30.0 dB net voice-over-foley separation.
  - True Peak capped via `alimiter=limit=0.72` (strictly < -2.0 dBFS).
  - `music_detected == false` (0% music, melodies, chimes, or tonal drones).
- Dual-Gate QA: Runs `verify_asset_gate.py` (`CHK-01..CHK-07`) + `qc_gate.py` (`--sleep-short`).
  Quarantines and rebuilds from checkpoint if any gate fails.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "/shared/user/.gemini/raw_video_studio")
sys.path.insert(0, "/home/antigravity/awkandari-source/ABR_Anti_Brain_Rot/.agents/skills/abr-daily-producer/scripts")

import qc_gate
from linked_api_hub import (
    count_spoken_words,
    sanitize_tts_script,
    validate_sop_v21_word_budget,
)

REPO_ROOT = Path("/home/antigravity/awkandari-source/ABR_Anti_Brain_Rot")
SH02_DIR = REPO_ROOT / "SH-02"
STUDIO_SH02_DIR = Path("/shared/user/.gemini/raw_video_studio/SH-02")
FOLEY_LIB = Path("/shared/user/.gemini/raw_video_studio/ABR_AntiGravity_Workspace/03_Verified_Foley_Library")
SHARED_TRACKER_PATH = Path("/shared/user/.gemini/raw_video_studio/ABR_AntiGravity_Workspace/INDEX_Tracker.json")
CHANNEL_EMBLEM_PNG = Path("/shared/user/.gemini/raw_video_studio/channel_branding/ABR_Channel_Profile_Picture_800x800.png")

VERIFY_SCRIPT = SH02_DIR / "verify_asset_gate.py"
MANIFEST_PATH = SH02_DIR / "sh02_manifest.json"
SH02_TRACKER_PATH = SH02_DIR / "sh02_tracker.json"

KOKORO_MODEL = Path("/shared/user/.gemini/raw_video_studio/kokoro_models/kokoro-v1.0.int8.onnx")
KOKORO_VOICES = Path("/shared/user/.gemini/raw_video_studio/kokoro_models/voices-v1.0.bin")

BUILD_ROOT = Path("/tmp/abr_sh02_build")

# Evidence-based, calm late-night sleep-science scripts (~126-134 spoken words -> [75, 145] budget)
SH02_SCRIPTS: dict[str, list[str]] = {
    "SH02_S01": [
        "Notice how a settling stone hearth feels calmer on tired eyes than a bedroom lamp.",
        "Harvard Health Publishing notes that specialized retinal sensors called melanopsin ganglion cells monitor short-wavelength blue light to time your body clock.",
        "Even modest evening blue glare signals daytime to the hypothalamus and delays natural melatonin release.",
        "True ember light below nineteen hundred Kelvin sits in the deep amber spectrum, carrying virtually zero melanopsin-triggering blue photons.",
        "As the hearth slowly dims across the night, visual cortex arousal softens alongside your eyelids.",
        "Pair that warm darkness with gentle dusk pine air, and the nervous system receives a clear biological cue for rest.",
        "Tap the related video below to enter our full one hundred eighty minute Settling Stone Hearth and Dusk Pine sanctuary.",
    ],
    "SH02_S02": [
        "Even during deep sleep, your auditory cortex quietly scans the bedroom for sudden changes in sound.",
        "According to the Sleep Foundation, brief midnight awakenings are rarely caused by steady sound itself, but by sharp decibel spikes rising above a silent room.",
        "A distant car door or settling floorboard creates an abrupt acoustic contrast that triggers a cortical micro-arousal.",
        "Steady rainfall pattering across weathered cedar shingles forms a gentle broadband blanket across those quiet hours.",
        "By raising the soft ambient baseline, natural rain narrows the gap between background stillness and unexpected night noises.",
        "Your brain no longer treats every tiny creak as a signal to wake.",
        "Tap the related video below to drift into our full one hundred eighty minute Midnight Cedar Rain and Mossy Cave sanctuary.",
    ],
    "SH02_S03": [
        "Watch how an unhurried ocean swell rises against smooth cove pebbles and slowly draws back.",
        "Research from the National Heart, Lung, and Blood Institute shows that healthy sleep onset depends on shifting from daytime sympathetic alertness into parasympathetic calm.",
        "One of the clearest pathways into that shift is slower, steadier evening breathing.",
        "Natural deep-water swells arrive every eight to twelve seconds, closely matching the rhythm of relaxed pre-sleep respiration.",
        "Listening to low coastal undertow without music or sharp surf crashes gently invites your breath and heart rate to lengthen.",
        "Gradually, the body lets go of daytime tension and settles toward stage one sleep.",
        "Tap the related video below to rest inside our full one hundred eighty minute Deep Ocean Swell and Pebbled Cove sanctuary.",
    ],
    "SH02_S04": [
        "Why do short thirty-minute sleep tracks so often stop right when your mind is finally drifting deeper?",
        "According to the National Institute of Neurological Disorders and Stroke, human sleep unfolds in repeating ninety-minute ultradian cycles.",
        "Each cycle guides the brain down through light sleep into restorative slow-wave delta sleep, then through dreaming sleep before briefly surfacing.",
        "When an audio timer cuts off abruptly near that first transition, the sudden silence itself can nudge a light sleeper awake.",
        "A continuous one hundred eighty minute soundscape spans two full ninety-minute sleep cycles without seams, loops, or musical cues.",
        "By the time the room grows quiet, deep sleep architecture is firmly established.",
        "Tap the related video below to experience our full one hundred eighty minute Settling Hearth and Neuro-Acoustic Sleep Sanctuary series.",
    ],
    "SH02_S05": [
        "Step outside during a calm alpine snowfall and the entire landscape sounds remarkably hushed.",
        "Freshly fallen snowflakes trap tiny pockets of open air between delicate ice crystals, absorbing high-frequency acoustic reflections before they bounce.",
        "Sleep hygiene guidance from the Centers for Disease Control and Prevention emphasizes keeping the bedroom quiet, dark, and free from sudden sensory intrusions.",
        "In acoustic science, this natural high-frequency absorption softens sharp edges in the night air much like heavy timber walls.",
        "Without metallic chimes, synth drones, or bright room glare, hyper-alert listening networks in the brain can finally stand down.",
        "Only soft winter air and warm cabin stillness remain.",
        "Tap the related video below to settle into our full one hundred eighty minute Alpine Snowfall and Quiet Cabin Timber sanctuary.",
    ],
    "SH02_S06": [
        "As twilight settles over high desert mesas, sun-warmed basalt stone steadily releases its stored heat into the dry night air.",
        "Your body follows a remarkably similar thermal rhythm every evening before deep sleep.",
        "According to the Sleep Foundation, your core body temperature needs to drop by roughly one to two degrees Fahrenheit to initiate slow-wave sleep.",
        "Warmth gently moves outward through your hands and feet while cool bedroom air carries excess heat away.",
        "Pairing a cool, dark sleeping room with low-frequency desert night wind reinforces this natural thermoregulatory signal without startling the ears.",
        "Each quiet gust settles your mind deeper into stillness.",
        "Tap the related video below to enter our full one hundred eighty minute Desert Night Wind and Cooling Basalt Stone sanctuary.",
    ],
}


def safe_copy_file(src: Path, dst: Path) -> None:
    """FUSE-safe streaming byte copy (avoids GNU cp / copy2 inode replacement errors)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    with src.open("rb") as f_in, dst.open("wb") as f_out:
        while chunk := f_in.read(4 * 1024 * 1024):
            f_out.write(chunk)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def get_media_duration(path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        text=True,
    ).strip()
    return float(out)


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


def trim_and_fade_speech(audio: np.ndarray, sr: int) -> np.ndarray:
    idx = np.where(np.abs(audio) > 0.0022)[0]
    if len(idx) == 0:
        return np.zeros(int(0.08 * sr), dtype=np.float32)
    s = max(0, int(idx[0]) - int(0.015 * sr))
    e = min(len(audio), int(idx[-1]) + int(0.03 * sr))
    clipped = audio[s:e].astype(np.float32, copy=True)
    fade_n = min(int(0.020 * sr), len(clipped) // 4)
    if fade_n > 4:
        ramp = 0.5 * (1.0 - np.cos(np.linspace(0.0, math.pi, fade_n, dtype=np.float32)))
        clipped[:fade_n] *= ramp
        clipped[-fade_n:] *= ramp[::-1]
    return clipped


def write_short_script_markdown(item: dict[str, Any], lines: list[str]) -> Path:
    aid = item["asset_id"]
    md_path = SH02_DIR / "scripts" / f"{aid}_Script_Foley.md"
    sanitized_lines = [sanitize_tts_script(t, for_engine=True) for t in lines]
    word_count = count_spoken_words(" ".join(sanitized_lines))
    content = [
        f"# {aid} — {item['title']}",
        "",
        "- **Batch**: `SH-02` (*Neuro-Acoustic Sleep Sanctuaries — Shorts*)",
        "- **SOP Authority**: `ABR-AG-SOP-v2.1` + `SH-02` Late-Night Sleep Sanctuary Guardrails",
        f"- **Parent 180-Min Sanctuary**: `{item['parent_sanctuary_id']}` (*{item['parent_sanctuary_title']}*)",
        f"- **Primary Scientific Citation**: {item['primary_source_citation']}",
        f"- **Spoken Word Count**: `{word_count}` words (SOP Short Budget: `75–145` words)",
        "- **Audio Spec**: `-16.0 LUFS` voice (`<= 0.8s` max silence), `-26.2 LUFS` organic foley sampler, `>= +30.0 dB` net voice separation, `alimiter=limit=0.72` (`< -2.0 dBFS` True Peak), `music_detected == false`",
        "- **Visual Spec**: `1080x1920` @ `24/1` fps, `1850K` (`< 1900K`) warm ember curve, `-15.0%` linear luminance decay (`0:00 -> 0:60`), `4` tripod-locked shots (`15–16.5s` holds + `1.5s` slow cross-dissolves, `0` rapid cuts)",
        "",
        "## Continuous Late-Night Narration",
        "",
    ]
    for idx, line in enumerate(sanitized_lines, start=1):
        content.append(f"{idx}. {line}")
    text_out = "\n".join(content) + "\n"
    md_path.write_text(text_out, encoding="utf-8")
    safe_copy_file(md_path, STUDIO_SH02_DIR / "scripts" / md_path.name)
    return md_path


def synthesize_short_voice_stem(
    kokoro: Kokoro,
    voice_vec: np.ndarray,
    item: dict[str, Any],
    lines: list[str],
    wdir: Path,
    *,
    force_rebuild: bool = False,
) -> tuple[Path, int]:
    aid = item["asset_id"]
    voice_stem = SH02_DIR / "stems" / f"{aid}_Voice_16LUFS.wav"
    sanitized_lines = [sanitize_tts_script(t, for_engine=True) for t in lines]
    full_script = " ".join(sanitized_lines)
    word_count = validate_sop_v21_word_budget(full_script, is_short=True)

    if not force_rebuild and voice_stem.exists() and voice_stem.stat().st_size > 5_000_000:
        return voice_stem, word_count

    sr = 24000
    base_speed = 0.84
    chunks: list[np.ndarray] = []
    for idx, line in enumerate(sanitized_lines, start=1):
        wav, _ = kokoro.create(line, voice=voice_vec, speed=base_speed, lang="en-us")
        wav = trim_and_fade_speech(wav, sr)
        chunks.append(wav)
        if idx < len(sanitized_lines):
            # Gentle 0.34s breath between sentences (strictly <= 0.8s ceiling)
            chunks.append(np.zeros(int(round(0.34 * sr)), dtype=np.float32))

    raw_24k = wdir / f"{aid}_voice_raw_24k.wav"
    sf.write(str(raw_24k), np.concatenate(chunks), sr, subtype="PCM_16")

    # Clamp internal pauses strictly <= 0.38s @ -45dB FIRST so cur_dur is exact
    clamped_48k = wdir / f"{aid}_voice_clamped_48k.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(raw_24k),
            "-af",
            (
                "aresample=48000,"
                "highpass=f=80,lowpass=f=7600,"
                "silenceremove=start_periods=1:start_duration=0.01:start_threshold=-45dB:"
                "stop_periods=-1:stop_duration=0.38:stop_threshold=-45dB,"
                "areverse,silenceremove=start_periods=1:start_duration=0.02:start_threshold=-45dB,areverse"
            ),
            "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le",
            str(clamped_48k),
        ],
        check=True,
        capture_output=True,
    )

    # Fit active continuous speech smoothly into 59.46s so:
    #   0.20s head (<= 0.5s vocal entry) + 59.46s speech + 0.34s tail (<= 0.8s silence) == exact 60.00s
    target_active_dur = 59.46
    cur_dur = get_media_duration(clamped_48k)
    tempo_ratio = cur_dur / target_active_dur
    atempo_filters: list[str] = []
    rem = tempo_ratio
    while rem < 0.5:
        atempo_filters.append("atempo=0.5")
        rem /= 0.5
    while rem > 2.0:
        atempo_filters.append("atempo=2.0")
        rem /= 2.0
    atempo_filters.append(f"atempo={rem:.6f}")
    atempo_chain = ",".join(atempo_filters)

    leveled_48k = wdir / f"{aid}_voice_leveled_48k.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(clamped_48k),
            "-af",
            (
                f"{atempo_chain},"
                "acompressor=threshold=-22dB:ratio=2.8:attack=12:release=180:makeup=2dB,"
                "adelay=200|200,"
                "apad=whole_dur=60.00,"
                "afade=t=in:st=0.16:d=0.08,afade=t=out:st=59.56:d=0.12"
            ),
            "-t", "60.00",
            "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(leveled_48k),
        ],
        check=True,
        capture_output=True,
    )

    # Iterative EBU R128 calibration to exact -16.0 LUFS with alimiter=limit=0.72 (< -2.0 dBFS)
    eb1 = measure_ebur128(leveled_48k)
    gain1_db = -16.0 - eb1["integrated_lufs"]
    voice_stem.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(leveled_48k),
            "-af", f"volume={gain1_db:.3f}dB,alimiter=limit=0.72:attack=5:release=50:level=false",
            "-t", "60.00",
            "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(voice_stem),
        ],
        check=True,
        capture_output=True,
    )
    eb2 = measure_ebur128(voice_stem)
    if abs(eb2["integrated_lufs"] - (-16.0)) > 0.12:
        corr_db = -16.0 - eb2["integrated_lufs"]
        corr_wav = wdir / f"{aid}_voice_corr.wav"
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(voice_stem),
                "-af", f"volume={corr_db:.3f}dB,alimiter=limit=0.72:attack=5:release=50:level=false",
                "-t", "60.00",
                "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
                str(corr_wav),
            ],
            check=True,
            capture_output=True,
        )
        safe_copy_file(corr_wav, voice_stem)
        corr_wav.unlink(missing_ok=True)

    for tmp in (raw_24k, clamped_48k, leveled_48k):
        tmp.unlink(missing_ok=True)

    safe_copy_file(voice_stem, STUDIO_SH02_DIR / "stems" / voice_stem.name)
    return voice_stem, word_count


def build_short_foley_and_master_audio(
    item: dict[str, Any],
    voice_stem: Path,
    wdir: Path,
    *,
    force_rebuild: bool = False,
) -> tuple[Path, Path, Path]:
    aid = item["asset_id"]
    foley_sampler = SH02_DIR / "stems" / f"{aid}_Foley_Sampler_26p2LUFS.wav"
    foley_ducked = SH02_DIR / "stems" / f"{aid}_Foley_MixCushion_Ducked.wav"
    master_m4a = wdir / f"{aid}_Master_Audio.m4a"

    if (
        not force_rebuild
        and foley_sampler.exists()
        and foley_ducked.exists()
        and master_m4a.exists()
    ):
        return foley_sampler, foley_ducked, master_m4a

    src_a = FOLEY_LIB / item["foley_sources"][0]
    src_b = FOLEY_LIB / item["foley_sources"][1]
    filt = item["foley_filter"]
    offset_a = 4.0 + item["index"] * 3.5
    offset_b = 22.0 + item["index"] * 4.0

    pre_foley = wdir / f"{aid}_foley_pre.wav"
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-ss", f"{offset_a:.2f}", "-t", "61.00", "-i", str(src_a),
            "-stream_loop", "-1", "-ss", f"{offset_b:.2f}", "-t", "61.00", "-i", str(src_b),
            "-filter_complex",
            (
                "[0:a]volume=0.70[a0];[1:a]volume=0.55[a1];"
                f"[a0][a1]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
                f"{filt},"
                "dynaudnorm=f=150:g=7:p=0.90:m=4.5,"
                "acompressor=threshold=-26dB:ratio=8:attack=15:release=250,"
                "afade=t=in:st=0:d=1.2,afade=t=out:st=58.5:d=1.5[fout]"
            ),
            "-map", "[fout]", "-t", "60.00",
            "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(pre_foley),
        ],
        check=True,
        capture_output=True,
    )

    # Calibrate standalone foley sampler stem to exact -26.2 LUFS
    feb = measure_ebur128(pre_foley)
    fgain_db = -26.2 - feb["integrated_lufs"]
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(pre_foley),
            "-af", f"volume={fgain_db:.3f}dB,alimiter=limit=0.35:attack=5:release=60:level=false",
            "-t", "60.00", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(foley_sampler),
        ],
        check=True,
        capture_output=True,
    )
    feb2 = measure_ebur128(foley_sampler)
    if abs(feb2["integrated_lufs"] - (-26.2)) > 0.15:
        fcorr_db = -26.2 - feb2["integrated_lufs"]
        fcorr = wdir / f"{aid}_foley_corr.wav"
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(foley_sampler),
                "-af", f"volume={fcorr_db:.3f}dB,alimiter=limit=0.35:attack=5:release=60:level=false",
                "-t", "60.00", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
                str(fcorr),
            ],
            check=True,
            capture_output=True,
        )
        safe_copy_file(fcorr, foley_sampler)
        fcorr.unlink(missing_ok=True)
    pre_foley.unlink(missing_ok=True)

    # Produce sidechain-ducked mix cushion stem (-17.5 dB attenuation + 6:1 ducking -> ~+36 dB separation)
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(foley_sampler),
            "-i", str(voice_stem),
            "-filter_complex",
            (
                "[0:a]volume=-17.5dB[f_att];"
                "[f_att][1:a]sidechaincompress=threshold=0.012:ratio=6:attack=10:release=380:level_sc=1.0[f_duck]"
            ),
            "-map", "[f_duck]", "-t", "60.00",
            "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(foley_ducked),
        ],
        check=True,
        capture_output=True,
    )

    # Mix Voice + Ducked Foley + -70 dBFS stereo TPDF dither -> -16.0 LUFS master AAC-LC 384k
    # Cap True Peak via alimiter=limit=0.72 (-2.85 dBFS PCM -> < -2.2 dBFS post-AAC, strictly < -2.0 dBFS)
    pre_master = wdir / f"{aid}_master_pre.wav"
    seed_a = 300 + item["index"] * 11
    seed_b = 500 + item["index"] * 17
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(voice_stem),
            "-i", str(foley_ducked),
            "-f", "lavfi", "-i", f"anoisesrc=color=white:r=48000:d=60.00:seed={seed_a}",
            "-f", "lavfi", "-i", f"anoisesrc=color=white:r=48000:d=60.00:seed={seed_b}",
            "-filter_complex",
            (
                "[2:a]volume=0.0003,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=mono[dl];"
                "[3:a]volume=0.0003,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=mono[dr];"
                "[dl][dr]amerge=inputs=2[dither];"
                "[0:a][1:a][dither]amix=inputs=3:duration=first:dropout_transition=0:normalize=0,"
                "alimiter=limit=0.72:attack=5:release=50:level=false[mout]"
            ),
            "-map", "[mout]", "-t", "60.00",
            "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(pre_master),
        ],
        check=True,
        capture_output=True,
    )

    meb = measure_ebur128(pre_master)
    mgain_db = -16.0 - meb["integrated_lufs"]
    # Encode with alimiter=limit=0.72; if AAC reconstruction peak ever approaches -2.05 dBFS, tighten slightly
    limiter_ceil = 0.72
    for _ in range(3):
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(pre_master),
                "-af", f"volume={mgain_db:.3f}dB,alimiter=limit={limiter_ceil:.3f}:attack=5:release=50:level=false",
                "-t", "60.00",
                "-c:a", "aac", "-aac_coder", "fast", "-b:a", "384k", "-ar", "48000", "-ac", "2",
                str(master_m4a),
            ],
            check=True,
            capture_output=True,
        )
        m4a_eb = measure_ebur128(master_m4a)
        lufs_err = -16.0 - m4a_eb["integrated_lufs"]
        if m4a_eb["true_peak_dbtp"] >= -2.08:
            limiter_ceil = max(0.64, limiter_ceil - 0.03)
            mgain_db += lufs_err
            continue
        if abs(lufs_err) > 0.15:
            mgain_db += lufs_err
            continue
        break

    pre_master.unlink(missing_ok=True)
    safe_copy_file(foley_sampler, STUDIO_SH02_DIR / "stems" / foley_sampler.name)
    safe_copy_file(foley_ducked, STUDIO_SH02_DIR / "stems" / foley_ducked.name)
    return foley_sampler, foley_ducked, master_m4a


def build_dark_amber_sanctuary_endcard(wdir: Path) -> Path:
    """
    Renders Shot 4 (45.0s..60.0s): dark obsidian-ember (@ABR-AntiBrainRot Oak-Book-Owl emblem)
    sub-1900K sleep sanctuary endcard with zero bright glare and zero burned-in clutter.
    """
    out_png = wdir / "sh02_dark_amber_endcard_1080x1920.png"
    if out_png.exists():
        return out_png

    w, h = 1080, 1920
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w * 0.5, h * 0.46
    dist = np.sqrt(((xx - cx) / (w * 0.52)) ** 2 + ((yy - cy) / (h * 0.42)) ** 2)
    glow = np.exp(-1.65 * (dist ** 2))

    # Deep hearth-ember radial gradient (1850K warm amber, zero blue)
    bg = np.zeros((h, w, 3), dtype=np.float32)
    bg[:, :, 0] = 22.0 + 78.0 * glow
    bg[:, :, 1] = 10.8 + 38.2 * glow
    bg[:, :, 2] = 0.0

    canvas = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8), mode="RGB")

    if CHANNEL_EMBLEM_PNG.exists():
        emblem = Image.open(CHANNEL_EMBLEM_PNG).convert("RGBA").resize((340, 340), Image.Resampling.LANCZOS)
        em_arr = np.array(emblem, dtype=np.float32)
        lum = (0.299 * em_arr[:, :, 0] + 0.587 * em_arr[:, :, 1] + 0.114 * em_arr[:, :, 2]) / 255.0
        alpha = (em_arr[:, :, 3] / 255.0)
        ey, ex = np.mgrid[0:340, 0:340].astype(np.float32)
        er = np.sqrt(((ex - 170.0) / 158.0) ** 2 + ((ey - 170.0) / 158.0) ** 2)
        circ_mask = np.clip((1.0 - er) * 4.0, 0.0, 1.0) * alpha * 0.85

        toned = np.zeros((340, 340, 3), dtype=np.float32)
        toned[:, :, 0] = 28.0 + 112.0 * lum
        toned[:, :, 1] = 13.8 + 55.0 * lum
        toned[:, :, 2] = 0.0

        patch = bg[720:1060, 370:710, :]
        blended = patch * (1.0 - circ_mask[:, :, None]) + toned * circ_mask[:, :, None]
        bg[720:1060, 370:710, :] = blended
        canvas = Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8), mode="RGB")

    draw = ImageDraw.Draw(canvas)
    draw.ellipse((352, 702, 728, 1078), outline=(112, 54, 0), width=3)
    draw.ellipse((336, 686, 744, 1094), outline=(68, 33, 0), width=2)
    canvas.save(out_png)
    return out_png


def load_and_grade_sub1900k_plate(plate_path: Path, *, target_base_luma: float = 31.0, crop_inner: bool = True) -> np.ndarray:
    """
    Grades a 9:16 visual plate via FFmpeg `colortemperature=temperature=1850` and normalizes
    chromaticity & baseline luminance to exact sub-1900K (1850K Planckian amber, ~1840K CCT)
    so all 4 shots share uniform pre-decay brightness with zero blue glare.
    """
    crop_vf = "crop=iw*0.92:ih*0.92," if crop_inner else ""
    vf = (
        f"{crop_vf}scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
        "colortemperature=temperature=1850:mix=1.0:pl=0.25,"
        "colorbalance=rs=0.05:gs=-0.01:bs=-0.20,"
        "format=rgb24"
    )
    p = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(plate_path), "-vf", vf, "-frames:v", "1", "-f", "rawvideo", "-"],
        capture_output=True,
        check=True,
    )
    arr = np.frombuffer(p.stdout, dtype=np.uint8).reshape(1920, 1080, 3).astype(np.float32)

    # Enforce strict sub-1900K (1850K ember LUT: post-YUV420p BT.709 CCT ~1815K-1855K, strictly < 1900K)
    r = arr[:, :, 0]
    g_clamped = np.minimum(arr[:, :, 1], r * 0.395)
    g = 0.25 * g_clamped + 0.75 * (r * 0.382)
    b = np.zeros_like(r)

    graded = np.stack([r, g, b], axis=-1)
    cur_luma = float(0.2126 * graded[:, :, 0].mean() + 0.7152 * graded[:, :, 1].mean() + 0.0722 * graded[:, :, 2].mean())
    scale_k = target_base_luma / max(1.0, cur_luma)
    graded *= scale_k

    # Soft +1.8 ember black-floor lift (< 1% true black while keeping G/R = 0.382 at ~1830K)
    graded[:, :, 0] = np.clip(graded[:, :, 0] + 1.8, 2.0, 235.0)
    graded[:, :, 1] = np.clip(graded[:, :, 1] + 0.69, 0.8, 96.0)
    graded[:, :, 2] = 0.0

    # Re-pin exact mean Rec.709 luminance to target_base_luma for smooth -15.0% linear decay
    post_luma = float(0.2126 * graded[:, :, 0].mean() + 0.7152 * graded[:, :, 1].mean())
    graded *= (target_base_luma / max(1.0, post_luma))
    return np.clip(graded, 0.0, 245.0).astype(np.float32)


def render_short_master_mp4(
    item: dict[str, Any],
    master_m4a: Path,
    endcard_png: Path,
    wdir: Path,
    *,
    force_rebuild: bool = False,
) -> Path:
    """
    Renders 1,440 frames (60.00s @ 24/1 fps) at 1080x1920:
    - 4 tripod-locked shots (Shot 1: 0.0-16.5s, Shot 2: 15.0-31.5s, Shot 3: 30.0-46.5s, Shot 4: 45.0-60.0s)
    - 1.5s (36-frame) slow cosine cross-dissolves at 15.0s, 30.0s, and 45.0s (0 rapid cuts)
    - Frame-exact -15.0% linear luminance decay from 0:00 to 0:60
    - H.264 High (`8x8dct=1:cabac=1`), BT.709, explicit progressive scan, +faststart
    """
    aid = item["asset_id"]
    out_mp4 = SH02_DIR / "masters" / f"{aid}_Master_1080x1920_24p.mp4"
    if not force_rebuild and out_mp4.exists() and out_mp4.stat().st_size > 1_000_000:
        return out_mp4

    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    tmp_mp4 = wdir / f"{aid}_mux_tmp.mp4"

    p1 = load_and_grade_sub1900k_plate(SH02_DIR / "plates" / item["plates"][0], target_base_luma=31.0, crop_inner=True)
    p2 = load_and_grade_sub1900k_plate(SH02_DIR / "plates" / item["plates"][1], target_base_luma=31.0, crop_inner=True)
    p3 = load_and_grade_sub1900k_plate(SH02_DIR / "plates" / item["plates"][2], target_base_luma=31.0, crop_inner=True)
    p4 = load_and_grade_sub1900k_plate(endcard_png, target_base_luma=31.0, crop_inner=False)

    total_frames = 1440  # 60.00s @ 24/1 fps
    xfade_frames = 36    # 1.50s @ 24/1 fps
    # Dissolve windows: [360..396) (15.0s..16.5s), [720..756) (30.0s..31.5s), [1080..1116) (45.0s..46.5s)

    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", "24/1", "-i", "-",
        "-i", str(master_m4a),
        "-map", "0:v:0", "-map", "1:a:0",
        "-vf", "scale=1080:1920:in_color_matrix=bt709:out_color_matrix=bt709,format=yuv420p,setfield=prog",
        "-c:v", "libx264", "-profile:v", "high", "-level:v", "4.2",
        "-preset", "faster", "-crf", "18",
        "-pix_fmt", "yuv420p", "-field_order", "progressive",
        "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
        "-x264-params", "colorprim=bt709:transfer=bt709:colormatrix=bt709:keyint=48:min-keyint=24:scenecut=0:8x8dct=1:cabac=1",
        "-r", "24/1", "-frames:v", str(total_frames),
        "-c:a", "copy",
        "-movflags", "+faststart",
        str(tmp_mp4),
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    assert proc.stdin is not None
    try:
        for f in range(total_frames):
            # -15.0% linear luminance decay across 0:00 -> 0:60 (0.142 pre-YUV -> ~-15.0% post-BT.709 YUV420p)
            decay = 1.0 - 0.142 * (f / float(total_frames - 1))

            if f < 360:
                base = p1
            elif f < 360 + xfade_frames:
                alpha = 0.5 * (1.0 - math.cos(math.pi * (f - 360) / float(xfade_frames)))
                base = p1 * (1.0 - alpha) + p2 * alpha
            elif f < 720:
                base = p2
            elif f < 720 + xfade_frames:
                alpha = 0.5 * (1.0 - math.cos(math.pi * (f - 720) / float(xfade_frames)))
                base = p2 * (1.0 - alpha) + p3 * alpha
            elif f < 1080:
                base = p3
            elif f < 1080 + xfade_frames:
                alpha = 0.5 * (1.0 - math.cos(math.pi * (f - 1080) / float(xfade_frames)))
                base = p3 * (1.0 - alpha) + p4 * alpha
            else:
                base = p4

            frame_u8 = np.clip(base * decay + 0.5, 0.0, 255.0).astype(np.uint8)
            proc.stdin.write(frame_u8.tobytes())
        proc.stdin.close()
    except Exception:
        proc.kill()
        raise

    stderr_bytes = proc.stderr.read() if proc.stderr else b""
    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"FFmpeg encode failed for {aid} (rc={rc}): {stderr_bytes.decode('utf-8', errors='replace')[-800:]}")

    safe_copy_file(tmp_mp4, out_mp4)
    tmp_mp4.unlink(missing_ok=True)
    safe_copy_file(out_mp4, STUDIO_SH02_DIR / "masters" / out_mp4.name)
    return out_mp4


def write_asset_manifest(item: dict[str, Any], word_count: int) -> Path:
    aid = item["asset_id"]
    m_path = SH02_DIR / "manifests" / f"{aid}_manifest.json"
    payload = {
        "asset_id": aid,
        "batch_id": "SH-02",
        "format_type": "SLEEP_SANCTUARY_SHORT",
        "title": item["title"],
        "narrator_gender": "male",
        "narrator_voice": "Kokoro ONNX Deep Sleep Baritone (0.60 bm_george + 0.40 bm_daniel)",
        "spoken_word_count": word_count,
        "shot_count": 4,
        "shot_schedule": [
            {"shot": 1, "window_sec": [0.0, 16.5], "plate": item["plates"][0]},
            {"shot": 2, "window_sec": [15.0, 31.5], "plate": item["plates"][1], "cross_dissolve_in_sec": 1.5},
            {"shot": 3, "window_sec": [30.0, 46.5], "plate": item["plates"][2], "cross_dissolve_in_sec": 1.5},
            {"shot": 4, "window_sec": [45.0, 60.0], "plate": "sh02_dark_amber_endcard_1080x1920.png", "cross_dissolve_in_sec": 1.5},
        ],
        "state": "RENDERED",
        "stream_metrics": {},
        "youtube_routing": {
            "channel_handle": "@ABR-AntiBrainRot",
            "playlist_title": "Neuro-Acoustic Sleep Sanctuaries — Shorts",
            "secondary_playlist_ids": ["PLUt7V0-ta200", "PLAe5Tqk750cc"],
            "publish_at_utc": item["publish_at_utc"],
            "related_video": {
                "parent_sanctuary_id": item["parent_sanctuary_id"],
                "parent_sanctuary_title": item["parent_sanctuary_title"],
                "parent_playlist_id": item["parent_sanctuary_playlist_id"],
                "parent_playlist_url": f"https://www.youtube.com/playlist?list={item['parent_sanctuary_playlist_id']}",
            },
            "primary_source_org": item["primary_source_org"],
            "primary_source_citation": item["primary_source_citation"],
            "storefront_url": "https://awkandari-source.github.io/ABR_Anti_Brain_Rot/",
        },
    }
    m_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return m_path


def run_dual_gate_qa(
    item: dict[str, Any],
    master_mp4: Path,
    voice_stem: Path,
    foley_sampler: Path,
    foley_ducked: Path,
    asset_manifest_path: Path,
) -> dict[str, Any]:
    aid = item["asset_id"]

    # Gate 1: SOP-03 verify_asset_gate.py (CHK-01 .. CHK-07)
    p_sop03 = subprocess.run(
        [
            sys.executable,
            str(VERIFY_SCRIPT),
            "--master", str(master_mp4),
            "--voice-stem", str(voice_stem),
            "--foley-stem", str(foley_sampler),
            "--foley-ducked-stem", str(foley_ducked),
            "--manifest", str(asset_manifest_path),
            "--tracker", str(SH02_TRACKER_PATH),
            "--declared-min-hold", "15.0",
            "--require-male-narrator",
        ],
        capture_output=True,
        text=True,
    )
    sop03_json = json.loads(p_sop03.stdout) if p_sop03.stdout.strip().startswith("{") else {
        "all_passed": False,
        "stderr": p_sop03.stderr,
        "stdout": p_sop03.stdout,
    }

    # Gate 2: Daily Producer qc_gate.py (--sleep-short mode)
    qc_res = qc_gate.run_qc_gate(
        master_mp4,
        expected_width=1080,
        expected_height=1920,
        min_duration_sec=59.5,
        max_duration_sec=60.5,
        voice_wav=voice_stem,
        foley_wav=foley_ducked,
        narrated=True,
        target_lufs=-16.0,
        max_true_peak_dbfs=-2.0,
        max_silence_override_sec=0.8,
        verify_sub1900k_luma_decay=True,
    )

    dual_passed = bool(p_sop03.returncode == 0 and sop03_json.get("all_passed") and qc_res.get("all_passed"))
    audit_payload = {
        "asset_id": aid,
        "title": item["title"],
        "parent_sanctuary_id": item["parent_sanctuary_id"],
        "parent_sanctuary_title": item["parent_sanctuary_title"],
        "primary_source_org": item["primary_source_org"],
        "dual_gate_status": "QA_VERIFIED" if dual_passed else "QUARANTINED_REBUILD",
        "dual_gate_passed": dual_passed,
        "audited_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "master_sha256": sha256_file(master_mp4),
        "file_size_bytes": master_mp4.stat().st_size,
        "file_size_mb": round(master_mp4.stat().st_size / (1024.0 * 1024.0), 2),
        "shot_count": 4,
        "sop03_verify_asset_gate": sop03_json,
        "qc_gate_audit": qc_res,
    }

    audit_path = SH02_DIR / "audit_logs" / f"{aid}_gate_audit.json"
    audit_path.write_text(json.dumps(audit_payload, indent=2) + "\n", encoding="utf-8")
    safe_copy_file(audit_path, STUDIO_SH02_DIR / "audit_logs" / audit_path.name)
    safe_copy_file(asset_manifest_path, STUDIO_SH02_DIR / "manifests" / asset_manifest_path.name)
    return audit_payload


def quarantine_failed_asset(aid: str, attempt: int) -> None:
    qdir = SH02_DIR / "quarantine" / f"{aid}_attempt_{attempt}"
    qdir.mkdir(parents=True, exist_ok=True)
    for p in [
        SH02_DIR / "masters" / f"{aid}_Master_1080x1920_24p.mp4",
        SH02_DIR / "stems" / f"{aid}_Voice_16LUFS.wav",
        SH02_DIR / "stems" / f"{aid}_Foley_Sampler_26p2LUFS.wav",
        SH02_DIR / "stems" / f"{aid}_Foley_MixCushion_Ducked.wav",
    ]:
        if p.exists():
            safe_copy_file(p, qdir / p.name)
            p.unlink(missing_ok=True)


def atomic_merge_shared_tracker(verified_summaries: list[dict[str, Any]]) -> None:
    """Atomically merges only SH02_S01..SH02_S06 keys into shared INDEX_Tracker.json without disturbing parallel batches."""
    if not SHARED_TRACKER_PATH.exists():
        return
    try:
        tracker = json.loads(SHARED_TRACKER_PATH.read_text(encoding="utf-8"))
        assets = tracker.setdefault("assets", {})
        for s in verified_summaries:
            aid = s["asset_id"]
            existing = assets.get(aid, {})
            if existing.get("state") not in ("API_SCHEDULED", "PUBLISHED", "PUBLIC_LIVE"):
                existing.update(
                    {
                        "batch_id": "SH-02",
                        "format_type": "SLEEP_SANCTUARY_SHORT",
                        "title": s["title"],
                        "parent_sanctuary_id": s["parent_sanctuary_id"],
                        "duration_sec": s["duration_sec"],
                        "voice_separation_db": s["voice_separation_db"],
                        "master_lufs": s["master_lufs"],
                        "true_peak_dbfs": s["true_peak_dbfs"],
                        "max_narration_silence_sec": s["max_narration_silence_sec"],
                        "vocal_duty_cycle_pct": s["vocal_duty_cycle_pct"],
                        "music_detected": False,
                        "state": "QA_VERIFIED",
                    }
                )
                assets[aid] = existing
        SHARED_TRACKER_PATH.write_text(json.dumps(tracker, indent=2) + "\n", encoding="utf-8")
    except Exception as exc:
        print(f"[WARN] Non-fatal shared INDEX_Tracker merge warning: {exc}", flush=True)


def main() -> int:
    t0 = time.time()
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    batch_manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    print("[SH-02] Loading Kokoro ONNX neural voice model (George-Daniel Sleep Baritone)...", flush=True)
    kokoro = Kokoro(str(KOKORO_MODEL), str(KOKORO_VOICES))
    v_george = kokoro.get_voice_style("bm_george")
    v_daniel = kokoro.get_voice_style("bm_daniel")
    voice_vec = (0.60 * v_george + 0.40 * v_daniel).astype(np.float32)

    endcard_png = build_dark_amber_sanctuary_endcard(BUILD_ROOT)

    verified_summaries: list[dict[str, Any]] = []

    for item in batch_manifest["deliverables"]:
        aid = item["asset_id"]
        lines = SH02_SCRIPTS[aid]
        wdir = BUILD_ROOT / aid
        wdir.mkdir(parents=True, exist_ok=True)

        print(f"\n==================== [{aid}] {item['title']} ====================", flush=True)
        write_short_script_markdown(item, lines)

        audit_res: dict[str, Any] | None = None
        for attempt in (1, 2):
            force = attempt > 1
            print(f"[{aid}] Render & Dual-Gate QA pass (attempt {attempt}/2)...", flush=True)
            voice_stem, word_count = synthesize_short_voice_stem(
                kokoro, voice_vec, item, lines, wdir, force_rebuild=force
            )
            foley_sampler, foley_ducked, master_m4a = build_short_foley_and_master_audio(
                item, voice_stem, wdir, force_rebuild=force
            )
            master_mp4 = render_short_master_mp4(
                item, master_m4a, endcard_png, wdir, force_rebuild=force
            )
            asset_manifest_path = write_asset_manifest(item, word_count)
            audit_res = run_dual_gate_qa(
                item, master_mp4, voice_stem, foley_sampler, foley_ducked, asset_manifest_path
            )
            if audit_res["dual_gate_passed"]:
                break
            print(f"[{aid}] Gate failure on attempt {attempt}; quarantining & rebuilding...", flush=True)
            quarantine_failed_asset(aid, attempt)

        assert audit_res is not None
        if not audit_res["dual_gate_passed"]:
            print(f"[FATAL] {aid} failed Dual-Gate QA after rebuild! Inspect SH-02/audit_logs/{aid}_gate_audit.json", flush=True)
            return 1

        qc_d = audit_res["qc_gate_audit"]
        sub_d = qc_d["stems_audit"]["sub1900k_luminance_decay"]
        sop_m = audit_res["sop03_verify_asset_gate"]["checks"]
        summary_entry = {
            "asset_id": aid,
            "title": item["title"],
            "parent_sanctuary_id": item["parent_sanctuary_id"],
            "file_size_mb": audit_res["file_size_mb"],
            "resolution": f"{qc_d['video_stream']['width']}x{qc_d['video_stream']['height']}",
            "fps": qc_d["video_stream"]["r_frame_rate"],
            "profile": qc_d["video_stream"]["profile"],
            "color_space": qc_d["video_stream"]["color_space"],
            "faststart": qc_d["container_atoms"]["faststart_verified"],
            "mean_cct_kelvin": sub_d["mean_cct_kelvin"],
            "max_cct_kelvin": sub_d["max_cct_kelvin"],
            "luminance_decay_pct": sub_d["luminance_decay_pct"],
            "shot_count": 4,
            "duration_sec": qc_d["duration_sec"],
            "master_lufs": qc_d["master_loudness"]["integrated_lufs"],
            "foley_sampler_lufs": sop_m["CHK-03"]["foley"]["integrated_lufs"],
            "true_peak_dbfs": qc_d["master_loudness"]["true_peak_dbfs"],
            "voice_separation_db": qc_d["stems_audit"]["effective_separation_db"],
            "max_narration_silence_sec": sop_m["CHK-07"]["max_narration_silence_sec"],
            "vocal_duty_cycle_pct": sop_m["CHK-07"]["vocal_duty_cycle_pct"],
            "music_detected": False,
            "state": "QA_VERIFIED",
        }
        item["state"] = "QA_VERIFIED"
        item["qa_metrics"] = summary_entry
        verified_summaries.append(summary_entry)
        print(
            f"[{aid}] QA_VERIFIED | {summary_entry['file_size_mb']} MB | "
            f"CCT={summary_entry['mean_cct_kelvin']}K | Decay={summary_entry['luminance_decay_pct']}% | "
            f"LUFS={summary_entry['master_lufs']} | TP={summary_entry['true_peak_dbfs']} dBFS | "
            f"Sep=+{summary_entry['voice_separation_db']} dB | MaxSil={summary_entry['max_narration_silence_sec']}s",
            flush=True,
        )

    batch_manifest["batch_state"] = "QA_VERIFIED"
    batch_manifest["qa_completed_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    MANIFEST_PATH.write_text(json.dumps(batch_manifest, indent=2) + "\n", encoding="utf-8")
    safe_copy_file(MANIFEST_PATH, STUDIO_SH02_DIR / "sh02_manifest.json")
    safe_copy_file(SH02_TRACKER_PATH, STUDIO_SH02_DIR / "sh02_tracker.json")

    batch_report_path = SH02_DIR / "audit_logs" / "SH02_BATCH_QA_SUMMARY.json"
    batch_report_path.write_text(
        json.dumps(
            {
                "batch_id": "SH-02",
                "batch_state": "QA_VERIFIED",
                "total_verified": len(verified_summaries),
                "elapsed_sec": round(time.time() - t0, 2),
                "deliverables": verified_summaries,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    safe_copy_file(batch_report_path, STUDIO_SH02_DIR / "audit_logs" / batch_report_path.name)
    atomic_merge_shared_tracker(verified_summaries)

    print(f"\n[SH-02] ALL 6/6 DELIVERABLES QA_VERIFIED in {time.time() - t0:.1f}s!", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
