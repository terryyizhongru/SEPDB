# Benchmark for Speech-based Early-stage Parkinson's Disease Detection

This repository contains the official benchmark splits and evaluation protocols for the paper:  
**"A Benchmark for Early-stage Parkinson's Disease Detection from Speech"**

---

## Latest Updates
- **Benchmark splits:** Speaker-independent, standardized splits are available in `benchmark_splits/`.
- **Evaluation scripts:** Work in progress; code will be released/cleaned up.

---

## Benchmark splits: directory layout and naming

The `benchmark_splits/` folder contains multiple split groups. Each group is a 5-fold cross-validation setup with:

- `fold_1/` ... `fold_5/`
- One test set per fold (early-stage PD benchmark)
- A `train_and_val/` subfolder per fold containing the training and validation lists

At a high level:

- `folds_csv/`
	- Speaker-level lists with metadata for each subject.
	- Typical columns include: `ID`, `Group/Diagnosis`, demographics, clinical scores (e.g., HY stage, UPDRS), and dataset source.
- `folds_tsv*/`
	- Utterance/audio-level lists used for model training.
	- Each row corresponds to one audio file and includes: subject `ID`, `AUDIOFILE` (wav path), and `DIAGNOSIS` (label).

### What you find inside each fold

Each `fold_x/` directory follows the same naming pattern (extension is `.csv` under `folds_csv/`, and `.tsv` under `folds_tsv*/`):

- Test set:
	- `test_early6PD6HC.*` (early-stage PD benchmark)
	- `test_all6PD6HC.*` (all-stage PD test set)


- Train/validation split (inside the subfolder):
	- `train_and_val/`
		- `train.*` (AllPD setting in the paper: the full set of PD speakers across all stages from the benchmark datasets)
		- validation lists such as `val_early6PD6HC.*` and `val_all6PD6HC.*`

### Split groups (tasks)

- `folds_tsv_all/`
	- Combined list covering all tasks/audios.

Single-task training lists used in the benchmark paper experiments:

- `folds_tsv_SENTENCES/`
- `folds_tsv_DDK_ANALYSIS_PATAKA/`
- `folds_tsv_SUSTAINED-VOWELS_onlyA123/`

For these three single-task split groups, the `train_and_val/` folder also includes:

- `train_allPDsubset.tsv` (AllPD-subset introduced in the paper: a distribution-matched subset of AllPD)
- `train_earlybalance.tsv` (EarlyPD setting: the full set of EarlyPD speakers from the benchmark datasets)

## Preprocessing

Use the helper scripts in `preprocess_scripts/` to normalize raw NeuroVoz/PC-GITA audios before running any benchmark experiments. Provide `$DATASET_DIR` as the parent containing the source downloads and target root for the reorganized files.

1. Rename and copy NeuroVoz audio files:

```
python3 preprocess_scripts/rename_audios_neurovoz.py $DATASET_DIR/neurovoz_v3/audios $DATASET_DIR/NeuroVoz_PCGITA/neurovoz_data/audios
```

2. Restructure and rename PC-GITA audio files:

```
python3 preprocess_scripts/rename_restruct_gita.py --data-dir $DATASET_DIR/PC-GITA/ --new-data-dir $DATASET_DIR/NeuroVoz_PCGITA/pcgita_data/audios
```

---

