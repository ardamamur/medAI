# Use the official ANTs image from Docker Hub as the base image
FROM antsx/ants:latest

# Set environment variables to avoid some potential installation issues
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

# Install Python 3.10 and pip along with system dependencies
RUN apt-get update && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.10 python3.10-dev python3.10-distutils build-essential gcc cmake curl && \
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python3.10 get-pip.py

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install dependencies using pip
RUN python3.10 -m pip install --no-cache-dir -r requirements.txt

# Create output directory with proper permissions
RUN mkdir -p /app/images/output && chmod -R 755 /app/images/output

# Copy the rest of your application code into the container
COPY . .

# Set execute permissions for the antsBrainExtraction.sh script
RUN chmod +x /app/utils/antsBrainExtraction.sh

# Expose the port Streamlit runs on
EXPOSE 8501

# Command to run the application
CMD ["python3.10", "-m", "streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableXsrfProtection=false"]
