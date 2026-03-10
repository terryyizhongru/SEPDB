import os
import glob
import argparse
from tqdm import tqdm
from scipy.io import wavfile
import noisereduce as nr


def resample_only(wav_files, output_dir, target_sr=16000):
    """Resample every WAV to `target_sr` and convert to 16-bit mono."""
    for wav_file in tqdm(wav_files, desc="Resample"):
        output_path = os.path.join(output_dir, os.path.basename(wav_file))
        os.system(f'sox "{wav_file}" -b 16 -c 1 -r {target_sr} "{output_path}"')


def normalize_only(wav_files, output_dir, target_sr=16000, norm_db=-3):
    """Normalize loudness, resample, and emit 16-bit mono audio."""
    for wav_file in tqdm(wav_files, desc="Normalize"):
        output_path = os.path.join(output_dir, os.path.basename(wav_file))
        os.system(f'sox --norm={norm_db} "{wav_file}" -b 16 -c 1 -r {target_sr} "{output_path}"')


def resample_and_norm(wav_files, output_dir, target_sr=16000, norm_db=-3):
    """Resample to `target_sr`, convert to 16-bit mono, and normalize to `norm_db`."""
    for wav_file in tqdm(wav_files, desc="Resample+Norm"):
        output_path = os.path.join(output_dir, os.path.basename(wav_file))
        os.system(f'sox --norm={norm_db} "{wav_file}" -b 16 -c 1 -r {target_sr} "{output_path}"')


def denoise_file(input_path, output_path, noise_path=None):
    """Denoise a single WAV file.

    - If `noise_path` is provided, use that sample as the noise reference.
    - Otherwise, let `noisereduce` profile the noise automatically.
    """
    # Load the file to denoise
    rate, data = wavfile.read(input_path)

    if noise_path is not None:
        # Load the noise sample and ensure the rates match
        noise_rate, noise_data = wavfile.read(noise_path)
        if noise_rate != rate:
            raise ValueError(
                f"Noise sample rate ({noise_rate}) does not match audio rate ({rate}): {noise_path} vs {input_path}"
            )

        reduced_noise = nr.reduce_noise(
            y=data,
            y_noise=noise_data,
            sr=rate,
            stationary=True,
        )
    else:
        # Without a provided sample, estimate noise automatically
        reduced_noise = nr.reduce_noise(
            y=data,
            sr=rate,
            stationary=True,
        )

    # Write the denoised file
    wavfile.write(output_path, rate, reduced_noise)


def denoise_batch(wav_files, output_dir, noise_path=None):
    """Denoise a batch of WAV files."""
    for wav_file in tqdm(wav_files, desc="Denoise"):
        output_path = os.path.join(output_dir, os.path.basename(wav_file))
        denoise_file(wav_file, output_path, noise_path=noise_path)

def for_neurovoz_pipeline(wav_files, output_dir, target_sr=16000, norm_db=-3.0, noise_path=None):
    """NeuroVoz-specific three-step pipeline:

    1. Resample every WAV to `target_sr`.
    2. Denoise then normalize files containing `_MONOLOGUE_0`.
    3. Leave the rest at the resampled version (only normalized).

    Assumes input WAVs are raw and writes the processed tracks to `output_dir`.
    """

    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Resample every WAV to target_sr and write to output
    for wav_file in tqdm(wav_files, desc="NeuroVoz Step1: Resample all"):
        base = os.path.basename(wav_file)
        resampled_path = os.path.join(output_dir, base)
        os.system(f'sox "{wav_file}" -b 16 -c 1 -r {target_sr} "{resampled_path}"')

    # Step 2: Normalize everything at 16 kHz; `_MONOLOGUE_0` files are denoised first
    resampled_files = glob.glob(os.path.join(output_dir, "*.wav"))

    # First handle `_MONOLOGUE_0`: denoise + normalize
    mono_files = [
        f for f in resampled_files
        if "_MONOLOGUE_0" in os.path.basename(f)
    ]

    for mono_file in tqdm(mono_files, desc="NeuroVoz Step2a: Denoise+Norm for _MONOLOGUE_0"):
        base = os.path.basename(mono_file)
        tmp_denoised = os.path.join(output_dir, f"tmp_denoise_{base}")

        # 2.1 Denoise (supports manual noise sample or auto estimation)
        denoise_file(mono_file, tmp_denoised, noise_path=noise_path)

        # 2.2 Normalize the denoised file (keep 16 kHz, 16 bit, mono)
        final_path = os.path.join(output_dir, base)
        os.system(f'sox --norm={norm_db} "{tmp_denoised}" -b 16 -c 1 -r {target_sr} "{final_path}"')

        # Remove the temporary file
        if os.path.exists(tmp_denoised):
            os.remove(tmp_denoised)

    # Now process non `_MONOLOGUE_0`: normalize the 16 kHz WAVs
    non_mono_files = [
        f for f in resampled_files
        if "_MONOLOGUE_0" not in os.path.basename(f)
    ]

    for wav_file in tqdm(non_mono_files, desc="NeuroVoz Step2b: Norm for non-MONOLOGUE_0"):
        base = os.path.basename(wav_file)
        tmp_norm = os.path.join(output_dir, f"tmp_norm_{base}")
        final_path = os.path.join(output_dir, base)

        # Write to a temporary path to avoid read/write conflicts with sox
        os.system(f'sox --norm={norm_db} "{wav_file}" -b 16 -c 1 -r {target_sr} "{tmp_norm}"')

        # Replace the original file with the normalized version
        os.replace(tmp_norm, final_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Resample, normalize, or denoise audio waveforms",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--wav-dir", type=str, required=True, help="input WAV directory")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="output directory (defaults to <wav-dir>/audios_fortrain)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["resample", "norm", "resample_norm", "denoise", "for_neurovoz"],
        default="resample_norm",
        help="Choose resample/norm/resample_norm/denoise or the NeuroVoz pipeline (defaults to resample_norm)",
    )
    parser.add_argument("--target-sr", type=int, default=16000, help="target sample rate")
    parser.add_argument("--norm-db", type=float, default=-3.0, help="normalization target dB (used for norm or resample_norm)")
    parser.add_argument("--noise", type=str, default=None, help="noise sample WAV path (optional for denoise mode)")

    args = parser.parse_args()

    target_output = args.output_dir
    if not target_output:
        wav_dir = os.path.abspath(args.wav_dir)
        target_output = os.path.join(os.path.dirname(wav_dir), "audios_fortrain")
    os.makedirs(target_output, exist_ok=True)
    wav_files = glob.glob(os.path.join(args.wav_dir, "*.wav"))

    if args.mode == "resample":
        resample_only(wav_files, target_output, target_sr=args.target_sr)
    elif args.mode == "norm":
        normalize_only(wav_files, target_output, target_sr=args.target_sr, norm_db=args.norm_db)
    elif args.mode == "resample_norm":
        resample_and_norm(wav_files, target_output, target_sr=args.target_sr, norm_db=args.norm_db)
    elif args.mode == "denoise":
        denoise_batch(wav_files, target_output, noise_path=args.noise)
    elif args.mode == "for_neurovoz":
        for_neurovoz_pipeline(
            wav_files,
            target_output,
            target_sr=args.target_sr,
            norm_db=args.norm_db,
            noise_path=args.noise,
        )

