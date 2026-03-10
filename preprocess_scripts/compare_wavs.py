#!/usr/bin/env python3

import argparse
import array
import hashlib
import sys
import wave
from pathlib import Path


def read_wav(path):
    with wave.open(str(path), "rb") as wav_file:
        params = wav_file.getparams()
        frames = wav_file.readframes(wav_file.getnframes())
    return params, frames


def summarize(path, params, frames):
    return {
        "path": str(path),
        "channels": params.nchannels,
        "sample_width": params.sampwidth,
        "sample_rate": params.framerate,
        "num_frames": params.nframes,
        "duration_sec": params.nframes / params.framerate if params.framerate else 0.0,
        "compression_type": params.comptype,
        "compression_name": params.compname,
        "pcm_sha256": hashlib.sha256(frames).hexdigest(),
        "pcm_num_bytes": len(frames),
    }


def print_summary(label, summary):
    print(f"{label}: {summary['path']}")
    print(f"  channels: {summary['channels']}")
    print(f"  sample_width: {summary['sample_width']}")
    print(f"  sample_rate: {summary['sample_rate']}")
    print(f"  num_frames: {summary['num_frames']}")
    print(f"  duration_sec: {summary['duration_sec']:.6f}")
    print(f"  compression_type: {summary['compression_type']}")
    print(f"  compression_name: {summary['compression_name']}")
    print(f"  pcm_num_bytes: {summary['pcm_num_bytes']}")
    print(f"  pcm_sha256: {summary['pcm_sha256']}")


def decode_samples(frames, sample_width, channels):
    if channels != 1:
        raise ValueError("Sample-level comparison currently supports mono WAV files only")

    if sample_width == 1:
        samples = array.array("B")
        samples.frombytes(frames)
        return [sample - 128 for sample in samples]

    if sample_width == 2:
        samples = array.array("h")
        samples.frombytes(frames)
        return list(samples)

    if sample_width == 4:
        samples = array.array("i")
        samples.frombytes(frames)
        return list(samples)

    raise ValueError(f"Unsupported sample width for sample-level comparison: {sample_width}")


def analyze_sample_differences(params_a, frames_a, params_b, frames_b):
    if params_a.nchannels != params_b.nchannels:
        return None, "channel-count mismatch"
    if params_a.sampwidth != params_b.sampwidth:
        return None, "sample-width mismatch"
    if params_a.nframes != params_b.nframes:
        return None, "frame-count mismatch"

    try:
        samples_a = decode_samples(frames_a, params_a.sampwidth, params_a.nchannels)
        samples_b = decode_samples(frames_b, params_b.sampwidth, params_b.nchannels)
    except ValueError as exc:
        return None, str(exc)

    diffs = [abs(sample_a - sample_b) for sample_a, sample_b in zip(samples_a, samples_b)]
    if not diffs:
        return {
            "num_samples": 0,
            "num_diff_samples": 0,
            "diff_ratio": 0.0,
            "max_abs_diff": 0,
            "mean_abs_diff": 0.0,
            "nonzero_diff_counts": {},
            "likely_dither_only": False,
        }, None

    nonzero_diff_counts = {}
    num_diff_samples = 0
    max_abs_diff = 0
    diff_sum = 0

    for diff in diffs:
        diff_sum += diff
        if diff > max_abs_diff:
            max_abs_diff = diff
        if diff != 0:
            num_diff_samples += 1
            nonzero_diff_counts[diff] = nonzero_diff_counts.get(diff, 0) + 1

    num_samples = len(diffs)
    diff_ratio = num_diff_samples / num_samples
    mean_abs_diff = diff_sum / num_samples

    likely_dither_only = (
        num_diff_samples > 0
        and params_a.sampwidth == 2
        and max_abs_diff <= 2
    )

    return {
        "num_samples": num_samples,
        "num_diff_samples": num_diff_samples,
        "diff_ratio": diff_ratio,
        "max_abs_diff": max_abs_diff,
        "mean_abs_diff": mean_abs_diff,
        "nonzero_diff_counts": nonzero_diff_counts,
        "likely_dither_only": likely_dither_only,
    }, None


def main():
    parser = argparse.ArgumentParser(
        description="Compare two WAV files at the audio PCM level"
    )
    parser.add_argument("wav_a", help="first WAV file")
    parser.add_argument("wav_b", help="second WAV file")
    args = parser.parse_args()

    path_a = Path(args.wav_a)
    path_b = Path(args.wav_b)

    missing = [str(path) for path in (path_a, path_b) if not path.exists()]
    if missing:
        for path in missing:
            print(f"Missing file: {path}", file=sys.stderr)
        return 2

    params_a, frames_a = read_wav(path_a)
    params_b, frames_b = read_wav(path_b)

    summary_a = summarize(path_a, params_a, frames_a)
    summary_b = summarize(path_b, params_b, frames_b)

    print_summary("WAV_A", summary_a)
    print()
    print_summary("WAV_B", summary_b)
    print()

    same_params = params_a == params_b
    same_pcm = frames_a == frames_b
    same_length = len(frames_a) == len(frames_b)
    diff_stats, diff_error = analyze_sample_differences(params_a, frames_a, params_b, frames_b)

    print("COMPARE:")
    print(f"  same_params: {same_params}")
    print(f"  same_pcm_bytes: {same_pcm}")
    print(f"  same_pcm_length: {same_length}")

    if diff_stats is not None:
        print("  sample_diff_stats:")
        print(f"    num_samples: {diff_stats['num_samples']}")
        print(f"    num_diff_samples: {diff_stats['num_diff_samples']}")
        print(f"    diff_ratio: {diff_stats['diff_ratio']:.12f}")
        print(f"    max_abs_diff: {diff_stats['max_abs_diff']}")
        print(f"    mean_abs_diff: {diff_stats['mean_abs_diff']:.12f}")

        if diff_stats["nonzero_diff_counts"]:
            print("    nonzero_diff_counts:")
            for diff_value in sorted(diff_stats["nonzero_diff_counts"]):
                print(f"      {diff_value}: {diff_stats['nonzero_diff_counts'][diff_value]}")

        print(f"  likely_dither_only: {diff_stats['likely_dither_only']}")
    else:
        print(f"  sample_diff_stats: unavailable ({diff_error})")

    if same_pcm:
        print("RESULT: audio-identical")
        return 0

    if diff_stats is not None and diff_stats["likely_dither_only"]:
        print("RESULT: audio-different-but-likely-dither-only")
        return 0

    print("RESULT: audio-different")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())