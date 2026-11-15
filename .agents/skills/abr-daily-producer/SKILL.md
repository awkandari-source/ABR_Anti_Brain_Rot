---
name: abr-daily-producer
description: Autonomous Daily Production Orchestrator skill for @ABR-AntiBrainRot. Enforces Two-Phase Inspect-Then-Execute workflow, 7-API health & ElevenLabs 8,000-char safeguard, daily 16:9 Long-Form + 9:16 Short cadence, Two-Layer Zero-Music Audio (+30 dB separation, -14.0 LUFS), H.264 High BT.709 48kHz/384k AAC QC gate, Google Drive archiving, YouTube publishAt scheduling, sweeper registration, and GitHub index sync.
---
# ABR Anti-Brain Rot (`@ABR-AntiBrainRot`) — Daily Autonomous Production Skill (`abr-daily-producer`)

## 1. Two-Phase Inspect-Then-Execute Governance
Never synthesize paid media or upload files until **Phase 1 (Read-Only Pre-Flight Audit)** succeeds:
1. **7-Service Health Check:** Import `LinkedAPIHub` from `/shared/user/.gemini/raw_video_studio/linked_api_hub.py` and run `hub.health_check_all()` across YouTube Data v3 & Analytics v2, ElevenLabs v1, Higgsfield Motion v1, Google Gemini v1beta (dual-key failover), Windsor.ai, Google Drive (`gdrive`), and GitHub (`gh`).
2. **ElevenLabs Credit Safeguard (`8,000` Character Floor):**
   - Query `hub.elevenlabs.get_subscription()["characters_remaining"]`.
   - If remaining credits are `< 8,000` characters for a narrated slot, route **100% of that episode's narration** to `GeminiLinkedAPI` (`gemini-2.5-flash-preview-tts`, `24 kHz` PCM) so voice timbre never switches mid-episode, and emit a credit top-up notice in the Phase 1 Manifest.
3. **Dynamic Index & Schedule Gap Resolution (`T+7` Rolling Buffer):**
   - Parse `/home/antigravity/ABR_Anti_Brain_Rot/ABR_Anti_Brain_Rot_Index.md` + live `YouTubeLinkedAPI` scheduled uploads.
   - Dynamically resolve the Google Drive root archive folder (`1mlAlS_xpEn11gUGyKi_zuQiDZ0Co9Ay9`) and the 4 official playlists (`PLEyZbMU0SV08`, `PLSpo6LDB5RsE`, `PLO3jEEgHm_Iw`, `PLfO4Y6xIR8iU`).
   - Select the earliest unscheduled calendar date for (a) `16:9` Long-Form and (b) `9:16` Shorts with **0% topic or artifact overlap**.
4. **Retention & Attribution Signal Pull:** Query 7-day YouTube performance and Windsor.ai social insights to select high-retention curiosity and parent-science hooks.
5. **Emit Phase 1 Manifest:** Document API health, quota, `publishAt` UTC (`15:00:00Z` for Shorts & Science/History long-form; `16:30:00Z` for Kids Bedtime Stories & 3-Hour Sleep Soundscapes), prompts, citations, and playlist/funnel comment routing.

---

## 2. Daily Content Cadence & Pillar Routing

### 2.1 Daily `9:16` Short (`38s–45s`, `5` Scenes, Native `1080x1920`)
- Rotate across **Pillar 3** (Ancient Engineering, Lost Civilizations, Empire Wealth), **Pillar 2** (Pediatric Neuroscience Hooks & Parent Reset Tips), and **Pillar 1** (Calm Story Teasers).
- Scene 5 MUST use `/shared/user/.gemini/raw_video_studio/channel_branding/ABR_Shorts_Endcard_1080x1920.jpg`.
- Route top pinned funnel comment to the matching long-form video/playlist and parent reset guide in `/home/antigravity/ABR_Anti_Brain_Rot/`.

### 2.2 Daily `16:9` Long-Form Video (Native `1920x1080`)
| Day of Week | Pillar & Format | Runtime & Structure | Publish Time (UTC) |
| :--- | :--- | :--- | :--- |
| **Monday** | Pillar 1: Calm Kids Bedtime Story | `10:00` (`30` scenes x `20s`) | `16:30:00Z` |
| **Tuesday** | Pillar 1B: Non-Looped Dark-Screen Sleep Soundscape | `03:00:00` (`0` TTS credits) | `16:30:00Z` |
| **Wednesday** | Pillar 2: Pediatric Brain Science Documentary | `10:00` (peer-reviewed citations + `60s` zero-music mid-roll sponsor break) | `15:00:00Z` |
| **Thursday** | Pillar 1B: Non-Looped Nature Sleep Ambience | `03:00:00` (`0` TTS credits) | `16:30:00Z` |
| **Friday** | Pillar 2B: Calm Ancient History Documentary | `08:00` (primary historical citations + `60s` zero-music mid-roll sponsor break) | `15:00:00Z` |
| **Saturday** | Pillar 1: Woodland Kids Bedtime Story | `05:00` (`15` scenes x `20s`) | `16:30:00Z` |
| **Sunday** | Pillar 1B: Non-Looped Night Soundscape | `03:00:00` (`0` TTS credits) | `16:30:00Z` |

---

## 3. Visual, Pediatric Sleep & Two-Layer Zero-Music Guardrails

1. **Visual Guardrails:**
   - Render soft matte watercolor/gouache storybook or calm historical plates via `GeminiLinkedAPI` (`gemini-2.5-flash-image`), strictly zero burned-in text and zero letterboxing.
   - Narrated long-form holds: **`12s` to `20s` minimum per scene** (`0` rapid 2-second cuts).
   - Animate subtle organic motion via `HiggsfieldLinkedAPI` (`seedance_pro -> seedance_lite -> dop-turbo` fallback) + gentle deterministic pan/zoom continuity.
   - Overlay `/shared/user/.gemini/raw_video_studio/channel_branding/ABR_Video_Watermark_150x150.png` on all `16:9` long-form videos.
2. **Pediatric Sleep Guardrails (Pillar 1B 3-Hour Episodes):**
   - Non-looped acoustic progression (`0.1 Hz` natural surf/wind entrainment or exponential rain/drip decay).
   - Sub-2000K warm amber luminance with `< 1%` true-black floor.
   - Mandatory **`50 dBA at 2-meter speaker distance`** pediatric hearing safety protocol in YouTube description.
3. **Two-Layer Zero-Music Audio Law (NON-NEGOTIABLE):**
   - **Layer 1 (Voice):** Centered-mono human-cadence narration (`100–115 WPM`, `1.5–3.0s` pauses) mastered to **`-14.0 LUFS`** (`+/- 0.5 LUFS`).
   - **Layer 2 (Foley):** Pure organic environmental foley via ElevenLabs `/v1/sound-generation`, low-passed (`highpass=70Hz, lowpass=920Hz, acompressor`) and 5:1 sidechain-ducked to **`-43.5 dB`** (never run single-pass `loudnorm` on foley).
   - **Strict Prohibition:** `0%` musical instruments, melodies, ambient synth pads, drones, chimes, bells, or rhythmic beats.

---

## 4. Automated FFmpeg QC Gate (Hard Fail Before Upload)
Every master MP4 MUST pass automated `ffprobe` + `ffmpeg -af ebur128` verification before Drive upload or YouTube scheduling:
- **Voice-to-Foley Separation:** `>= +30.0 dB` on all narrated assets (if lower, re-run sidechain ducker logic from `fix_week2_voice_over_foley.py` / `fix_week2_shorts_audio.py`).
- **Integrated Loudness:** `-14.0 LUFS` (`+/- 0.5 LUFS`, i.e. `[-14.5, -13.5] LUFS`) for narrated videos; safe low-SPL continuous profile for 3-hour sleep soundscapes.
- **Container & Stream Spec:**
  - Codec: `h264` (`High` profile, progressive scan `field_order=progressive`, `yuv420p`)
  - Color Space: `bt709` (`color_primaries=bt709`, `color_trc=bt709`, `colorspace=bt709`)
  - Faststart: `moov` atom at front of MP4 (`-movflags +faststart`)
  - Audio Stream: `48,000 Hz` (`48 kHz`) stereo (`2` channels) `AAC-LC` at `384 kbps`
  - Geometry: Exact `1920x1080` (`16:9`) or `1080x1920` (`9:16`)

---

## 5. Cloud Archive, Native Scheduling & Sweeper Registration
1. Upload final MP4, custom `16:9` thumbnail (`1280x720`), WAV stems (`Voice` & `Foley`), and metadata JSON to a new episode folder under Google Drive root `1mlAlS_xpEn11gUGyKi_zuQiDZ0Co9Ay9`.
2. Schedule both MP4s on YouTube (`privacyStatus="private"`, `publishAt="<ISO-8601 UTC>"`), set custom `16:9` thumbnail, and write `youtube_publish_metadata.json` so `/shared/user/.gemini/raw_video_studio/autonomous_scheduled_sweeper.py` automatically assigns playlists and posts top funnel comments once public (never include `drive.google.com` links in YouTube text).
3. Append new rows to `/home/antigravity/ABR_Anti_Brain_Rot/ABR_Anti_Brain_Rot_Index.md`, sync to Google Drive & GitHub, and emit the Release & QC Verification Artifact.
