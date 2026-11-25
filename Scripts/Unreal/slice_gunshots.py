# Cuts single gunshots out of a multi-shot field recording (R3 combat audio). Imported by setup_combat.py.
# Source: The Free Firearm Sound Library (Ben Jaszczak, Brian Nelson, Kevin Heras, Matthew Nanney), CC0,
# https://opengameart.org/content/the-free-firearm-sound-library . The 96 kHz / 24-bit files are not kept in the repo.
# Output: <prefix>_01.wav ... 48 kHz, 16-bit, stereo, peak -1 dBFS, each starting 2 ms before the shot.
# Run (any Python with numpy): python slice_gunshots.py <in.wav> <out prefix> [max seconds]
import struct
import sys
import wave

import numpy as np


def load(path):
    with wave.open(path, "rb") as w:
        frames, channels, width, rate = w.getnframes(), w.getnchannels(), w.getsampwidth(), w.getframerate()
        raw = np.frombuffer(w.readframes(frames), np.uint8)
    if width == 3:
        b = raw.reshape(-1, 3).astype(np.int32)
        v = b[:, 0] | (b[:, 1] << 8) | (b[:, 2] << 16)
        v = np.where(v >= 1 << 23, v - (1 << 24), v) / float(1 << 23)
    elif width == 2:
        v = np.frombuffer(raw.tobytes(), "<i2") / 32768.0
    else:
        raise ValueError(f"unsupported sample width {width}")
    return v.reshape(-1, channels).astype(np.float32), rate


def find_shots(x, rate, min_gap=1.0):
    """Sample index of every shot that has at least min_gap seconds of silence-ish tail before the next one."""
    hop = rate // 200  # 5 ms
    env = np.abs(x).max(1)
    env = env[: len(env) // hop * hop].reshape(-1, hop).max(1)
    threshold = 0.25 * env.max()
    starts, last_loud = [], -10 ** 9
    for i, e in enumerate(env):
        if e >= threshold:
            if i - last_loud > 60:  # 300 ms of quiet before it: a new shot
                starts.append(i * hop)
            last_loud = i
    ends = starts[1:] + [len(x)]
    return [(s, e) for s, e in zip(starts, ends) if (e - s) / rate >= min_gap]


def halve_rate(x):
    """96 kHz -> 48 kHz: windowed-sinc low-pass at 0.45 of the new rate, then drop every other sample."""
    taps = 95
    n = np.arange(taps) - (taps - 1) / 2
    kernel = 0.45 * np.sinc(0.45 * n) * np.hamming(taps)
    kernel /= kernel.sum()
    return np.stack([np.convolve(x[:, c], kernel, "same") for c in range(x.shape[1])], 1)[::2]


def main(src, prefix, max_seconds=2.0):
    x, rate = load(src)
    count = 0
    for start, end in find_shots(x, rate):
        # exact onset: first sample over 5 % of the shot's peak, minus 2 ms of pre-roll
        head = np.abs(x[start - rate // 50: start + rate // 50]).max(1)
        onset = start - rate // 50 + int(np.argmax(head >= 0.05 * head.max())) - rate // 500
        clip = x[max(onset, 0): min(end - rate // 10, onset + int(max_seconds * rate))].copy()
        if rate == 96000:
            clip, out_rate = halve_rate(clip), 48000
        else:
            out_rate = rate
        fade = out_rate // 20  # 50 ms out
        clip[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)[:, None]
        clip *= 10 ** (-1 / 20) / np.abs(clip).max()

        count += 1
        out = f"{prefix}_{count:02d}.wav"
        with wave.open(out, "wb") as w:
            w.setnchannels(clip.shape[1])
            w.setsampwidth(2)
            w.setframerate(out_rate)
            w.writeframes((np.clip(clip, -1.0, 1.0) * 32767.0).astype("<i2").tobytes())
        print(f"{out}: {len(clip) / out_rate:.2f} s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 2.0)
