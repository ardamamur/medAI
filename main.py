import streamlit as st
from PIL import Image
import os
import subprocess
import nibabel as nib
import matplotlib.pyplot as plt
import numpy as np
import SimpleITK as sitk
import tempfile
import plotly.graph_objects as go
from extraction import *
from findings import *
import os

# Configure page settings
st.set_page_config(page_title="Brain Volume Estimation", page_icon=":brain:", layout="wide")
# Load images
brain_banner = Image.open('images/sources/Brain.png')

# Load custom CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("style.css")


def brain_volume_extraction():
    t1, t2 = st.columns((1, 8))
    t1.image(brain_banner, width=180)
    t2.title("Brain Volume Estimation")
    t2.markdown("Given a CT series of a human brain, the task is to automatically segment the brain area inside the skull and measure its volume in milliliters.", unsafe_allow_html=True)
    already_extracted = st.checkbox("Already have an extracted brain image?")
    if already_extracted:
        uploaded_extracted_file = st.file_uploader("Upload the extracted brain NIfTI file", type=["nii", "nii.gz"], key="extracted_file_uploader")
        if uploaded_extracted_file:
            progress_bar = st.progress(0)
            progress_text = st.empty()
            progress_text.text("Loading extracted NIfTI file...")

            with tempfile.TemporaryDirectory() as temp_dir:
                file_path = os.path.join(temp_dir, uploaded_extracted_file.name)
                with open(file_path, 'wb') as f:
                    f.write(uploaded_extracted_file.read())

                image_np = load_nifti_file(file_path, "extracted_nifti_image_data")
                brain_volume = calculate_brain_volume(file_path, progress_bar)

                progress_bar.progress(100)
                progress_text.text("Process complete.")

                st.subheader("Results")
                st.write(f"**Brain Volume:** {brain_volume:.2f} ml")
                st.subheader("Brain Volume Visualization")
                plot_brain_volume(brain_volume)

                st.subheader("Brain Mask Overlays")
                col1, col2, col3 = st.columns(3)
                with col1:
                    overlay_image = create_overlay_image(file_path, file_path, 'axial')
                    st.image(overlay_image, caption="Axial View")
                with col2:
                    overlay_image = create_overlay_image(file_path, file_path, 'coronal')
                    st.image(overlay_image, caption="Coronal View")
                with col3:
                    overlay_image = create_overlay_image(file_path, file_path, 'sagittal')
                    st.image(overlay_image, caption="Sagittal View")
    else:
        uploaded_files = st.file_uploader("Choose DICOM or NIfTI Files", accept_multiple_files=True, type=["dcm", "nii", "nii.gz"], key="file_uploader")

        if uploaded_files:
            progress_bar = st.progress(0)
            progress_text = st.empty()
            progress_text.text("Starting the process...")

            with tempfile.TemporaryDirectory() as temp_dir:
                is_nifti = False
                for uploaded_file in uploaded_files:
                    bytes_data = uploaded_file.read()
                    file_path = os.path.join(temp_dir, uploaded_file.name)
                    with open(file_path, 'wb') as f:
                        f.write(bytes_data)
                    if uploaded_file.name.endswith(('.nii', '.nii.gz')):
                        is_nifti = True

                if is_nifti:
                    progress_text.text("Loading NIfTI file...")
                    image_np = load_nifti_file(file_path, "nifti_image_data")
                    nifti_image = file_path
                else:
                    progress_text.text("Loading DICOM series...")
                    image_np = load_and_store_dicom_series(temp_dir, "dicom_image_data")
                    nifti_image = None

                if nifti_image:
                    progress_text.text("Extracting brain with ANTs...")
                    brain_volume, brain_mask_nifti = extract_brain_with_ants(nifti_image, progress_bar)
                    progress_bar.progress(100)
                    progress_text.text("Process complete.")
                    st.subheader("Results")
                    st.write(f"**Brain Volume:** {brain_volume:.2f} ml")
                    st.subheader("Brain Volume Visualization")
                    plot_brain_volume(brain_volume)

                    st.subheader("Brain Mask Overlays")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        overlay_image = create_overlay_image(nifti_image, brain_mask_nifti, 'axial')
                        st.image(overlay_image, caption="Axial View")
                    with col2:
                        overlay_image = create_overlay_image(nifti_image, brain_mask_nifti, 'coronal')
                        st.image(overlay_image, caption="Coronal View")
                    with col3:
                        overlay_image = create_overlay_image(nifti_image, brain_mask_nifti, 'sagittal')
                        st.image(overlay_image, caption="Sagittal View")

def report_findings():
    st.title("Findings from Radiology Reports")
    st.markdown("Input a radiology report to extract medical entities in a structured form.", unsafe_allow_html=True)
    
    report_text = st.text_area("Radiology Report", height=300)
    
    if st.button("Extract Findings"):
        if report_text:
            entities = extract_entities(report_text)
            result_json = convert_to_json(entities)
            st.subheader("Extracted Entities")
            st.json(result_json)
        else:
            st.warning("Please input a radiology report.")

# Main sidebar
st.sidebar.title("medAI 🚨")
page_names_to_funcs = {
    "Brain Volume Estimation": brain_volume_extraction,
    "Findings from Radiology Reports": report_findings,
    "Classification of CT vs CTA": None
}
selected_page = st.sidebar.selectbox("Select a service", page_names_to_funcs.keys(), key="value")
page_names_to_funcs[selected_page]()


