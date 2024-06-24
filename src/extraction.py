import streamlit
from PIL import Image
import os
import subprocess
import shutil
import nibabel as nib
import matplotlib.pyplot as plt
import numpy as np
import SimpleITK as sitk
import plotly.graph_objects as go
import tempfile
import yaml

class BrainVolumeExtractor:
    def __init__(self, st: streamlit):
        self.st = st
        self.t1, self.t2 = st.columns((1, 8))
        with open('/app/config.yaml', 'r') as f:
            self.config = yaml.safe_load(f)
        brain_banner = Image.open(self.config['environment']['sources'] + 'Brain.png')
        self.t1.image(brain_banner, width=180)
        self.t2.title("Brain Volume Estimation")
        self.t2.markdown("Given a CT series of a human brain, the task is to automatically segment the brain area inside the skull and measure its volume in milliliters.", unsafe_allow_html=True)
        self.already_extracted = self.st.checkbox("Already have an extracted brain image?")
        self.template = self.st.selectbox("Select the template", ["IXI", "OASIS", "NKI", "KIRBY", "KIRBYMULTIMODAL"])
        self.template_path = self.config['environment']['templates'] + self.template + '/'

    def calculate_brain_volume(self, mask_path, progress_bar):
        img = nib.load(mask_path)
        data = img.get_fdata()
        voxel_volume = np.prod(img.header.get_zooms())
        brain_voxels = np.sum(data > 0)
        brain_volume_ml = brain_voxels * voxel_volume / 1000
        progress_bar.progress(80)
        return brain_volume_ml

    def create_overlay_image(self, nifti_image, mask_image, axis):
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
            mask_slice = mask_data[data.shape[0] // 2, :, :]
        else:
            raise ValueError("Axis must be 'axial', 'coronal', or 'sagittal'")
        ax.imshow(np.rot90(slice_data), cmap='gray')
        ax.imshow(np.rot90(mask_slice), cmap='hot', alpha=0.5)
        ax.axis('off')

        overlay_path = self.config['environment']['output'] + f'overlay_{axis}.png'
        fig.savefig(overlay_path, bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        return overlay_path

    def plot_brain_volume(self, volume):
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
        self.st.plotly_chart(fig)

    def load_nifti_file(self, filepath, session_key):
        if session_key not in self.st.session_state:
            nifti_img = nib.load(filepath)
            image_np = np.asanyarray(nifti_img.dataobj)
            self.st.session_state[session_key] = image_np
        return self.st.session_state[session_key]

    def load_and_store_dicom_series(self, directory, session_key):
        if session_key not in self.st.session_state:
            reader = sitk.ImageSeriesReader()
            dicom_names = reader.GetGDCMSeriesFileNames(directory)
            reader.SetFileNames(dicom_names)
            image_sitk = reader.Execute()
            image_np = sitk.GetArrayFromImage(image_sitk)
            self.st.session_state[session_key] = image_np
        return self.st.session_state[session_key]

    def convert_dicom_to_nifti(self, dicom_file, progress_bar):
        dicom_path = 'temp_dicom.dcm'
        with open(dicom_path, 'wb') as f:
            f.write(dicom_file.getbuffer())
        output_dir = 'nifti_output'
        os.makedirs(output_dir, exist_ok=True)
        subprocess.run(['dcm2niix', '-o', output_dir, dicom_path], check=True)
        nifti_file = [f for f in os.listdir(output_dir) if f.endswith('.nii.gz')][0]
        progress_bar.progress(40)
        return os.path.join(output_dir, nifti_file)

    def extract_brain_with_ants(self, nifti_image, progress_bar):
        template_image = os.path.join(self.template_path, 'T_template0.nii.gz')
        brain_probability_mask = os.path.join(self.template_path, 'T_template_BrainCerebellumProbabilityMask.nii.gz')
        output_dir = self.config['environment']['output']
        
        # Ensure the output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        output_prefix = os.path.join(output_dir, 'brain_extraction')

        # Debugging: print paths to ensure they are correct
        self.st.text(f'NIfTI image: {nifti_image}')
        self.st.text(f'Template image: {template_image}')
        self.st.text(f'Brain probability mask: {brain_probability_mask}')
        self.st.text(f'Output directory: {output_dir}')
        self.st.text(f'Output prefix: {output_prefix}')

        # Check if files exist
        if not os.path.exists(nifti_image):
            self.st.error(f"NIfTI image {nifti_image} does not exist.")
            return None
        if not os.path.exists(template_image):
            self.st.error(f"Template image {template_image} does not exist.")
            return None
        if not os.path.exists(brain_probability_mask):
            self.st.error(f"Brain probability mask {brain_probability_mask} does not exist.")
            return None

        try:
            subprocess.run([
                '/app/utils/antsBrainExtraction.sh',
                '-d', '3',
                '-a', nifti_image,
                '-e', template_image,
                '-m', brain_probability_mask,
                '-o', output_prefix
            ], check=True)
        except subprocess.CalledProcessError as e:
            self.st.error(f"ANTs brain extraction failed: {e}")
            return None

        brain_mask_nifti = f'{output_prefix}BrainExtractionMask.nii.gz'
        brain_extraction_nifti = f'{output_prefix}BrainExtractionBrain.nii.gz'

        # Ensure output files were created
        if not os.path.isfile(brain_mask_nifti) or not os.path.isfile(brain_extraction_nifti):
            self.st.error(f"Brain mask or brain extraction files were not created.")
            return None

        # Debugging: log the existence of output files
        self.st.text(f'Brain mask exists: {os.path.isfile(brain_mask_nifti)}')
        self.st.text(f'Brain extraction exists: {os.path.isfile(brain_extraction_nifti)}')

        progress_bar.progress(80)
        return brain_mask_nifti

    def process_extracted_file(self, uploaded_extracted_file, uploaded_input_brain_image):
        progress_bar = self.st.progress(0)
        progress_text = self.st.empty()
        progress_text.text("Loading extracted NIfTI file...")
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, uploaded_extracted_file.name)
            input_file_path = os.path.join(temp_dir, uploaded_input_brain_image.name)
            with open(file_path, 'wb') as f:
                f.write(uploaded_extracted_file.read())
            with open(input_file_path, 'wb') as f:
                f.write(uploaded_input_brain_image.read())
            image_np = self.load_nifti_file(file_path, "extracted_nifti_image_data")
            progress_bar.progress(20)
            progress_text.text("Calculating brain volume...")
            brain_volume = self.calculate_brain_volume(file_path, progress_bar)
            progress_bar.progress(100)
            progress_text.text("Process complete.")
            self.st.subheader("Results")
            self.st.write(f"**Brain Volume:** {brain_volume:.2f} ml")
            self.st.subheader("Brain Volume Visualization")
            self.plot_brain_volume(brain_volume)
            self.st.subheader("Brain Mask Overlays")
            col1, col2, col3 = self.st.columns(3)
            with col1:
                overlay_image = self.create_overlay_image(input_file_path, file_path, 'axial')
                self.st.image(overlay_image, caption="Axial View")
            with col2:
                overlay_image = self.create_overlay_image(input_file_path, file_path, 'coronal')
                self.st.image(overlay_image, caption="Coronal View")
            with col3:
                overlay_image = self.create_overlay_image(input_file_path, file_path, 'sagittal')
                self.st.image(overlay_image, caption="Sagittal View")

    def process_dicom_or_nifti_files(self, uploaded_files):
        progress_bar = self.st.progress(0)
        progress_text = self.st.empty()
        progress_text.text("Starting the process...")
        output_dir = 'output_files'
        os.makedirs(output_dir, exist_ok=True)

        is_nifti = False
        file_paths = []
        for uploaded_file in uploaded_files:
            file_path = os.path.join(output_dir, uploaded_file.name)
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.read())
            file_paths.append(file_path)
            if uploaded_file.name.endswith(('.nii', '.nii.gz')):
                is_nifti = True
        
        if is_nifti:
            progress_text.text("Loading NIfTI file...")
            nifti_file_path = file_paths[0]
        else:
            dicom_file_path = file_paths[0]
            nifti_file_path = self.convert_dicom_to_nifti(dicom_file_path, progress_bar)
            if nifti_file_path is None:
                progress_text.text("Failed to convert DICOM to NIfTI.")
                return

        if not os.path.exists(nifti_file_path):
            self.st.error(f"NIfTI file {nifti_file_path} does not exist.")
            return

        progress_bar.progress(20)
        progress_text.text("Extracting brain with ANTs...")
        extracted_brain_mask = self.extract_brain_with_ants(nifti_file_path, progress_bar)
        if extracted_brain_mask is None:
            progress_text.text("Brain extraction failed.")
            return
        progress_bar.progress(80)
        progress_text.text("Calculating brain volume...")
        brain_volume = self.calculate_brain_volume(extracted_brain_mask, progress_bar)
        progress_bar.progress(100)
        progress_text.text("Process complete.")
        self.st.subheader("Results")
        self.st.write(f"**Brain Volume:** {brain_volume:.2f} ml")
        self.st.subheader("Brain Volume Visualization")
        self.plot_brain_volume(brain_volume)
        self.st.subheader("Brain Mask Overlays")
        col1, col2, col3 = self.st.columns(3)
        input_file_path = nifti_file_path if is_nifti else dicom_file_path
        with col1:
            overlay_image = self.create_overlay_image(input_file_path, extracted_brain_mask, 'axial')
            self.st.image(overlay_image, caption="Axial View")
        with col2:
            overlay_image = self.create_overlay_image(input_file_path, extracted_brain_mask, 'coronal')
            self.st.image(overlay_image, caption="Coronal View")
        with col3:
            overlay_image = self.create_overlay_image(input_file_path, extracted_brain_mask, 'sagittal')
            self.st.image(overlay_image, caption="Sagittal View")


    def run(self):
        if self.already_extracted:
            uploaded_input_brain_image = self.st.file_uploader("Upload the converted NIfTI Brain Image",
                                                               type=["nii", "nii.gz"], key="input_brain_image_uploader")
            uploaded_extracted_brain_image = self.st.file_uploader("Upload the extracted NIfTI Brain Image",
                                                                   type=["nii", "nii.gz"], key="extracted_file_uploader")
            if uploaded_extracted_brain_image and uploaded_input_brain_image:
                self.process_extracted_file(uploaded_extracted_brain_image, uploaded_input_brain_image)
            else:
                self.st.warning("Please upload both the input and extracted NIfTI brain images.")
        else:
            uploaded_files = self.st.file_uploader("Choose series of DICOM images or converted NIfTI Image",
                                                   accept_multiple_files=True, type=["dcm", "nii", "nii.gz"], key="file_uploader")
            if uploaded_files:
                self.process_dicom_or_nifti_files(uploaded_files)
