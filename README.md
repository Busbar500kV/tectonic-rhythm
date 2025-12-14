# tectonic-rhythm
Feel the mood of seismic events by යසස් පොන්වීර


# 🌍🎶 Tectonic Rhythm

**Tectonic Rhythm** is a generative audiovisual project that transforms historical global seismic activity into sound and motion.

Earthquakes are treated not as isolated disasters, but as a continuous planetary rhythm — a slow, uneven pulse produced by tectonic plates over time.

The project renders:
- a **dark-mode world map** with continental outlines,
- **time-compressed seismic events** as glowing points,
- and a **synthesized audio track** whose amplitude follows earthquake magnitude.

The result is a short film where the Earth “plays itself”.

---

## ▶️ Final Output

**Final video (MP4):**  
https://github.com/Busbar500kV/tectonic-rhythm/blob/main/out/final.mp4

> If GitHub does not preview the video (especially on mobile), use **“View raw”** or download the file to play locally.

---

## 🧠 Concept

Earthquakes are usually discussed as discrete events.  
Here, they are treated as a **continuous signal**:

- **Space** → geography  
- **Time** → musical progression  
- **Magnitude** → loudness and visual intensity  

The project avoids narration, legends, or explanations.  
Instead, it invites the viewer to *feel* global seismic activity as a pattern.

---

## 🌐 Data Source

Seismic data is fetched from the **USGS Earthquake Catalog (GeoJSON API)**.

Typical fields used:
- `time` — UTC timestamp of the event  
- `latitude`, `longitude` — epicenter location  
- `magnitude` — moment magnitude (Mw)  

Events are sorted by time and **linearly compressed** into a fixed-duration video.

No filtering is applied beyond basic validity checks.  
The density and clustering visible in the video reflect real seismic behavior.

---

## 🗺️ Visual Mapping

### World Map
- Continental outlines from **Natural Earth (110m resolution)**
- Cached locally after first download
- Rendered as a single muted outline on a black background (dark mode)

### Earthquake Events

Each earthquake is rendered as a glowing point:

| Seismic Property | Visual Mapping |
|-----------------|----------------|
| Latitude / Longitude | Screen position |
| Magnitude | Point size |
| Event age | Fade-out (alpha decay) |
| Time | Month–Year label |

The timestamp shown is **Month + Year**, not frame time, to preserve narrative continuity without implying real-time playback.

---

## 🔊 Sound Mapping

The soundtrack is generated programmatically.

### Core principles
- Earthquake **magnitude → sound amplitude**
- Event timing follows the **same compressed timeline** as the video
- Silence is meaningful; not every moment contains sound

### Mapping summary

| Seismic Parameter | Audio Parameter |
|------------------|-----------------|
| Magnitude (Mw) | Volume (nonlinear scaling) |
| Event density | Rhythmic texture |
| Time | Audio timeline position |

The current implementation uses a **minimal mono audio signal**, intentionally avoiding melody so that rhythm and intensity dominate.

---

## ⚙️ Execution Model

Designed for unattended, long-running execution on a remote machine:

- Runs inside a Python virtual environment
- Uses `screen` for SSH-safe detached execution
- Automatically:
  - installs dependencies
  - renders frames
  - synthesizes audio
  - merges video and audio using `ffmpeg`
  - commits and pushes the final output

### One-command execution

```bash
bash scripts/run_detached_busbar.sh