import os
import re
import glob
import shutil
import argparse
import pandas as pd
from tqdm import tqdm


TASK_NAME_MAP = {
    'VOWELS': 'SUSTAINED-VOWELS',
    'MODULATED_VOWELS': 'MODULATED_SUSTAINED-VOWELS',
    'DDK_ANALYSIS': 'DDK_ANALYSIS',
    'SENTENCES': 'SENTENCES',
    'SENTENCES2': 'SENTENCES',
    'READ_TEXT': 'READ_TEXT',
    'MONOLOGUE': 'MONOLOGUE',
    'WORDS': 'WORDS',
}

FLAT_FILENAME_TASK_MAP = {
    'KA': 'DDK_ANALYSIS',
    'PA': 'DDK_ANALYSIS',
    'TA': 'DDK_ANALYSIS',
    '-TA': 'DDK_ANALYSIS',
    'PATAKA': 'DDK_ANALYSIS',
    'PETAKA': 'DDK_ANALYSIS',
    'PAKATA': 'DDK_ANALYSIS',
    'A': 'MODULATED_SUSTAINED-VOWELS',
    'E': 'MODULATED_SUSTAINED-VOWELS',
    'I': 'MODULATED_SUSTAINED-VOWELS',
    'O': 'MODULATED_SUSTAINED-VOWELS',
    'U': 'MODULATED_SUSTAINED-VOWELS',
}


def normalize_task_name(task_name):
    normalized = task_name.upper().replace('-', '_').replace(' ', '_')
    return TASK_NAME_MAP.get(normalized, normalized)


def infer_task_from_sample_suffix(sample_suffix):
    token = sample_suffix.lstrip('_').upper()

    if re.fullmatch(r'[AEIOU]\d+', token):
        return 'SUSTAINED-VOWELS'
    if token in FLAT_FILENAME_TASK_MAP:
        return FLAT_FILENAME_TASK_MAP[token]
    if 'MONOLOGO' in token:
        return 'MONOLOGUE'

    return None


def get_task_id(wav_path, data_dir, sample_suffix):
    rel_parts = os.path.relpath(wav_path, data_dir).split(os.path.sep)
    if len(rel_parts) > 1:
        return normalize_task_name(rel_parts[0])
    return infer_task_from_sample_suffix(sample_suffix)


def load_metadata(metadata_path):
    metadata_path = os.path.expanduser(metadata_path)
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")

    suffix = os.path.splitext(metadata_path)[1].lower()
    if suffix in {'.xlsx', '.xls'}:
        metadata = pd.read_excel(metadata_path, sheet_name=0)
    elif suffix == '.csv':
        metadata = pd.read_csv(metadata_path)
    else:
        raise ValueError(
            f"Unsupported metadata format: {metadata_path}. Use .xlsx, .xls, or .csv"
        )

    return metadata

if __name__ == "__main__":

    # -- command line arguments
    parser = argparse.ArgumentParser(description='Restructure the original GITA audio samples', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--data-dir', required=True, type=str)
    parser.add_argument('--metadata-path', default=None, type=str, help='Path to PC-GITA metadata file (.xlsx/.xls/.csv). Defaults to Copia_de_PCGITA_metadata.xlsx inside --data-dir')
    parser.add_argument('--new-data-dir', default='./data/gita/audios/', type=str)
    args = parser.parse_args()

    os.makedirs(args.new_data_dir, exist_ok=True)

    if args.metadata_path is None:
        args.metadata_path = os.path.join(args.data_dir, 'Copia_de_PCGITA_metadata.xlsx')

    # -- loading and processing metadata
    # -- original column IDs: RECODING ORIGINAL NAME,UPDRS,UPDRS-speech,H/Y,SEX,AGE,time after diagnosis
    metadata = load_metadata(args.metadata_path)
    metadata['label'] = metadata['RECODING ORIGINAL NAME'].map(lambda x: 1 if 'AVPEPUDEAC' not in x else 0)
    metadata['group_id'] = metadata['label'].map(lambda x: 'PD' if x else 'HC')

    # -- processing audio samples
    ignored_samples = 0
    unresolved_task_samples = 0
    wavs = glob.glob(os.path.join(args.data_dir, '**/*.wav'), recursive=True)
    for wav_path in tqdm(wavs):
        if 'los_que_' in wav_path or 'las_que_' in wav_path:
            ignored_samples += 1
            continue

        sample_id = wav_path.split(os.path.sep)[-1].split('.')[0]
        subject_id = re.findall(r"(AVPEPUDEA(?:C)?\d{4})", sample_id)[0]
        if subject_id in metadata['RECODING ORIGINAL NAME'].tolist():
            sample_suffix = sample_id.split(subject_id)[-1]
            sample_id = f'{subject_id}_{sample_suffix}'.replace('_PRECUPADO', '_PREOCUPADO').replace('__', '_').upper()
            task_id = get_task_id(wav_path, args.data_dir, sample_suffix)
            if task_id is None:
                unresolved_task_samples += 1
                print(f'[WARN] Could not infer task for {wav_path}. If you want full audios_fortrain naming, use the task-structured PC-GITA directory (e.g. pc_gita_16khz) instead of the flat audios directory.')
                continue

            # -- retriveing metadata per sample
            sample = metadata[metadata['RECODING ORIGINAL NAME'] == subject_id]
            group_id = sample['group_id'].values[0].upper()

            new_wav_path = os.path.join(args.new_data_dir, f'{group_id}_{task_id}_{sample_id}.wav').replace('_PRECUPADO', '_PREOCUPADO').replace('__', '_')
            shutil.copy(wav_path, new_wav_path)

    print(f'{ignored_samples} samples were ignored because of some of the subjects were not further considered in the study.')
    print(f'{unresolved_task_samples} samples were skipped because the task could not be inferred reliably from a flat filename.')
