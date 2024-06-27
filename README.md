# medAI : Healthcare Software Development Platform


## 🧐 About
Welcome to **medAI**, an advanced tool for medical image processing, leveraging the power of Streamlit for interactive data visualization. This project includes functionalities for brain volume extraction and findings from radiology reports, making it a versatile and user-friendly application for medical image analysis.

## Features
- **Brain Volume Estimation**: Automatically segments the brain area inside the skull and measures its volume in milliliters from CT scans.
- **Findings from Radiology Reports**: Extracts key findings from radiology reports.

### Qualitatives

![Result Image 2](https://github.com/ardamamur/medAI/blob/main/images/sources/medai_ss_1.PNG?raw=true)


## 🏁 Getting Started 

### Prerequisites
Ensure you have the following installed:
- Python 3.7 or higher
- Docker (for containerized deployment)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ardamamur/medAI.git
   cd medAI
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt

3. **Docker Deployment:**:
    ```bash
    docker build -t medai-app .

4. **Run the Docker Container**: (you can pull from the dockerhub)
    ```bash
    docker run -p 8501:8501 ardamamurtum/medai-app


![Result Image 2](https://github.com/ardamamur/medAI/blob/main/images/sources/medai_ss_2.PNG?raw=true)