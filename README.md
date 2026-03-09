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

- Test set (early-stage PD benchmark):
	- `test_early6PD6HC.*`
	- (Some folds also include other test lists, e.g. `test_all6PD6HC.*`.)

- Train+validation combined list (fold-level):
	- `train_and_val.*`
	- This is the full list for that fold before splitting into train/validation.

- Train/validation split (inside the subfolder):
	- `train_and_val/`
		- `train.*`
		- validation lists such as `val_early6PD6HC.*` and `val_all6PD6HC.*`

### Split groups (tasks)

- `folds_tsv_all/`
	- Combined list covering all tasks/audios.

Single-task training lists used in the benchmark paper experiments:

- `folds_tsv_SENTENCES/`
- `folds_tsv_DDK_ANALYSIS_PATAKA/`
- `folds_tsv_SUSTAINED-VOWELS/`

Additional variants:

- `folds_tsv_DDK_ANALYSIS/` (broader DDK sets)
- `folds_tsv_SUSTAINED-VOWELS_onlyA123/` (restricted vowel subset)

---

