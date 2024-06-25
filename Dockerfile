# Use the official ANTs image from Docker Hub as the base image
FROM antsx/ants:latest

# Install Python and pip
RUN apt-get update && apt-get install -y python3 python3-venv

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Create a virtual environment and install dependencies
RUN python3 -m venv venv && \
    . /app/venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download en_core_web_sm

# Set execute permissions for the antsBrainExtraction.sh script
# Create output directory with proper permissions
RUN mkdir -p /app/images/output && chmod +x /app/images/output

# Copy the rest of your application code into the container
COPY . .

# Set execute permissions for the antsBrainExtraction.sh script
RUN chmod +x /app/utils/antsBrainExtraction.sh

# Activate the virtual environment and set it as the default for all future commands
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Expose the port Streamlit runs on
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableXsrfProtection=false"]