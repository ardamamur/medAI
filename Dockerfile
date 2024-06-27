# Use the official ANTs image from Docker Hub as the base image
FROM antsx/ants:latest

# Set environment variables to avoid some potential installation issues
ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

# Install system dependencies for building Python
RUN apt-get update && \
    apt-get install -y build-essential gcc cmake curl libssl-dev libffi-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget

# Download and install Python 3.10
RUN wget https://www.python.org/ftp/python/3.10.0/Python-3.10.0.tgz && \
    tar -xzf Python-3.10.0.tgz && \
    cd Python-3.10.0 && \
    ./configure --enable-optimizations && \
    make -j$(nproc) && \
    make altinstall && \
    ln -s /usr/local/bin/python3.10 /usr/bin/python3.10 && \
    cd .. && rm -rf Python-3.10.0 Python-3.10.0.tgz

# Install pip for Python 3.10
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python3.10 get-pip.py && \
    rm get-pip.py

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
