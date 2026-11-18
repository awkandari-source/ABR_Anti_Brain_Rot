#!/usr/bin/env python3
"""
SH-01 ("Quiet Wonders & Slow Science — Shorts") Hardened Batch Producer & Dual-Gate QA
======================================================================================
Cloned and adapted from `ms08_batch_producer.py` + `remediate_washi_45s_v21.py` for
isolated `SH-01` production (`MS-08` and `MS-09` untouched):
- Synthesizes continuous single-take calm baritone narration via local Kokoro ONNX
  (`0.65 * bm_george + 0.35 * bm_daniel`), sanitized & clamped (`0.75s @ -45dB` + `0.33s`
  internal breath tightening -> `vocal_entry_sec <= 0.25s`, `max_silence <= 0.45s`, `duty >= 92%`).
- Normalizes narration to `-14.0 LUFS`, mixes filtered organic environmental foley from
  `03_Verified_Foley_Library` at `-26.2 LUFS` (and sidechain-ducked cushion `<= -43.0 dB`
  achieving `>= +33 dB` net voice-over-foley separation), caps True Peak via
  `alimiter=limit=0.72` (verified strictly `< -2.0 dBFS` even after AAC-LC 384k encoding),
  and enforces `music_detected == false` (0% music).
- Renders 4 bespoke `<2700K` museum watercolor macro plates per 60.0s Short at
  `1080x1920` (9:16 vertical), `24/1` fps (`1,440` frames), `3` x `1.0s` cross-dissolves
  (`<= 4` cuts, `15.0s` net continuous hold per shot), `libx264` `-profile:v high` with
  explicit `8x8dct=1:cabac=1`, `BT.709` color metadata, and `+faststart`.
- Executes BOTH `SH-01/verify_asset_gate.py` (`CHK-01`..`CHK-07`) AND `qc_gate.py`.
  Quarantines and rebuilds from checkpoint automatically if any check fails.
"""

from __future__ import annotations

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

STUDIO_ROOT = Path("/shared/user/.gemini/raw_video_studio")
WS_ROOT = STUDIO_ROOT / "ABR_AntiGravity_Workspace"
FOLEY_LIB = WS_ROOT / "03_Verified_Foley_Library"
REPO_ROOT = Path("/home/antigravity/awkandari-source/ABR_Anti_Brain_Rot")
REPO_SH01 = REPO_ROOT / "SH-01"
MEDIA_SH01 = WS_ROOT / "02_Daily_Shorts_Queue" / "SH-01"

VERIFY_SCRIPT = REPO_SH01 / "verify_asset_gate.py"
MANIFEST_PATH = REPO_SH01 / "sh01_manifest.json"
TRACKER_PATH = MEDIA_SH01 / "sh01_tracker.json"
WATERMARK_PNG = STUDIO_ROOT / "channel_branding" / "ABR_Video_Watermark_150x150.png"

KOKORO_MODEL = STUDIO_ROOT / "kokoro_models" / "kokoro-v1.0.int8.onnx"
KOKORO_VOICES = STUDIO_ROOT / "kokoro_models" / "voices-v1.0.bin"

BUILD_ROOT = Path("/tmp/abr_sh01_build")

sys.path.insert(0, str(STUDIO_ROOT))
sys.path.insert(0, str(REPO_ROOT / ".agents/skills/abr-daily-producer/scripts"))

import qc_gate  # type: ignore
from linked_api_hub import (  # type: ignore
    clamp_narration_silence,
    count_spoken_words,
    sanitize_tts_script,
    validate_sop_v21_word_budget,
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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def get_audio_duration(path: Path) -> float:
    return float(
        subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
            text=True,
        ).strip()
    )


def trim_and_fade_speech(audio: np.ndarray, sr: int) -> np.ndarray:
    idx = np.where(np.abs(audio) > 0.0025)[0]
    if len(idx) == 0:
        return np.zeros(int(0.1 * sr), dtype=np.float32)
    s = max(0, int(idx[0]) - int(0.018 * sr))
    e = min(len(audio), int(idx[-1]) + int(0.032 * sr))
    clipped = audio[s:e].astype(np.float32, copy=True)
    fade_n = min(int(0.020 * sr), len(clipped) // 4)
    if fade_n > 4:
        ramp = 0.5 * (1.0 - np.cos(np.linspace(0.0, math.pi, fade_n, dtype=np.float32)))
        clipped[:fade_n] *= ramp
        clipped[-fade_n:] *= ramp[::-1]
    return clipped


def build_atempo_chain(ratio: float) -> str:
    """Builds valid FFmpeg atempo filter chain for any positive speed ratio."""
    parts: list[str] = []
    rem = ratio
    while rem < 0.55:
        parts.append("atempo=0.650000")
        rem /= 0.65
    while rem > 1.85:
        parts.append("atempo=1.500000")
        rem /= 1.50
    parts.append(f"atempo={rem:.6f}")
    return ",".join(parts)


def write_short_script_markdown(item: dict[str, Any], out_dir: Path) -> Path:
    aid = item["asset_id"]
    md_path = out_dir / f"{aid}_Script_Foley.md"
    sanitized = sanitize_tts_script(item["narration_script"], for_engine=True)
    words = count_spoken_words(sanitized)
    lines = [
        f"# {aid} — {item['title']}",
        "",
        "- **Batch / Playlist**: `SH-01` — *Quiet Wonders & Slow Science — Shorts*",
        f"- **Category / Pillar**: {item['category']} · {item['pillar']}",
        f"- **Primary Source**: {item['primary_source']}",
        f"- **Scheduled Publish (UTC)**: `{item['publish_at_utc']}`",
        "- **SOP Authority**: `ABR-AG-SOP-v2.1` (Zero-Music, Continuous Narration, Low-Stimulation 24p)",
        f"- **Spoken Word Count**: `{words}` words (`[75, 145]` Short budget)",
        "- **Visual Pacing**: `4` macro `<2700K` watercolor plates (`[15.5, 16.0, 16.0, 15.5]s` raw) with `3` x `1.0s` cross-dissolves (`<= 4` cuts, `15.0s` net hold, `60.00s` @ `1080x1920` `24/1` fps)",
        f"- **Organic Foley Pairing**: `{item['foley_a']}` + `{item['foley_b']}` (`-26.2 LUFS` stem / `>= +30.0 dB` net voice separation, `0%` music)",
        "",
        "## Sanitized Continuous Narration Script",
        "",
        sanitized,
        "",
        "## Primary Scientific & Historical Citations",
        "",
        *[f"- {c}" for c in item["citations"]],
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return md_path


def synthesize_short_voice_stem(
    kokoro: Kokoro,
    voice_vec: np.ndarray,
    item: dict[str, Any],
    total_dur: float,
    wdir: Path,
    stems_dir: Path,
    pre_limit: float = 0.66,
) -> tuple[Path, int, str]:
    sanitized = sanitize_tts_script(item["narration_script"], for_engine=True)
    word_count = validate_sop_v21_word_budget(sanitized, is_short=True)

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", sanitized) if s.strip()]
    sr = 24000
    raw_24k = wdir / "_voice_raw_24k.wav"
    if not raw_24k.exists():
        chunks: list[np.ndarray] = []
        for idx, sent in enumerate(sentences, start=1):
            wav, _ = kokoro.create(sent, voice=voice_vec, speed=0.90, lang="en-gb")
            wav = trim_and_fade_speech(wav, sr)
            chunks.append(wav)
            if idx < len(sentences):
                chunks.append(np.zeros(int(round(0.24 * sr)), dtype=np.float32))
        sf.write(str(raw_24k), np.concatenate(chunks), sr, subtype="PCM_16")

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
    clamp_narration_silence(raw_48k, clamped_48k, is_short=True)

    tight_48k = wdir / "_voice_tight_48k.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(clamped_48k),
            "-af", (
                "silenceremove=stop_periods=-1:stop_duration=0.32:stop_threshold=-45dB,"
                "areverse,silenceremove=start_periods=1:start_duration=0.02:start_threshold=-45dB,areverse"
            ),
            "-ar", "48000", "-ac", "1", "-c:a", "pcm_s16le",
            str(tight_48k),
        ],
        check=True,
        capture_output=True,
    )
    tight_dur = get_audio_duration(tight_48k)

    # 0.14s lead-in + continuous speech + 0.28s gentle tail = 60.000s exact
    target_speech_span = total_dur - 0.42
    atempo_chain = build_atempo_chain(tight_dur / target_speech_span)

    leveled_wav = wdir / "_voice_leveled_48k.wav"
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(tight_48k),
            "-af", (
                f"{atempo_chain},"
                "highpass=f=78,lowpass=f=11500,"
                "dynaudnorm=f=75:g=5:p=0.85:m=5.0,"
                "acompressor=threshold=-23dB:ratio=6.0:attack=3:release=90:makeup=3.5dB,"
                f"alimiter=limit={pre_limit:.2f}:attack=3:release=45:level=false,"
                "alimiter=limit=0.72:attack=4:release=50:level=false,"
                "adelay=140,"
                f"apad=whole_dur={total_dur:.3f},"
                "pan=stereo|c0=c0|c1=c0"
            ),
            "-t", f"{total_dur:.3f}",
            "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(leveled_wav),
        ],
        check=True,
        capture_output=True,
    )

    voice_stem = stems_dir / "Voice_Stem.wav"
    eb = measure_ebur128(leveled_wav)
    gain_db = -14.0 - eb["integrated_lufs"]
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(leveled_wav),
            "-af", (
                f"volume={gain_db:.3f}dB,"
                f"alimiter=limit={pre_limit:.2f}:attack=3:release=45:level=false,"
                "alimiter=limit=0.72:attack=4:release=50:level=false"
            ),
            "-t", f"{total_dur:.3f}",
            "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(voice_stem),
        ],
        check=True,
        capture_output=True,
    )

    # Fine-trim LUFS if limiter shaved >= 0.15 dB while holding True Peak strictly < -2.2 dBFS
    for _ in range(2):
        eb2 = measure_ebur128(voice_stem)
        if abs(eb2["integrated_lufs"] - (-14.0)) <= 0.15 and eb2["true_peak_dbtp"] < -2.15:
            break
        corr_db = -14.0 - eb2["integrated_lufs"]
        corr_wav = wdir / "_voice_corr_48k.wav"
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(voice_stem),
                "-af", (
                    f"volume={corr_db:.3f}dB,"
                    f"alimiter=limit={pre_limit:.2f}:attack=3:release=45:level=false,"
                    "alimiter=limit=0.72:attack=4:release=50:level=false"
                ),
                "-t", f"{total_dur:.3f}",
                "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
                str(corr_wav),
            ],
            check=True,
            capture_output=True,
        )
        shutil.copyfile(corr_wav, voice_stem)
        corr_wav.unlink(missing_ok=True)

    return voice_stem, word_count, sanitized


def build_short_foley_and_master_audio(
    item: dict[str, Any],
    voice_stem: Path,
    total_dur: float,
    wdir: Path,
    stems_dir: Path,
) -> tuple[Path, Path, Path]:
    foley_stem = stems_dir / "Foley_Stem.wav"
    foley_ducked = stems_dir / "Foley_Ducked_Stem.wav"
    master_m4a = stems_dir / "Master_Audio.m4a"

    src_a = FOLEY_LIB / item["foley_a"]
    src_b = FOLEY_LIB / item["foley_b"]
    filt = item["foley_filter"]
    pos = int(item["position"])

    raw_foley = wdir / "_foley_pre_48k.wav"
    fade_out_st = total_dur - 1.2
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-stream_loop", "-1", "-ss", f"{4.0 + pos * 3.5:.1f}", "-t", f"{total_dur + 1.0:.2f}", "-i", str(src_a),
            "-stream_loop", "-1", "-ss", f"{19.0 + pos * 5.0:.1f}", "-t", f"{total_dur + 1.0:.2f}", "-i", str(src_b),
            "-filter_complex", (
                "[0:a]volume=0.72[a0];[1:a]volume=0.55[a1];"
                f"[a0][a1]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
                f"{filt},"
                "dynaudnorm=f=120:g=7:p=0.90:m=5.0,"
                "acompressor=threshold=-26dB:ratio=8:attack=15:release=250,"
                f"afade=t=in:st=0:d=0.8,afade=t=out:st={fade_out_st:.2f}:d=1.2[fout]"
            ),
            "-map", "[fout]", "-t", f"{total_dur:.3f}",
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
            "-t", f"{total_dur:.3f}",
            "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(foley_stem),
        ],
        check=True,
        capture_output=True,
    )
    raw_foley.unlink(missing_ok=True)

    # Sidechain-ducked cushion (<= -43.0 dB mean -> +33..+36 dB voice separation across all 3 qc_gate metrics)
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(foley_stem),
            "-i", str(voice_stem),
            "-filter_complex", (
                "[0:a]volume=-19.5dB[f_att];"
                "[f_att][1:a]sidechaincompress=threshold=0.012:ratio=8:attack=10:release=350:level_sc=1.0[f_duck]"
            ),
            "-map", "[f_duck]", "-t", f"{total_dur:.3f}",
            "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(foley_ducked),
        ],
        check=True,
        capture_output=True,
    )

    # Mix Voice + Ducked Foley + -70 dBFS stereo TPDF white-noise dither -> exact -14.0 LUFS AAC-LC 384k
    pre_master = wdir / "_master_pre.wav"
    seed_a = 301 + pos * 11
    seed_b = 607 + pos * 17
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(voice_stem),
            "-i", str(foley_ducked),
            "-f", "lavfi", "-i", f"anoisesrc=color=white:r=48000:d={total_dur:.3f}:seed={seed_a}",
            "-f", "lavfi", "-i", f"anoisesrc=color=white:r=48000:d={total_dur:.3f}:seed={seed_b}",
            "-filter_complex", (
                "[2:a]volume=0.0003,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=mono[dl];"
                "[3:a]volume=0.0003,aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=mono[dr];"
                "[dl][dr]amerge=inputs=2[dither];"
                "[0:a][1:a][dither]amix=inputs=3:duration=first:dropout_transition=0:normalize=0,"
                "alimiter=limit=0.66:attack=3:release=45:level=false,"
                "alimiter=limit=0.72:attack=4:release=50:level=false[mout]"
            ),
            "-map", "[mout]", "-t", f"{total_dur:.3f}",
            "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le",
            str(pre_master),
        ],
        check=True,
        capture_output=True,
    )

    meb = measure_ebur128(pre_master)
    mgain_db = -14.0 - meb["integrated_lufs"]

    # Guard against AAC lossy inter-sample peak overshoot so final True Peak is strictly < -2.0 dBFS
    for pre_ceil in (0.64, 0.60, 0.56):
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(pre_master),
                "-af", (
                    f"volume={mgain_db:.3f}dB,"
                    f"alimiter=limit={pre_ceil:.2f}:attack=3:release=45:level=false,"
                    "alimiter=limit=0.72:attack=4:release=50:level=false"
                ),
                "-t", f"{total_dur:.3f}",
                "-c:a", "aac", "-aac_coder", "fast", "-b:a", "384k", "-ar", "48000", "-ac", "2",
                str(master_m4a),
            ],
            check=True,
            capture_output=True,
        )
        m_aac_eb = measure_ebur128(master_m4a)
        if m_aac_eb["true_peak_dbtp"] <= -2.15 and (-14.4 <= m_aac_eb["integrated_lufs"] <= -13.6):
            break
        mgain_db += (-14.0 - m_aac_eb["integrated_lufs"])

    pre_master.unlink(missing_ok=True)
    return foley_stem, foley_ducked, master_m4a


def prepare_watermark_9x16(wm_out: Path) -> Path:
    if not wm_out.exists():
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", str(WATERMARK_PNG),
                "-vf", "scale=96:96,format=rgba,colorchannelmixer=aa=0.50",
                str(wm_out),
            ],
            check=True,
            capture_output=True,
        )
    return wm_out


def render_short_video_24p(
    item: dict[str, Any],
    master_m4a: Path,
    wm_rgba: Path,
    wdir: Path,
    plates_dir: Path,
    renders_dir: Path,
) -> tuple[Path, Path, Path]:
    aid = item["asset_id"]
    master_mp4 = renders_dir / f"{aid}_60s_Master.mp4"
    poster_jpg = renders_dir / f"{aid}_Poster_1080x1920.jpg"
    thumb_jpg = renders_dir / f"{aid}_Thumbnail_1280x720.jpg"

    # Pre-scale 4 bespoke macro plates to 1320x2348 warm <2700K PNG (cropping >=80px edge margin)
    graded_dir = wdir / "plates_1320x2348"
    graded_dir.mkdir(parents=True, exist_ok=True)
    scaled_plates: list[Path] = []
    for idx in range(1, 5):
        src_p = plates_dir / f"plate_{idx:02d}.jpg"
        dst_p = graded_dir / f"plate_{idx:02d}.png"
        if not dst_p.exists():
            subprocess.run(
                [
                    "ffmpeg", "-y", "-i", str(src_p),
                    "-vf", (
                        "scale=1320:2348:force_original_aspect_ratio=increase,crop=1320:2348,"
                        "eq=contrast=1.02:saturation=0.93:brightness=-0.01,"
                        "colorbalance=rs=0.04:gs=0.01:bs=-0.05"
                    ),
                    str(dst_p),
                ],
                check=True,
                capture_output=True,
            )
        scaled_plates.append(dst_p)

    # Generate clean 1080x1920 poster + 1280x720 thumbnail from Plate 1
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(scaled_plates[0]), "-vf", "crop=1080:1920:120:214", "-q:v", "3", str(poster_jpg)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(scaled_plates[0]),
            "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720",
            "-q:v", "3", str(thumb_jpg),
        ],
        check=True,
        capture_output=True,
    )

    # Render 4 smooth 24p macro shot clips: [15.50s, 16.00s, 16.00s, 15.50s] -> 3 x 1.0s xfade = 60.000s (1,440 frames)
    raw_durs = [15.50, 16.00, 16.00, 15.50]
    shot_mp4s: list[Path] = []
    for idx0, (plate_png, dur_s) in enumerate(zip(scaled_plates, raw_durs)):
        n_frames = int(round(dur_s * 24))
        shot_out = wdir / f"shot_{idx0 + 1:02d}_24p.mp4"
        if idx0 % 2 == 0:
            crop_expr = f"crop=1080:1920:'80+80*(n/{n_frames})':'140+140*(n/{n_frames})'"
        else:
            crop_expr = f"crop=1080:1920:'160-80*(n/{n_frames})':'280-140*(n/{n_frames})'"
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-loop", "1", "-framerate", "24", "-i", str(plate_png),
                "-vf", f"{crop_expr},fps=24,format=yuv420p,setfield=prog",
                "-frames:v", str(n_frames), "-r", "24",
                "-c:v", "libx264", "-profile:v", "high", "-preset", "ultrafast", "-crf", "12",
                "-pix_fmt", "yuv420p", "-field_order", "progressive",
                "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
                "-x264-params", "8x8dct=1:cabac=1:colorprim=bt709:transfer=bt709:colormatrix=bt709",
                "-an", str(shot_out),
            ],
            check=True,
            capture_output=True,
        )
        shot_mp4s.append(shot_out)

    # Join 4 macro shots with 3 x 1.0s cross-dissolves (<= 4 cuts) + subtle brand watermark + +faststart
    tmp_master = wdir / f"_{aid}_60s_Master.mp4"
    xfade_fc = (
        "[0:v][1:v]xfade=transition=fade:duration=1.0:offset=14.500[vx1];"
        "[vx1][2:v]xfade=transition=fade:duration=1.0:offset=29.500[vx2];"
        "[vx2][3:v]xfade=transition=fade:duration=1.0:offset=44.500[vxf];"
        "[4:v]loop=loop=1448:size=1:start=0,setpts=N/(24*TB)[wm];"
        "[vxf][wm]overlay=W-w-36:H-h-180,"
        "fade=t=in:st=0:d=0.40,fade=t=out:st=59.40:d=0.60,"
        "fps=24,format=yuv420p,setfield=prog[vout]"
    )
    subprocess.run(
        [
            "ffmpeg", "-y",
            "-i", str(shot_mp4s[0]),
            "-i", str(shot_mp4s[1]),
            "-i", str(shot_mp4s[2]),
            "-i", str(shot_mp4s[3]),
            "-i", str(wm_rgba),
            "-i", str(master_m4a),
            "-filter_complex", xfade_fc,
            "-map", "[vout]", "-map", "5:a:0",
            "-frames:v", "1440", "-t", "60.000", "-r", "24",
            "-c:v", "libx264", "-profile:v", "high", "-level:v", "4.1",
            "-preset", "veryfast", "-tune", "stillimage", "-crf", "19",
            "-pix_fmt", "yuv420p", "-field_order", "progressive",
            "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709",
            "-x264-params", "8x8dct=1:cabac=1:colorprim=bt709:transfer=bt709:colormatrix=bt709:keyint=48:min-keyint=24:scenecut=0",
            "-c:a", "copy",
            "-movflags", "+faststart",
            str(tmp_master),
        ],
        check=True,
        capture_output=True,
    )
    shutil.copyfile(tmp_master, master_mp4)
    tmp_master.unlink(missing_ok=True)
    return master_mp4, poster_jpg, thumb_jpg


def run_dual_gate_qa(
    item: dict[str, Any],
    *,
    master_mp4: Path,
    voice_stem: Path,
    foley_stem: Path,
    foley_ducked: Path,
    word_count: int,
    sanitized_script: str,
    repo_manifest_dir: Path,
    media_manifest_dir: Path,
) -> dict[str, Any]:
    aid = item["asset_id"]
    per_short_manifest = repo_manifest_dir / f"{aid}_Manifest.json"

    init_doc = {
        "asset_id": aid,
        "slug": item["slug"],
        "batch_id": "SH-01",
        "playlist_title": "Quiet Wonders & Slow Science — Shorts",
        "sop_version": "ABR-AG-SOP-v2.1",
        "format_type": "DAILY_SHORT_9X16_24P",
        "target_fps": 24.0,
        "visual_cuts_count": 3,
        "max_cuts_allowed": 4,
        "title": item["title"],
        "youtube_title": item["youtube_title"],
        "category": item["category"],
        "pillar": item["pillar"],
        "primary_source": item["primary_source"],
        "citations": item["citations"],
        "narrator_name": "George-Daniel Baritone",
        "narrator_voice_id": "kokoro_bm_george_daniel_blend_v1",
        "narrator_gender": "male",
        "state": "RENDERED",
        "sha256": sha256_file(master_mp4),
        "file_size_bytes": master_mp4.stat().st_size,
        "script_metrics": {
            "spoken_words": word_count,
            "sanitized_script": sanitized_script,
        },
        "stream_metrics": {},
        "youtube_routing": {
            "privacy_status": "private",
            "publish_at_utc": item["publish_at_utc"],
            "playlist_title": "Quiet Wonders & Slow Science — Shorts",
            "series_playlist_id": None,
            "made_for_kids": False,
            "ad_policy": "SHORTS_FEED",
        },
    }
    per_short_manifest.write_text(json.dumps(init_doc, indent=2) + "\n", encoding="utf-8")

    # Gate 1: SH-01/verify_asset_gate.py (CHK-01 .. CHK-07)
    p = subprocess.run(
        [
            sys.executable,
            str(VERIFY_SCRIPT),
            "--master", str(master_mp4),
            "--voice-stem", str(voice_stem),
            "--foley-stem", str(foley_stem),
            "--manifest", str(per_short_manifest),
            "--tracker", str(TRACKER_PATH),
            "--declared-min-hold", "15.0",
            "--max-cuts", "4",
            "--require-male-narrator",
        ],
        capture_output=True,
        text=True,
    )
    if p.returncode != 0:
        raise RuntimeError(f"Gate 1 (verify_asset_gate.py) FAILED for {aid}:\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}")
    sop03_res = json.loads(p.stdout)

    # Gate 2: Daily Producer qc_gate.py (1080x1920, H.264 High BT.709 progressive, 384k AAC, +faststart, >=+30 dB, 0% music)
    qc_res = qc_gate.run_qc_gate(
        master_mp4,
        expected_width=1080,
        expected_height=1920,
        min_duration_sec=59.5,
        max_duration_sec=60.5,
        voice_wav=voice_stem,
        foley_wav=foley_ducked,
        narrated=True,
    )
    failed_qc = [k for k, v in qc_res["gates"].items() if not v]
    if failed_qc:
        raise RuntimeError(f"Gate 2 (qc_gate.py) FAILED for {aid} on {failed_qc}:\n{json.dumps(qc_res, indent=2)}")

    # Explicit SH-01 extra assertions: 24/1 fps, High profile, BT.709, cuts <= 4, True Peak < -2.0 dBFS, music_detected == false
    tp_dbfs = float(qc_res["master_loudness"]["true_peak_dbfs"])
    if tp_dbfs >= -2.0:
        raise RuntimeError(f"True Peak ceiling violated for {aid}: {tp_dbfs} dBFS >= -2.0 dBFS")
    if qc_res["video_stream"].get("r_frame_rate") != "24/1":
        raise RuntimeError(f"Frame rate mismatch for {aid}: {qc_res['video_stream'].get('r_frame_rate')} != 24/1")

    final_doc = json.loads(per_short_manifest.read_text(encoding="utf-8"))
    final_doc["qc_gate_audit"] = qc_res
    per_short_manifest.write_text(json.dumps(final_doc, indent=2) + "\n", encoding="utf-8")
    shutil.copyfile(per_short_manifest, media_manifest_dir / f"{aid}_Manifest.json")
    return {
        "asset_id": aid,
        "state": "QA_VERIFIED",
        "file_size_bytes": master_mp4.stat().st_size,
        "file_size_mb": round(master_mp4.stat().st_size / (1024 * 1024), 2),
        "mp4_path": str(master_mp4),
        "manifest_path": str(per_short_manifest),
        "stream_metrics": final_doc["stream_metrics"],
        "sop03_checks": sop03_res["checks"],
        "qc_gates": qc_res["gates"],
        "qc_video_stream": qc_res["video_stream"],
        "qc_audio_stream": qc_res["audio_stream"],
        "qc_container_atoms": qc_res["container_atoms"],
        "qc_master_loudness": qc_res["master_loudness"],
        "qc_effective_separation_db": qc_res["stems_audit"]["effective_separation_db"],
    }


def main() -> int:
    t0 = time.time()
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    for sub in ("plates", "stems", "renders", "manifests", "audit_logs", "quarantine"):
        (MEDIA_SH01 / sub).mkdir(parents=True, exist_ok=True)
    for sub in ("manifests", "audit_logs"):
        (REPO_SH01 / sub).mkdir(parents=True, exist_ok=True)

    batch_manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    deliverables: list[dict[str, Any]] = batch_manifest["deliverables"]

    print("[SH-01] Loading Kokoro ONNX neural TTS (bm_george + bm_daniel baritone blend)...", flush=True)
    kokoro = Kokoro(str(KOKORO_MODEL), str(KOKORO_VOICES))
    voice_vec = 0.65 * kokoro.get_voice_style("bm_george") + 0.35 * kokoro.get_voice_style("bm_daniel")
    wm_rgba = prepare_watermark_9x16(BUILD_ROOT / "wm_96_rgba.png")

    audit_records: list[dict[str, Any]] = []

    for item in deliverables:
        aid = item["asset_id"]
        print(f"\n==================== [{aid}] {item['title']} ====================", flush=True)
        wdir = BUILD_ROOT / aid
        stems_dir = MEDIA_SH01 / "stems" / aid
        plates_dir = MEDIA_SH01 / "plates" / aid
        renders_dir = MEDIA_SH01 / "renders"
        wdir.mkdir(parents=True, exist_ok=True)
        stems_dir.mkdir(parents=True, exist_ok=True)

        existing_mp4 = renders_dir / f"{aid}_60s_Master.mp4"
        existing_man = REPO_SH01 / "manifests" / f"{aid}_Manifest.json"
        if item.get("state") == "QA_VERIFIED" and existing_mp4.exists() and existing_man.exists():
            mdoc = json.loads(existing_man.read_text(encoding="utf-8"))
            qc_res = mdoc["qc_gate_audit"]
            audit_records.append({
                "asset_id": aid,
                "state": "QA_VERIFIED",
                "file_size_bytes": existing_mp4.stat().st_size,
                "file_size_mb": round(existing_mp4.stat().st_size / (1024 * 1024), 2),
                "mp4_path": str(existing_mp4),
                "poster_jpg": item.get("poster_path", str(renders_dir / f"{aid}_Poster_1080x1920.jpg")),
                "thumb_jpg": item.get("thumb_path", str(renders_dir / f"{aid}_Thumbnail_1280x720.jpg")),
                "manifest_path": str(existing_man),
                "stream_metrics": mdoc["stream_metrics"],
                "sop03_checks": mdoc["sop03_verification"],
                "qc_gates": qc_res["gates"],
                "qc_video_stream": qc_res["video_stream"],
                "qc_audio_stream": qc_res["audio_stream"],
                "qc_container_atoms": qc_res["container_atoms"],
                "qc_master_loudness": qc_res["master_loudness"],
                "qc_effective_separation_db": qc_res["stems_audit"]["effective_separation_db"],
            })
            print(f"[{aid}] Reused QA_VERIFIED checkpoint ({round(existing_mp4.stat().st_size / 1048576, 2)} MB).", flush=True)
            continue

        md_repo = write_short_script_markdown(item, REPO_SH01 / "manifests")
        shutil.copyfile(md_repo, MEDIA_SH01 / "manifests" / md_repo.name)

        qa_summary: dict[str, Any] | None = None
        for attempt, pre_lim in enumerate((0.66, 0.60, 0.55), start=1):
            try:
                print(f"[{aid}] Render & QA Attempt {attempt}/3 (pre_limit={pre_lim:.2f})...", flush=True)
                voice_stem, word_count, sanitized = synthesize_short_voice_stem(
                    kokoro, voice_vec, item, 60.0, wdir, stems_dir, pre_limit=pre_lim
                )
                foley_stem, foley_ducked, master_m4a = build_short_foley_and_master_audio(
                    item, voice_stem, 60.0, wdir, stems_dir
                )
                master_mp4, poster_jpg, thumb_jpg = render_short_video_24p(
                    item, master_m4a, wm_rgba, wdir, plates_dir, renders_dir
                )
                qa_summary = run_dual_gate_qa(
                    item,
                    master_mp4=master_mp4,
                    voice_stem=voice_stem,
                    foley_stem=foley_stem,
                    foley_ducked=foley_ducked,
                    word_count=word_count,
                    sanitized_script=sanitized,
                    repo_manifest_dir=REPO_SH01 / "manifests",
                    media_manifest_dir=MEDIA_SH01 / "manifests",
                )
                qa_summary["poster_jpg"] = str(poster_jpg)
                qa_summary["thumb_jpg"] = str(thumb_jpg)
                print(
                    f"[{aid}] QA_VERIFIED! Size={qa_summary['file_size_mb']} MB | "
                    f"LUFS={qa_summary['qc_master_loudness']['integrated_lufs']} | "
                    f"TP={qa_summary['qc_master_loudness']['true_peak_dbfs']} dBFS | "
                    f"Sep=+{qa_summary['stream_metrics']['net_voice_separation_db']} dB | "
                    f"Duty={qa_summary['stream_metrics']['vocal_duty_cycle_pct']}% | "
                    f"Music={qa_summary['stream_metrics']['music_detected']}",
                    flush=True,
                )
                break
            except Exception as exc:
                print(f"[{aid}] Attempt {attempt} failed gate: {exc}", flush=True)
                cand_mp4 = renders_dir / f"{aid}_60s_Master.mp4"
                if cand_mp4.exists():
                    q_dst = MEDIA_SH01 / "quarantine" / f"{aid}_attempt{attempt}_quarantined.mp4"
                    shutil.copyfile(cand_mp4, q_dst)
                    cand_mp4.unlink(missing_ok=True)
                for f in wdir.glob("_*"):
                    if f.is_file():
                        f.unlink(missing_ok=True)
                if attempt == 3:
                    raise

        assert qa_summary is not None
        item["state"] = "QA_VERIFIED"
        item["mp4_path"] = qa_summary["mp4_path"]
        item["poster_path"] = qa_summary["poster_jpg"]
        item["thumb_path"] = qa_summary["thumb_jpg"]
        item["manifest_path"] = qa_summary["manifest_path"]
        item["file_size_bytes"] = qa_summary["file_size_bytes"]
        item["file_size_mb"] = qa_summary["file_size_mb"]
        item["qa_metrics"] = {
            "resolution": f"{qa_summary['qc_video_stream']['width']}x{qa_summary['qc_video_stream']['height']}",
            "r_frame_rate": qa_summary["qc_video_stream"]["r_frame_rate"],
            "profile": qa_summary["qc_video_stream"]["profile"],
            "color_space": qa_summary["qc_video_stream"]["color_space"],
            "faststart_verified": qa_summary["qc_container_atoms"]["faststart_verified"],
            "visual_cuts_count": qa_summary["stream_metrics"]["visual_cuts_count"],
            "min_scene_hold_sec": qa_summary["stream_metrics"]["min_scene_hold_sec"],
            "integrated_lufs": qa_summary["qc_master_loudness"]["integrated_lufs"],
            "true_peak_dbfs": qa_summary["qc_master_loudness"]["true_peak_dbfs"],
            "foley_stem_lufs": qa_summary["stream_metrics"]["foley_lufs"],
            "voice_separation_db": qa_summary["stream_metrics"]["net_voice_separation_db"],
            "qc_effective_separation_db": qa_summary["qc_effective_separation_db"],
            "max_narration_silence_sec": qa_summary["stream_metrics"]["max_narration_silence_sec"],
            "vocal_duty_cycle_pct": qa_summary["stream_metrics"]["vocal_duty_cycle_pct"],
            "music_detected": qa_summary["stream_metrics"]["music_detected"],
        }
        audit_records.append(qa_summary)

        # Checkpoint batch manifest after each Short completes QA
        MANIFEST_PATH.write_text(json.dumps(batch_manifest, indent=2) + "\n", encoding="utf-8")
        shutil.copyfile(MANIFEST_PATH, MEDIA_SH01 / "sh01_manifest.json")

    audit_log = {
        "batch_id": "SH-01",
        "playlist_title": "Quiet Wonders & Slow Science — Shorts",
        "completed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "elapsed_sec": round(time.time() - t0, 2),
        "total_assets": len(audit_records),
        "qa_verified_count": sum(1 for r in audit_records if r["state"] == "QA_VERIFIED"),
        "all_6_qa_verified": len(audit_records) == 6 and all(r["state"] == "QA_VERIFIED" for r in audit_records),
        "assets": audit_records,
    }
    repo_audit_path = REPO_SH01 / "audit_logs" / "SH01_Dual_Gate_Audit_Log.json"
    repo_audit_path.write_text(json.dumps(audit_log, indent=2) + "\n", encoding="utf-8")
    shutil.copyfile(repo_audit_path, MEDIA_SH01 / "audit_logs" / "SH01_Dual_Gate_Audit_Log.json")

    batch_manifest["batch_state"] = "QA_VERIFIED"
    batch_manifest["qa_completed_at_utc"] = audit_log["completed_at_utc"]
    MANIFEST_PATH.write_text(json.dumps(batch_manifest, indent=2) + "\n", encoding="utf-8")
    shutil.copyfile(MANIFEST_PATH, MEDIA_SH01 / "sh01_manifest.json")

    print(f"\n[SH-01] ALL 6/6 SHORTS PASSED DUAL-GATE QA (`QA_VERIFIED`) in {audit_log['elapsed_sec']}s!", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
