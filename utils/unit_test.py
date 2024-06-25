import nibabel as nib
import numpy as np
import os
import yaml
from scipy.spatial.distance import dice

def load_nifti(filepath):
    img = nib.load(filepath)
    return img.get_fdata()

def calculate_dice_coefficient(mask1, mask2):
    mask1 = mask1.astype(bool)
    mask2 = mask2.astype(bool)
    return 1 - dice(mask1.flatten(), mask2.flatten())

def main():
    # Adjust the path to the configuration file based on the environment
    config_path = "config.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    output_dir = config["pipeline_environment"]["output"]
    ground_truth_mask_path = os.path.join(output_dir, 'ground_truth_mask.nii.gz')
    new_model_mask_path = os.path.join(output_dir, 'brain_extractionBrainExtractionMask.nii.gz')
    artifacts_file_path = 'utils/artifacts.txt'
    
    if os.path.exists(artifacts_file_path):
        with open(artifacts_file_path, 'r') as f:
            previous_dice_score = float(f.read().strip().split(': ')[1])
    else:
        previous_dice_score = 0.0

    new_model_mask = load_nifti(new_model_mask_path)
    ground_truth_mask = load_nifti(ground_truth_mask_path)
    
    new_dice_score = calculate_dice_coefficient(new_model_mask, ground_truth_mask)
    
    with open(artifacts_file_path, 'w') as f:
        f.write(f'Dice Score: {new_dice_score}\n')
    
    assert new_dice_score >= previous_dice_score, (
        f"New Dice score {new_dice_score} is not better than the previous score {previous_dice_score}."
    )

if __name__ == "__main__":
    main()
