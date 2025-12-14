from __future__ import annotations
import numpy as np
from dataclasses import dataclass
from scipy.io import wavfile

@dataclass
class SonifyConfig:
    duration_s: float = 300.0
    sr: int = 48000
    mag_min: float = 5.5
    mag_max: float = 9.5
    base_freq_hz: float = 110.0  # A2
    freq_span_octaves: float = 4.0
    event_len_s: float = 0.35

def _waveform(kind: str, phase: np.ndarray) -> np.ndarray:
    # phase is radians
    if kind == "sine":
        return np.sin(phase)
    if kind == "square":
        return np.sign(np.sin(phase))
    if kind == "saw":
        return 2.0 * (phase / (2*np.pi) - np.floor(0.5 + phase / (2*np.pi)))
    if kind == "tri":
        return 2.0 * np.abs(2.0 * (phase / (2*np.pi) - np.floor(0.5 + phase / (2*np.pi)))) - 1.0
    return np.sin(phase)

def render_soundtrack(events, cfg: SonifyConfig, plate_to_wave: dict[str, str]) -> np.ndarray:
    """
    events: DataFrame-like with columns: time (datetime64), mag (float), plate (str)
    """
    t0 = events["time"].min()
    t1 = events["time"].max()
    span = (t1 - t0).total_seconds()
    if span <= 0:
        raise ValueError("Need events spanning time.")

    n = int(cfg.duration_s * cfg.sr)
    audio = np.zeros(n, dtype=np.float32)

    def norm_mag(m):
        x = (m - cfg.mag_min) / (cfg.mag_max - cfg.mag_min)
        return float(np.clip(x, 0.0, 1.0))

    for _, e in events.iterrows():
        tm = (e["time"] - t0).total_seconds()
        te = tm / span * cfg.duration_s
        start = int(te * cfg.sr)
        if start < 0 or start >= n:
            continue

        m = float(e["mag"])
        x = norm_mag(m)
        amp = (x ** 2.5)  # perceptual curve

        # pitch rises with magnitude (or swap to depth if you want)
        freq = cfg.base_freq_hz * (2.0 ** (x * cfg.freq_span_octaves))

        length = int(cfg.event_len_s * cfg.sr)
        end = min(n, start + length)

        tt = np.arange(end - start) / cfg.sr
        env = np.exp(-tt * 8.0)  # fast decay
        phase = 2*np.pi*freq*tt

        wave = _waveform(plate_to_wave.get(str(e.get("plate", "Unknown")), "sine"), phase)
        audio[start:end] += (amp * env * wave).astype(np.float32)

    # soft limiter
    mx = float(np.max(np.abs(audio)) + 1e-9)
    audio = audio / mx * 0.95
    return audio

def write_wav(path: str, audio: np.ndarray, sr: int):
    wavfile.write(path, sr, (audio * 32767).astype(np.int16))