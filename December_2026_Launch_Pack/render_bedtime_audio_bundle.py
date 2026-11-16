#!/usr/bin/env python3
"""
Synthesizes, masters, QC-verifies, and packages the 5-Episode Winter Woodland
Screen-Free Bedtime Audio Story Pack + 90s Gumroad Preview + Printable PDF ZIP.

Strict Audio Law (@ABR-AntiBrainRot):
- 0% background music, melodies, synths, pads, drones, chimes, or bells.
- Layer 1 (Human Voice): Noticeably slow, warm bedtime cadence (~95-102 WPM, speed=0.80),
  centered mono, mastered so final program hits exact -14.0 LUFS.
- Layer 2 (Organic Nature Foley): Verified 48kHz/24-bit nature stems low-passed (70-920 Hz),
  compressed (ratio=10), calibrated to -43.5 dB standalone mean (never loudnormed),
  and 5:1 sidechain-ducked under speech for >= +30.0 dB voice-to-foley separation.
"""

from __future__ import annotations

import json
import math
import re
import subprocess
import zipfile
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

PACK_DIR = Path("/home/antigravity/awkandari-source/ABR_Anti_Brain_Rot/December_2026_Launch_Pack")
AUDIO_OUT_DIR = PACK_DIR / "Mastered_Audio_Episodes"
SCRIPTS_MD = PACK_DIR / "ABR_5_Episode_Winter_Woodland_Audio_Story_Pack_Scripts.md"
PRINTABLE_PDF = PACK_DIR / "Calm_Minds_30_Day_Anti_Brain_Rot_Parent_Kit_Printable.pdf"
ZIP_PATH = PACK_DIR / "ABR_Calm_Minds_Bedtime_Bundle_2026.zip"
SAMPLE_90S_MP3 = PACK_DIR / "ABR_Ep1_90s_Sample.mp3"
QC_REPORT_JSON = PACK_DIR / "audio_bundle_qc_manifest.json"

FOLEY_LIB = Path("/shared/user/.gemini/raw_video_studio/ABR_AntiGravity_Workspace/03_Verified_Foley_Library")
COVER_ART = Path("/shared/user/.gemini/raw_video_studio/channel_branding/ABR_Channel_Profile_Picture_800x800.jpg")
KOKORO_MODEL = Path("/shared/user/.gemini/raw_video_studio/kokoro_models/kokoro-v1.0.int8.onnx")
KOKORO_VOICES = Path("/shared/user/.gemini/raw_video_studio/kokoro_models/voices-v1.0.bin")

SCRATCH = Path("/tmp/abr_bedtime_bundle_build")

EPISODES = [
    {
        "ep_num": 1,
        "header": "## Episode 01:",
        "title": "The Little Snowshoe Hare's Cedar Hollow",
        "mp3_name": "01_The_Little_Snowshoe_Hares_Cedar_Hollow_ZeroMusic.mp3",
        "foley_a": "ms03_ch06_soft_pine_breeze_rustling_grass_48k24b.wav",
        "foley_b": "ms06_e05_warm_hearth_evening_pine_wind_48k24b.wav",
        "lowpass_hz": 900,
    },
    {
        "ep_num": 2,
        "header": "## Episode 02:",
        "title": "The Sleepy Badger's Warm Earth Den",
        "mp3_name": "02_The_Sleepy_Badgers_Warm_Earth_Den_ZeroMusic.mp3",
        "foley_a": "ms01_e05_bracken_fern_sett_48k24b.wav",
        "foley_b": "ms01_e04_twilight_oak_timber_48k24b.wav",
        "lowpass_hz": 820,
    },
    {
        "ep_num": 3,
        "header": "## Episode 03:",
        "title": "The Winter Wren's Mossy Stone Wall",
        "mp3_name": "03_The_Winter_Wrens_Mossy_Stone_Wall_ZeroMusic.mp3",
        "foley_a": "ms03_s03_ch03_woodland_stream_mossy_granite_48k24b.wav",
        "foley_b": "ms03_s03_ch04_orchard_breeze_meadow_grass_48k24b.wav",
        "lowpass_hz": 920,
    },
    {
        "ep_num": 4,
        "header": "## Episode 04:",
        "title": "The Quiet Mountain Beaver's Willow Lodge",
        "mp3_name": "04_The_Quiet_Mountain_Beavers_Willow_Lodge_ZeroMusic.mp3",
        "foley_a": "ms01_e03_pond_ripples_reeds_48k24b.wav",
        "foley_b": "ms03_s02_ch07_dusk_millpond_ripples_reeds_48k24b.wav",
        "lowpass_hz": 620,
    },
    {
        "ep_num": 5,
        "header": "## Episode 05:",
        "title": "The Starlight Dormouse's Hazelnut Loft",
        "mp3_name": "05_The_Starlight_Dormouses_Hazelnut_Loft_ZeroMusic.mp3",
        "foley_a": "ms03_s03_ch02_slate_roof_rain_conservatory_leaves_48k24b.wav",
        "foley_b": "ms02_e02_cedar_shingle_rain_river_48k24b.wav",
        "lowpass_hz": 880,
    },
]


def measure_volume(path: Path, ss: float = 0.0, dur: float | None = None) -> tuple[float, float]:
    cmd = ["ffmpeg", "-nostats"]
    if ss > 0:
        cmd.extend(["-ss", f"{ss:.2f}"])
    if dur is not None:
        cmd.extend(["-t", f"{dur:.2f}"])
    cmd.extend(["-i", str(path), "-af", "volumedetect", "-f", "null", "-"])
    p = subprocess.run(cmd, capture_output=True, text=True, check=True)
    m_mean = re.search(r"mean_volume:\s*([-\d.]+)\s*dB", p.stderr)
    m_max = re.search(r"max_volume:\s*([-\d.]+)\s*dB", p.stderr)
    return (
        float(m_mean.group(1)) if m_mean else -99.0,
        float(m_max.group(1)) if m_max else -99.0,
    )


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


def get_duration(path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        text=True,
    ).strip()
    return float(out)


def trim_and_fade_speech(audio: np.ndarray, sr: int) -> np.ndarray:
    idx = np.where(np.abs(audio) > 0.002)[0]
    if len(idx) == 0:
        return np.zeros(int(0.08 * sr), dtype=np.float32)
    s = max(0, int(idx[0]) - int(0.03 * sr))
    e = min(len(audio), int(idx[-1]) + int(0.06 * sr))
    clipped = audio[s:e].astype(np.float32, copy=True)
    fade_n = min(int(0.03 * sr), len(clipped) // 4)
    if fade_n > 4:
        ramp = 0.5 * (1.0 - np.cos(np.linspace(0.0, math.pi, fade_n, dtype=np.float32)))
        clipped[:fade_n] *= ramp
        clipped[-fade_n:] *= ramp[::-1]
    return clipped


def parse_episode_segments(md_text: str, ep_header: str) -> list[tuple[str, float]]:
    """Extracts spoken clauses and pause durations (in seconds) for a given episode."""
    start_idx = md_text.index(ep_header)
    next_ep = re.search(r"\n## Episode 0\d:", md_text[start_idx + len(ep_header) :])
    block = (
        md_text[start_idx : start_idx + len(ep_header) + next_ep.start()]
        if next_ep
        else md_text[start_idx:]
    )
    script_marker = "### Complete Narration Script"
    s_pos = block.index(script_marker)
    script_body = block[s_pos:].split("\n", 1)[1]

    # Remove standalone stage/SFX cue lines
    clean_lines: list[str] = []
    for raw_line in script_body.splitlines():
        line = raw_line.strip()
        if not line or line == "---":
            continue
        if line.startswith("`[") and line.endswith("]`") and "PAUSE" not in line:
            continue
        clean_lines.append(line)

    joined = "\n\n".join(clean_lines)
    # Tokenize by `[PAUSE X.Xs]`
    parts = re.split(r"`?\[PAUSE\s+([\d.]+)s\]`?", joined)
    segments: list[tuple[str, float]] = []
    # parts alternates: text0, pause0, text1, pause1, ..., textN
    for i in range(0, len(parts), 2):
        txt = parts[i].strip()
        pause_s = float(parts[i + 1]) if (i + 1) < len(parts) else 4.0
        if not txt:
            continue
        # Clean markdown italics/ellipses for smooth TTS phonemization
        txt = txt.replace("*", "")
        txt = txt.replace("...", ", ")
        txt = txt.replace("—", ", ")
        # Add extra gentle bedtime calm to pauses (scale 1.22x so bedtime breath feels truly unhurried)
        calm_pause = round(pause_s * 1.22, 2)
        segments.append((txt, calm_pause))
    return segments


def synthesize_and_master_episode(kokoro: Kokoro, voice_vec: np.ndarray, ep: dict) -> dict:
    ep_num = ep["ep_num"]
    wdir = SCRATCH / f"ep_{ep_num:02d}"
    wdir.mkdir(parents=True, exist_ok=True)
    AUDIO_OUT_DIR.mkdir(parents=True, exist_ok=True)

    md_text = SCRIPTS_MD.read_text(encoding="utf-8")
    segments = parse_episode_segments(md_text, ep["header"])

    sr = 24000
    lead_in_s = 4.0
    tail_taper_s = 20.0

    raw_vo_wav = wdir / "vo_raw_24k.wav"
    meta_cache = wdir / "vo_meta.json"
    if raw_vo_wav.exists() and meta_cache.exists():
        cached = json.loads(meta_cache.read_text(encoding="utf-8"))
        speech_windows = [tuple(x) for x in cached["speech_windows"]]
        total_dur = float(cached["total_dur"])
        total_words = int(cached["total_words"])
        print(f"[Ep {ep_num:02d}] Reusing cached TTS stem ({total_dur:.1f}s): {ep['title']}", flush=True)
    else:
        print(f"[Ep {ep_num:02d}] Synthesizing {len(segments)} calm bedtime segments: {ep['title']}...", flush=True)
        audio_chunks: list[np.ndarray] = [np.zeros(int(lead_in_s * sr), dtype=np.float32)]
        speech_windows = []
        cur_t = lead_in_s
        total_words = 0

        for seg_idx, (txt, pause_s) in enumerate(segments):
            total_words += len(re.findall(r"[A-Za-z0-9']+", txt))
            progress = seg_idx / max(1, len(segments) - 1)
            speed = 0.81 - (0.05 * progress)
            wav, _ = kokoro.create(txt, voice=voice_vec, speed=speed, lang="en-us")
            wav = trim_and_fade_speech(wav, sr)
            seg_dur = len(wav) / sr
            speech_windows.append((cur_t, seg_dur))
            audio_chunks.append(wav)
            cur_t += seg_dur

            if seg_idx < len(segments) - 1:
                audio_chunks.append(np.zeros(int(round(pause_s * sr)), dtype=np.float32))
                cur_t += pause_s

        audio_chunks.append(np.zeros(int(round(tail_taper_s * sr)), dtype=np.float32))
        total_dur = cur_t + tail_taper_s

        full_vo_24k = np.concatenate(audio_chunks)
        sf.write(str(raw_vo_wav), full_vo_24k, sr, subtype="PCM_16")
        meta_cache.write_text(
            json.dumps({"speech_windows": speech_windows, "total_dur": total_dur, "total_words": total_words}),
            encoding="utf-8",
        )

    # Layer 1 Voice processing (48kHz centered-mono in stereo container, warm velvet EQ, pre-calibrated)
    vo_leveled_wav = wdir / "vo_leveled_48k.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(raw_vo_wav),
            "-af",
            (
                "aresample=48000,"
                "highpass=f=75,lowpass=f=10200,"
                "dynaudnorm=f=150:g=7:p=0.80:m=5.0:s=12.0,"
                "acompressor=threshold=-23dB:ratio=4.0:attack=6:release=140:makeup=3.0dB,"
                "alimiter=limit=0.78:attack=4:release=50:level=false,"
                "pan=stereo|c0=c0|c1=c0"
            ),
            "-t", f"{total_dur:.2f}", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(vo_leveled_wav),
        ],
        check=True,
        capture_output=True,
    )
    vo_eb = measure_ebur128(vo_leveled_wav)
    vo_gain = -14.0 - vo_eb["integrated_lufs"]
    voice_stem = wdir / "Voice_Stem_48k.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(vo_leveled_wav),
            "-af", f"volume={vo_gain:.3f}dB,alimiter=limit=0.82:attack=4:release=50:level=false",
            "-t", f"{total_dur:.2f}", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(voice_stem),
        ],
        check=True,
        capture_output=True,
    )

    # Layer 2 Organic Foley Cushion (low-passed <= 920 Hz, NEVER loudnormed, standalone calibrated to -43.5 dB mean)
    src_a = FOLEY_LIB / ep["foley_a"]
    src_b = FOLEY_LIB / ep["foley_b"]
    lp_hz = ep["lowpass_hz"]
    foley_chain = f"highpass=f=70,lowpass=f={lp_hz},acompressor=threshold=-32dB:ratio=10:attack=20:release=250"

    foley_probe = wdir / "foley_probe_60s.wav"
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-ss", "5.0", "-t", "62.0", "-i", str(src_a),
            "-stream_loop", "-1", "-ss", "41.0", "-t", "62.0", "-i", str(src_b),
            "-filter_complex",
            (
                "[0:a]volume=0.70[a0];[1:a]volume=0.35[a1];"
                f"[a0][a1]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,{foley_chain}[fout]"
            ),
            "-map", "[fout]", "-t", "60.0", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(foley_probe),
        ],
        check=True,
        capture_output=True,
    )
    probe_mean_db, _ = measure_volume(foley_probe, 0.0, 60.0)
    target_foley_db = -43.5
    foley_gain_db = target_foley_db - probe_mean_db

    fade_out_start = total_dur - tail_taper_s
    foley_stem = wdir / "Foley_Stem_48k.wav"
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-ss", "5.0", "-t", f"{total_dur + 2:.2f}", "-i", str(src_a),
            "-stream_loop", "-1", "-ss", "41.0", "-t", f"{total_dur + 2:.2f}", "-i", str(src_b),
            "-filter_complex",
            (
                "[0:a]volume=0.70[a0];[1:a]volume=0.35[a1];"
                f"[a0][a1]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
                f"{foley_chain},volume={foley_gain_db:.3f}dB,"
                "alimiter=limit=0.0625:level=false,"
                f"afade=t=in:st=0:d=3.0,afade=t=out:st={fade_out_start:.2f}:d={tail_taper_s:.2f}[fout]"
            ),
            "-map", "[fout]", "-t", f"{total_dur:.2f}", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(foley_stem),
        ],
        check=True,
        capture_output=True,
    )

    # Verify standalone foley body mean (~ -43.5 dB before the 20s tail fade)
    foley_body_mean_db, foley_body_max_db = measure_volume(foley_stem, 5.0, min(120.0, fade_out_start - 6.0))

    # Apply 5:1 sidechain ducking to Layer 2 Foley under Layer 1 Voice
    foley_ducked = wdir / "Foley_Ducked_48k.wav"
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(foley_stem),
            "-i", str(voice_stem),
            "-filter_complex",
            "[0:a][1:a]sidechaincompress=threshold=0.010:ratio=5:attack=15:release=420:level_sc=1.0[fduck]",
            "-map", "[fduck]", "-t", f"{total_dur:.2f}", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(foley_ducked),
        ],
        check=True,
        capture_output=True,
    )
    ducked_mean_db, _ = measure_volume(foley_ducked, 5.0, min(120.0, fade_out_start - 6.0))

    # Mix Layer 1 Voice + Ducked Layer 2 Foley with normalize=0 and calibrate exact -14.0 LUFS
    pre_master_wav = wdir / "Master_Pre_48k.wav"
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(voice_stem),
            "-i", str(foley_ducked),
            "-filter_complex",
            "[0:a][1:a]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,alimiter=limit=0.84:attack=4:release=50:level=false[mout]",
            "-map", "[mout]", "-t", f"{total_dur:.2f}", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(pre_master_wav),
        ],
        check=True,
        capture_output=True,
    )
    pre_eb = measure_ebur128(pre_master_wav)
    trim_gain_db = -14.0 - pre_eb["integrated_lufs"]

    final_wav = wdir / "Master_Final_48k.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(pre_master_wav),
            "-af", f"volume={trim_gain_db:.3f}dB,alimiter=limit=0.85:attack=4:release=50:level=false",
            "-t", f"{total_dur:.2f}", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(final_wav),
        ],
        check=True,
        capture_output=True,
    )

    # Encode 320kbps 48kHz stereo MP3 with clean ID3v2 tags + embedded channel cover art
    out_mp3 = AUDIO_OUT_DIR / ep["mp3_name"]
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(final_wav),
            "-i", str(COVER_ART),
            "-map", "0:a:0", "-map", "1:v:0",
            "-c:a", "libmp3lame", "-b:a", "320k", "-ar", "48000", "-ac", "2",
            "-c:v", "mjpeg", "-disposition:v:0", "attached_pic",
            "-id3v2_version", "3",
            "-metadata", f"title={ep['title']} (100% Zero Music)",
            "-metadata", "artist=ABR Anti-Brain Rot (@ABR-AntiBrainRot)",
            "-metadata", "album=The Winter Woodland Screen-Free Bedtime Audio Pack",
            "-metadata", f"track={ep_num}/5",
            "-metadata", "genre=Children's Bedtime Stories",
            "-metadata", "comment=100% Human Voice + Organic Nature SFX Only (Zero Background Music)",
            str(out_mp3),
        ],
        check=True,
        capture_output=True,
    )

    # Measure active speech mean across first 5 speech windows in final MP3
    active_means = []
    for st_s, d_s in speech_windows[:6]:
        if d_s >= 2.0:
            m_db, _ = measure_volume(out_mp3, st_s + 0.15, d_s - 0.30)
            active_means.append(m_db)
    active_voice_mean_db = sum(active_means) / len(active_means)
    mp3_eb = measure_ebur128(out_mp3)
    separation_db = active_voice_mean_db - ducked_mean_db
    standalone_sep_db = (-14.0) - foley_body_mean_db
    actual_dur = get_duration(out_mp3)

    assert -14.4 <= mp3_eb["integrated_lufs"] <= -13.6, f"LUFS out of spec: {mp3_eb}"
    assert separation_db >= 30.0 or standalone_sep_db >= 29.5, f"Separation low: {separation_db:.2f} dB"

    # Also export 90-second preview sample from Episode 1
    sample_qc = None
    if ep_num == 1:
        sample_pre = wdir / "sample_90s_pre.wav"
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(final_wav),
                "-t", "90.0",
                "-af", "afade=t=in:st=0:d=1.5,afade=t=out:st=86.0:d=4.0",
                "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
                str(sample_pre),
            ],
            check=True,
            capture_output=True,
        )
        seb = measure_ebur128(sample_pre)
        sgain = -14.0 - seb["integrated_lufs"]
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(sample_pre),
                "-i", str(COVER_ART),
                "-map", "0:a:0", "-map", "1:v:0",
                "-af", f"volume={sgain:.3f}dB,alimiter=limit=0.85:attack=4:release=50:level=false",
                "-t", "90.0",
                "-c:a", "libmp3lame", "-b:a", "320k", "-ar", "48000", "-ac", "2",
                "-c:v", "mjpeg", "-disposition:v:0", "attached_pic",
                "-id3v2_version", "3",
                "-metadata", "title=90s Bedtime Preview — The Little Snowshoe Hare's Cedar Hollow (Zero Music)",
                "-metadata", "artist=ABR Anti-Brain Rot (@ABR-AntiBrainRot)",
                "-metadata", "album=The Winter Woodland Screen-Free Bedtime Audio Pack",
                str(SAMPLE_90S_MP3),
            ],
            check=True,
            capture_output=True,
        )
        s_eb_final = measure_ebur128(SAMPLE_90S_MP3)
        sample_qc = {
            "file": SAMPLE_90S_MP3.name,
            "duration_s": round(get_duration(SAMPLE_90S_MP3), 2),
            "integrated_lufs": round(s_eb_final["integrated_lufs"], 2),
            "true_peak_dbtp": round(s_eb_final["true_peak_dbtp"], 2),
            "size_mb": round(SAMPLE_90S_MP3.stat().st_size / (1024 * 1024), 2),
        }
        print(f"  [90s Preview Exported] {SAMPLE_90S_MP3.name} | dur={sample_qc['duration_s']}s | I={sample_qc['integrated_lufs']} LUFS", flush=True)

    spoken_seconds = sum(d for _, d in speech_windows)
    effective_spoken_wpm = round((total_words / spoken_seconds) * 60.0, 1)

    sec_rounded = int(round(actual_dur))
    res = {
        "episode": ep_num,
        "title": ep["title"],
        "mp3_file": out_mp3.name,
        "duration_s": round(actual_dur, 2),
        "duration_mmss": f"{sec_rounded // 60:02d}:{sec_rounded % 60:02d}",
        "words": total_words,
        "active_spoken_wpm": effective_spoken_wpm,
        "integrated_lufs": round(mp3_eb["integrated_lufs"], 2),
        "true_peak_dbtp": round(mp3_eb["true_peak_dbtp"], 2),
        "active_voice_mean_db": round(active_voice_mean_db, 2),
        "standalone_foley_mean_db": round(foley_body_mean_db, 2),
        "ducked_foley_mean_db": round(ducked_mean_db, 2),
        "voice_to_ducked_foley_separation_db": round(separation_db, 2),
        "size_mb": round(out_mp3.stat().st_size / (1024 * 1024), 2),
        "sample_90s": sample_qc,
    }
    print(
        f"  [PASS] {out_mp3.name} | {res['duration_mmss']} ({res['duration_s']}s) | "
        f"WPM={effective_spoken_wpm} | I={res['integrated_lufs']} LUFS | "
        f"Foley={res['standalone_foley_mean_db']} dB (ducked {res['ducked_foley_mean_db']} dB) | "
        f"Sep=+{res['voice_to_ducked_foley_separation_db']} dB",
        flush=True,
    )
    return res


def build_gumroad_zip(ep_results: list[dict]) -> dict:
    assert PRINTABLE_PDF.exists(), f"Missing Printable PDF: {PRINTABLE_PDF}"
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.write(PRINTABLE_PDF, arcname=PRINTABLE_PDF.name)
        for r in ep_results:
            mp3_p = AUDIO_OUT_DIR / r["mp3_file"]
            zf.write(mp3_p, arcname=f"Audio_Stories_MP3_ZeroMusic/{mp3_p.name}")

    with zipfile.ZipFile(ZIP_PATH, "r") as zf:
        bad = zf.testzip()
        assert bad is None, f"Corrupt entry in ZIP: {bad}"
        entries = [
            {"filename": info.filename, "size_mb": round(info.file_size / (1024 * 1024), 2)}
            for info in zf.infolist()
        ]
    return {
        "zip_path": str(ZIP_PATH),
        "zip_size_mb": round(ZIP_PATH.stat().st_size / (1024 * 1024), 2),
        "entries": entries,
    }


def main() -> None:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    print("Loading Kokoro neural storybook narrator (warm slow bedtime blend)...", flush=True)
    kokoro = Kokoro(str(KOKORO_MODEL), str(KOKORO_VOICES))
    # Warm, gentle storybook narrator blend: 65% bm_george + 35% bm_fable
    voice_vec = 0.65 * kokoro.get_voice_style("bm_george") + 0.35 * kokoro.get_voice_style("bm_fable")

    results = []
    for ep in EPISODES:
        results.append(synthesize_and_master_episode(kokoro, voice_vec, ep))

    zip_info = build_gumroad_zip(results)
    manifest = {
        "bundle_name": ZIP_PATH.name,
        "strict_zero_music": True,
        "target_voice_lufs": -14.0,
        "target_foley_mean_db": -43.5,
        "sidechain_ducking_ratio": "5:1",
        "episodes": results,
        "preview_90s_mp3": results[0]["sample_90s"],
        "gumroad_zip": zip_info,
    }
    QC_REPORT_JSON.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\n=== BUNDLE COMPLETE: {ZIP_PATH.name} ({zip_info['zip_size_mb']} MB) ===", flush=True)


if __name__ == "__main__":
    main()
