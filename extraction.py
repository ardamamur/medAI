import streamlit as st
from PIL import Image
import os
import subprocess
import nibabel as nib
import matplotlib.pyplot as plt
import numpy as np
import SimpleITK as sitk
import plotly.graph_objects as go

def save_uploaded_file(uploaded_file, progress_bar):
    output_dir = 'nifti_output'
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, uploaded_file.name)
    with open(file_path, 'wb') as f:
        f.write(uploaded_file.getbuffer())
    progress_bar.progress(20)
    return file_path

def convert_dicom_to_nifti(dicom_file, progress_bar):
    dicom_path = 'temp_dicom.dcm'
    with open(dicom_path, 'wb') as f:
        f.write(dicom_file.getbuffer())
    output_dir = 'nifti_output'
    os.makedirs(output_dir, exist_ok=True)
    subprocess.run(['dcm2niix', '-o', output_dir, dicom_path])
    nifti_file = [f for f in os.listdir(output_dir) if f.endswith('.nii.gz')][0]
    progress_bar.progress(40)
    return os.path.join(output_dir, nifti_file)

def calculate_brain_volume(mask_path, progress_bar):
    img = nib.load(mask_path)
    data = img.get_fdata()
    voxel_volume = np.prod(img.header.get_zooms())  
    brain_voxels = np.sum(data > 0)
    brain_volume_ml = brain_voxels * voxel_volume / 1000
    progress_bar.progress(80)
    return brain_volume_ml

def extract_brain_with_ants(nifti_image, progress_bar):
    template_image = '/home/mamur/TUM/deepc/dataset/templates/IXI/T_template0.nii.gz'
    brain_probability_mask = '/home/mamur/TUM/deepc/dataset/templates/IXI/T_template_BrainCerebellumProbabilityMask.nii.gz'
    output_prefix = 'ants_output/brain_extraction'
    os.makedirs('ants_output', exist_ok=True)
    subprocess.run([
        '/home/mamur/TUM/ANTs/Scripts/antsBrainExtraction.sh',
        '-d', '3',
        '-a', nifti_image,
        '-e', template_image,
        '-m', brain_probability_mask,
        '-o', output_prefix
    ], check=True)
    progress_bar.progress(60)
    brain_mask_nifti = f'{output_prefix}BrainExtractionMask.nii.gz'
    brain_volume = calculate_brain_volume(brain_mask_nifti, progress_bar)
    progress_bar.progress(100)
    return brain_volume, brain_mask_nifti

def create_overlay_image(nifti_image, mask_image, axis):
    img = nib.load(nifti_image)
    mask = nib.load(mask_image)
    data = img.get_fdata()
    mask_data = mask.get_fdata()
    fig, ax = plt.subplots(figsize=(10, 10))
    if axis == 'axial':
        slice_data = data[:, :, data.shape[2] // 2]
        mask_slice = mask_data[:, :, mask_data.shape[2] // 2]
    elif axis == 'coronal':
        slice_data = data[:, data.shape[1] // 2, :]
        mask_slice = mask_data[:, mask_data.shape[1] // 2, :]
    elif axis == 'sagittal':
        slice_data = data[data.shape[0] // 2, :, :]
        mask_slice = mask_data[mask_data.shape[0] // 2, :, :]
    else:
        raise ValueError("Axis must be 'axial', 'coronal', or 'sagittal'")
    ax.imshow(np.rot90(slice_data), cmap='gray')
    ax.imshow(np.rot90(mask_slice), cmap='hot', alpha=0.5)
    ax.axis('off')
    overlay_path = f'images/output/overlay_{axis}.png'
    fig.savefig(overlay_path, bbox_inches='tight', pad_inches=0)
    plt.close(fig)
    return overlay_path

def plot_brain_volume(volume):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=volume,
        title={'text': "Brain Volume (ml)"},
        gauge={
            'axis': {'range': [None, 2000]},
            'steps': [
                {'range': [0, 1000], 'color': "lightgray"},
                {'range': [1000, 2000], 'color': "gray"}],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 1500}
        }))
    st.plotly_chart(fig)

def load_nifti_file(filepath, session_key):
    if session_key not in st.session_state:
        nifti_img = nib.load(filepath)
        image_np = np.asanyarray(nifti_img.dataobj)
        st.session_state[session_key] = image_np
    return st.session_state[session_key]

def load_and_store_dicom_series(directory, session_key):
    if session_key not in st.session_state:
        reader = sitk.ImageSeriesReader()
        dicom_names = reader.GetGDCMSeriesFileNames(directory)
        reader.SetFileNames(dicom_names)
        image_sitk = reader.Execute()
        image_np = sitk.GetArrayFromImage(image_sitk)
        st.session_state[session_key] = image_np
    return st.session_state[session_key]

def plot_slice(slice, size=(4, 4), is_nifti=False):
    fig, ax = plt.subplots(figsize=size)
    canvas_size = max(slice.shape)
    canvas = np.full((canvas_size, canvas_size), fill_value=slice.min(), dtype=slice.dtype)
    x_offset = (canvas_size - slice.shape[0]) // 2
    y_offset = (canvas_size - slice.shape[1]) // 2
    canvas[x_offset:x_offset+slice.shape[0], y_offset:y_offset+slice.shape[1]] = slice
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    if is_nifti:
        canvas = np.rot90(canvas)
    else:
        canvas = canvas[::-1, ::-1]
    ax.imshow(canvas, cmap='gray')
    ax.axis('off')
    return fig