import streamlit as st
from PIL import Image
import os
import subprocess
import nibabel as nib
import matplotlib.pyplot as plt
import numpy as np
import tempfile
import plotly.graph_objects as go
from src.extraction import *
from src.findings import *
import os
import shutil

# Configure page settings
st.set_page_config(page_title="Brain Volume Estimation", page_icon=":brain:", layout="wide")


# Load custom CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

local_css("/app/.streamlit/style.css")


def brain_volume_extraction():
    extractor = BrainVolumeExtractor(st)
    extractor.run()



def report_findings():
    extractor = FindingsExtractor(st)
    extractor.run()



# Main sidebar
st.sidebar.title("medAI 🚨")
page_names_to_funcs = {
    "Brain Volume Estimation": brain_volume_extraction,
    "Findings from Radiology Reports": report_findings,
    "Classification of CT vs CTA": None
}
selected_page = st.sidebar.selectbox("Select a service", page_names_to_funcs.keys(), key="value")
page_names_to_funcs[selected_page]()


