#!/usr/bin/env python3
"""
Script to rename NeuroVoz audio files according to specific rules:
1. Files with _A1_ _A2_ _A3_ (A can be E I O U) -> replace with _SUSTAINED-VOWELS_A1_ etc.
2. Files with _PATAKA_ -> replace with _DDK_ANALYSIS_PATAKA_
3. Files with _FREE_ -> replace with _MONOLOGUE_FREE_
4. All other files: PD_ HC_ -> replace with PD_SENTENCES_ HC_SENTENCES_
5. Reorder filename format from Group_Task_Detail_ID to Group_Task_ID_Detail
"""

import argparse
import re
import shutil
from pathlib import Path

def has_task_in_filename(filename):
    """
    Check if filename already contains a task identifier
    """
    task_patterns = [
        'SUSTAINED-VOWELS',
        'DDK_ANALYSIS', 
        'MONOLOGUE',
        'SENTENCES'
    ]
    return any(task in filename for task in task_patterns)

def add_task_to_filename(filename):
    """
    Add task identifier to filename based on original rules
    """
    new_name = filename
    
    # Rule 1: Vowel patterns (A1, A2, A3, E1, E2, E3, I1, I2, I3, O1, O2, O3, U1, U2, U3)
    vowel_pattern = r'_([AEIOU])(\d+)_'
    if re.search(vowel_pattern, filename):
        new_name = re.sub(vowel_pattern, r'_SUSTAINED-VOWELS_\1\2_', new_name)
    
    # Rule 2: PATAKA pattern
    elif '_PATAKA_' in filename:
        new_name = filename.replace('_PATAKA_', '_DDK_ANALYSIS_PATAKA_')
    
    # Rule 3: FREE pattern
    elif '_FREE_' in filename:
        new_name = filename.replace('_FREE_', '_MONOLOGUE_FREE_')
    
    # Rule 4: All other files (sentences)
    else:
        if filename.startswith('PD_'):
            new_name = filename.replace('PD_', 'PD_SENTENCES_', 1)
        elif filename.startswith('HC_'):
            new_name = filename.replace('HC_', 'HC_SENTENCES_', 1)
    
    return new_name

def reorder_filename_parts(filename):
    """
    Reorder filename from Group_Task_Detail_ID to Group_Task_ID_Detail
    Expected format: Group_Task_Detail_ID.wav
    Target format: Group_Task_ID_Detail.wav
    
    Handle multi-word tasks like DDK_ANALYSIS, SUSTAINED-VOWELS correctly
    """
    # Remove .wav extension
    name_without_ext = filename.replace('.wav', '')
    
    # Split by underscore
    parts = name_without_ext.split('_')
    
    if len(parts) < 3:
        return filename  # Not enough parts to reorder
    
    # Check if the last part is a 4-digit ID
    if parts[-1].isdigit() and len(parts[-1]) == 4:
        id_part = parts[-1]  # 4-digit ID
        
        # Handle different task types
        group = parts[0]  # PD or HC
        
        # Identify task type and its components
        if len(parts) >= 4:
            if parts[1] == 'DDK' and parts[2] == 'ANALYSIS':
                # DDK_ANALYSIS case
                task = 'DDK_ANALYSIS'
                detail_parts = parts[3:-1]  # Everything after DDK_ANALYSIS and before ID
            elif parts[1] == 'SUSTAINED-VOWELS':
                # SUSTAINED-VOWELS case  
                task = 'SUSTAINED-VOWELS'
                detail_parts = parts[2:-1]  # Everything after SUSTAINED-VOWELS and before ID
            else:
                # Single word task (MONOLOGUE, SENTENCES)
                task = parts[1]
                detail_parts = parts[2:-1]  # Everything between task and ID
                
            # Reorder to: Group_Task_ID_Detail
            if detail_parts:
                reordered_parts = [group, task, id_part] + detail_parts
            else:
                reordered_parts = [group, task, id_part]
            
            return '_'.join(reordered_parts) + '.wav'
    
    return filename  # No 4-digit ID found, return original

def rename_neurovoz_files(audio_dir, new_data_dir=None):
    """
    Rename audio files in the given directory according to the specified rules.
    """
    audio_path = Path(audio_dir)
    
    if not audio_path.exists():
        print(f"Error: Directory {audio_dir} does not exist!")
        return
    
    # Get all wav files
    wav_files = list(audio_path.glob("*.wav"))
    print(f"Found {len(wav_files)} WAV files to process")
    
    renamed_count = 0

    in_place = False
    if new_data_dir:
        target_path = Path(new_data_dir)
        target_path.mkdir(parents=True, exist_ok=True)
        print(f"Writing renamed files to: {target_path}")
    else:
        target_path = audio_path
        in_place = True
    
    for wav_file in wav_files:
        old_name = wav_file.name
        new_name = old_name
        
        # Step 1: Add task if not present
        if not has_task_in_filename(old_name):
            new_name = add_task_to_filename(old_name)
            print(f"  Added task: {old_name} -> {new_name}")
        
        # Step 2: Reorder filename parts
        reordered_name = reorder_filename_parts(new_name)
        if reordered_name != new_name:
            print(f"  Reordered: {new_name} -> {reordered_name}")
            new_name = reordered_name
        
        # Only rename if name changed
        if new_name != old_name:
            old_path = wav_file
            new_path = target_path / new_name
            
            # Check if target file already exists
            if new_path.exists():
                print(f"Warning: Target file {new_name} already exists! Skipping {old_name}")
                continue
            
            try:
                if in_place:
                    old_path.rename(new_path)
                else:
                    shutil.copy2(old_path, new_path)
                print(f"✅ Final: {old_name} -> {new_name}")
                renamed_count += 1
            except Exception as e:
                print(f"❌ Error renaming {old_name}: {e}")
    
    print(f"\nRenaming completed! {renamed_count} files renamed.")

def preview_changes(audio_dir):
    """
    Preview what changes would be made without actually renaming files.
    """
    audio_path = Path(audio_dir)
    
    if not audio_path.exists():
        print(f"Error: Directory {audio_dir} does not exist!")
        return
    
    # Get all wav files
    wav_files = list(audio_path.glob("*.wav"))
    print(f"Preview of changes for {len(wav_files)} WAV files:\n")
    
    change_count = 0
    
    for i, wav_file in enumerate(wav_files[:10]):  # Show first 10 for preview
        old_name = wav_file.name
        new_name = old_name
        
        print(f"File {i+1}: {old_name}")
        
        # Step 1: Add task if not present
        if not has_task_in_filename(old_name):
            new_name = add_task_to_filename(old_name)
            print(f"  -> Add task: {new_name}")
        
        # Step 2: Reorder filename parts  
        reordered_name = reorder_filename_parts(new_name)
        if reordered_name != new_name:
            print(f"  -> Reorder: {reordered_name}")
            new_name = reordered_name
        
        if new_name != old_name:
            print(f"  ✅ Final: {old_name} -> {new_name}")
            change_count += 1
        else:
            print(f"  ➡️  No change needed")
        print()
    
    if len(wav_files) > 10:
        print(f"... and {len(wav_files) - 10} more files")
    
    # Count total changes
    total_changes = 0
    for wav_file in wav_files:
        old_name = wav_file.name
        new_name = old_name
        
        if not has_task_in_filename(old_name):
            new_name = add_task_to_filename(old_name)
        
        new_name = reorder_filename_parts(new_name)
        
        if new_name != old_name:
            total_changes += 1
    
    print(f"\nTotal: {total_changes} files would be renamed out of {len(wav_files)} files.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rename NeuroVoz audio files")
    parser.add_argument(
        "--data-dir",
        default="/home/yzhong/data/storage1t/NeuroVoz/data/audios",
        help="Source path that contains the original WAV files",
    )
    parser.add_argument(
        "--new-data-dir",
        help="Destination directory where renamed WAV files are written",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Show potential changes without touching any files",
    )

    args = parser.parse_args()

    if args.preview:
        preview_changes(args.data_dir)
    else:
        if args.new_data_dir:
            rename_neurovoz_files(args.data_dir, args.new_data_dir)
        else:
            print("No --new-data-dir provided; renaming files in place (legacy behavior)")
            rename_neurovoz_files(args.data_dir)