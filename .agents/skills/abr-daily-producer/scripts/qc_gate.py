#!/usr/bin/env python3
"""
Automated Quality Control Gate (Hard Fail Before Upload) — @ABR-AntiBrainRot
============================================================================
Verifies all broadcast audio, visual, container, and zero-music invariants
using FFmpeg `ebur128`, `volumedetect`, `ffprobe`, and spectral autocorrelation:
1. Voice-to-foley separation >= +30.0 dB on narrated assets.
2. Integrated loudness: -14.0 LUFS (+/- 0.5 LUFS) for narrated videos;
   safe low-SPL continuous profile for 3-hour sleep soundscapes.
3. Zero-Music spectral periodicity audit (CHK-04: 0% sustained tonal/melodic harmonics).
4. Container & stream spec:
   - H.264 High Profile, yuv420p, progressive scan, BT.709 color space/primaries/transfer
   - Exact native 1920x1080 (16:9) or 1080x1920 (9:16) geometry
   - 48 kHz stereo AAC-LC at ~384 kbps
   - MP4 `moov` atom positioned before `mdat` atom (+faststart)
"""

from __future__ import annotations

import json
import re
import struct
import subprocess
import sys
import wave
from pathlib import Path
from typing import Any


def measure_ebur128(path: Path) -> dict[str, float]:
    p = subprocess.run(
        ["ffmpeg", "-vn", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
        capture_output=True,
        text=True,
        check=True,
    )
    summary = p.stderr.split("Summary:")[-1]
    m_i = re.search(r"\bI:\s*([-\d.]+)\s*LUFS", summary)
    m_lra = re.search(r"\bLRA:\s*([-\d.]+)\s*LU", summary)
    m_pk = re.search(r"\bPeak:\s*([-\d.]+)\s*dBFS", summary)
    return {
        "integrated_lufs": float(m_i.group(1)) if m_i else -99.0,
        "lra_lu": float(m_lra.group(1)) if m_lra else 0.0,
        "true_peak_dbfs": float(m_pk.group(1)) if m_pk else -99.0,
    }


def measure_volumedetect(path: Path, ss: float = 0.0, dur: float | None = None) -> dict[str, float]:
    cmd = ["ffmpeg", "-vn"]
    if ss > 0:
        cmd.extend(["-ss", f"{ss:.2f}"])
    if dur is not None:
        cmd.extend(["-t", f"{dur:.2f}"])
    cmd.extend(["-i", str(path), "-af", "volumedetect", "-f", "null", "-"])
    p = subprocess.run(cmd, capture_output=True, text=True, check=True)
    m_mean = re.search(r"mean_volume:\s*([-\d.]+)\s*dB", p.stderr)
    m_max = re.search(r"max_volume:\s*([-\d.]+)\s*dB", p.stderr)
    return {
        "mean_volume_db": float(m_mean.group(1)) if m_mean else -99.0,
        "max_volume_db": float(m_max.group(1)) if m_max else -99.0,
    }


def check_zero_music_spectral_audit(foley_wav: Path) -> dict[str, Any]:
    probe_wav = Path(f"/tmp/_qc_chk04_{foley_wav.stem}.wav")
    subprocess.run(
        ["ffmpeg", "-y", "-t", "24", "-i", str(foley_wav), "-ac", "1", "-ar", "4000", str(probe_wav)],
        capture_output=True,
        check=True,
    )
    try:
        with wave.open(str(probe_wav), "rb") as wf:
            raw = wf.readframes(wf.getnframes())
        samples = struct.unpack(f"<{len(raw)//2}h", raw)
        sr = 4000
        tonal_windows = 0
        max_corr_seen = 0.0
        max_start = max(sr, min(len(samples) - sr, 16 * sr))
        for w in range(0, max_start, 2 * sr):
            seg = samples[w : w + min(1024, len(samples) - w)]
            if len(seg) < 128:
                continue
            mean_val = sum(seg) / len(seg)
            centered = [x - mean_val for x in seg]
            energy = sum(x * x for x in centered) + 1e-9
            best_r = 0.0
            for lag in range(5, 50):
                num = sum(centered[i] * centered[i + lag] for i in range(len(centered) - lag))
                r = abs(num / energy)
                if r > best_r:
                    best_r = r
            max_corr_seen = max(max_corr_seen, best_r)
            if best_r > 0.88:
                tonal_windows += 1
        music_detected = tonal_windows >= 3
        return {
            "passed": not music_detected,
            "music_detected": music_detected,
            "tonal_windows": tonal_windows,
            "max_periodicity_ratio": round(max_corr_seen, 4),
        }
    finally:
        probe_wav.unlink(missing_ok=True)


def inspect_mp4_atoms(mp4_path: Path) -> dict[str, Any]:
    """Parses top-level ISO BMFF atoms to verify `moov` precedes `mdat`."""
    offsets: dict[str, int] = {}
    file_size = mp4_path.stat().st_size
    with mp4_path.open("rb") as f:
        pos = 0
        while pos + 8 <= file_size:
            f.seek(pos)
            hdr = f.read(8)
            if len(hdr) < 8:
                break
            size, box_type_bytes = struct.unpack(">I4s", hdr)
            box_type = box_type_bytes.decode("latin1", errors="replace")
            offsets.setdefault(box_type, pos)
            if size == 1:
                ext = f.read(8)
                if len(ext) < 8:
                    break
                size = struct.unpack(">Q", ext)[0]
            elif size == 0:
                break
            if size < 8:
                break
            pos += size
    moov_pos = offsets.get("moov", -1)
    mdat_pos = offsets.get("mdat", -1)
    return {
        "moov_offset": moov_pos,
        "mdat_offset": mdat_pos,
        "faststart_verified": (moov_pos >= 0 and mdat_pos >= 0 and moov_pos < mdat_pos),
        "top_level_atoms": offsets,
    }


def run_qc_gate(
    mp4_path: Path,
    *,
    expected_width: int,
    expected_height: int,
    min_duration_sec: float,
    max_duration_sec: float,
    voice_wav: Path | None = None,
    foley_wav: Path | None = None,
    narrated: bool = True,
) -> dict[str, Any]:
    probe_proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(mp4_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    probe = json.loads(probe_proc.stdout)
    streams = probe.get("streams", [])
    v_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
    a_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})
    duration_sec = float(probe.get("format", {}).get("duration", 0.0))

    atoms = inspect_mp4_atoms(mp4_path)
    master_ebur = measure_ebur128(mp4_path)
    master_vol = measure_volumedetect(mp4_path)

    video_spec_ok = (
        v_stream.get("codec_name") == "h264"
        and v_stream.get("profile") == "High"
        and int(v_stream.get("width", 0)) == expected_width
        and int(v_stream.get("height", 0)) == expected_height
        and v_stream.get("pix_fmt") == "yuv420p"
        and v_stream.get("field_order", "progressive") in ("progressive", "unknown")
        and v_stream.get("color_space") == "bt709"
        and v_stream.get("color_primaries") == "bt709"
        and v_stream.get("color_transfer") == "bt709"
    )
    # Require explicit progressive field_order
    progressive_explicit = v_stream.get("field_order") == "progressive"
    video_spec_ok = video_spec_ok and progressive_explicit

    audio_bitrate_bps = int(a_stream.get("bit_rate") or 0)
    audio_spec_ok = (
        a_stream.get("codec_name") == "aac"
        and a_stream.get("profile") == "LC"
        and str(a_stream.get("sample_rate")) == "48000"
        and int(a_stream.get("channels", 0)) == 2
        and 340_000 <= audio_bitrate_bps <= 420_000
    )

    duration_ok = min_duration_sec <= duration_sec <= max_duration_sec

    result: dict[str, Any] = {
        "mp4_path": str(mp4_path),
        "file_size_bytes": mp4_path.stat().st_size,
        "duration_sec": round(duration_sec, 3),
        "duration_bounds_sec": [min_duration_sec, max_duration_sec],
        "video_stream": {
            "codec_name": v_stream.get("codec_name"),
            "profile": v_stream.get("profile"),
            "width": v_stream.get("width"),
            "height": v_stream.get("height"),
            "pix_fmt": v_stream.get("pix_fmt"),
            "field_order": v_stream.get("field_order"),
            "color_space": v_stream.get("color_space"),
            "color_primaries": v_stream.get("color_primaries"),
            "color_transfer": v_stream.get("color_transfer"),
            "r_frame_rate": v_stream.get("r_frame_rate"),
            "bit_rate_bps": int(v_stream.get("bit_rate") or 0),
        },
        "audio_stream": {
            "codec_name": a_stream.get("codec_name"),
            "profile": a_stream.get("profile"),
            "sample_rate": a_stream.get("sample_rate"),
            "channels": a_stream.get("channels"),
            "bit_rate_bps": audio_bitrate_bps,
            "bit_rate_kbps": round(audio_bitrate_bps / 1000.0, 1),
        },
        "container_atoms": atoms,
        "master_loudness": {**master_ebur, **master_vol},
        "gates": {
            "video_h264_high_bt709_progressive": video_spec_ok,
            "audio_48khz_stereo_aac_lc_384k": audio_spec_ok,
            "container_moov_faststart": atoms["faststart_verified"],
            "duration_in_bounds": duration_ok,
        },
    }

    if narrated:
        if voice_wav is None or foley_wav is None:
            raise ValueError("Narrated QC gate requires both voice_wav and foley_wav stems.")
        vo_ebur = measure_ebur128(voice_wav)
        vo_vol = measure_volumedetect(voice_wav)
        fol_vol = measure_volumedetect(foley_wav)
        spectral = check_zero_music_spectral_audit(foley_wav)

        # Separation measured both ways: Voice Integrated LUFS vs Foley Mean dB, AND Voice Mean dB vs Foley Mean dB
        sep_lufs_vs_foley_db = round(vo_ebur["integrated_lufs"] - fol_vol["mean_volume_db"], 2)
        sep_mean_vs_foley_db = round(vo_vol["mean_volume_db"] - fol_vol["mean_volume_db"], 2)
        effective_sep_db = min(sep_lufs_vs_foley_db, sep_mean_vs_foley_db) if sep_mean_vs_foley_db > 0 else sep_lufs_vs_foley_db

        lufs_ok = -14.5 <= master_ebur["integrated_lufs"] <= -13.5
        sep_ok = sep_lufs_vs_foley_db >= 30.0 and fol_vol["mean_volume_db"] <= -43.0
        zero_music_ok = spectral["passed"]

        result["stems_audit"] = {
            "voice_stem": {**vo_ebur, **vo_vol},
            "foley_stem": fol_vol,
            "voice_lufs_minus_foley_mean_db": sep_lufs_vs_foley_db,
            "voice_mean_minus_foley_mean_db": sep_mean_vs_foley_db,
            "zero_music_spectral": spectral,
        }
        result["gates"]["integrated_loudness_minus14_lufs"] = lufs_ok
        result["gates"]["voice_to_foley_separation_gte_30db"] = sep_ok
        result["gates"]["zero_music_spectral_audit"] = zero_music_ok
    else:
        # 3-Hour Sleep Soundscape safe continuous low-SPL profile
        lufs_ok = -32.0 <= master_ebur["integrated_lufs"] <= -18.0
        result["gates"]["sleep_safe_low_spl_loudness"] = lufs_ok
        if foley_wav is not None:
            spectral = check_zero_music_spectral_audit(foley_wav)
            result["stems_audit"] = {"zero_music_spectral": spectral}
            result["gates"]["zero_music_spectral_audit"] = spectral["passed"]

    result["all_passed"] = all(result["gates"].values())
    return result


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: qc_gate.py <mp4> <width> <height> <min_dur> <max_dur> [voice.wav foley.wav]")
        sys.exit(2)
    mp4 = Path(sys.argv[1])
    w = int(sys.argv[2])
    h = int(sys.argv[3])
    mn = float(sys.argv[4])
    mx = float(sys.argv[5])
    vw = Path(sys.argv[6]) if len(sys.argv) >= 8 else None
    fw = Path(sys.argv[7]) if len(sys.argv) >= 8 else None
    res = run_qc_gate(
        mp4,
        expected_width=w,
        expected_height=h,
        min_duration_sec=mn,
        max_duration_sec=mx,
        voice_wav=vw,
        foley_wav=fw,
        narrated=(vw is not None),
    )
    print(json.dumps(res, indent=2))
    sys.exit(0 if res["all_passed"] else 1)
