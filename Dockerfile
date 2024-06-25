# Use the official ANTs image from Docker Hub as the base image
FROM antsx/ants:latest

# Install Python and pip
RUN apt-get update && apt-get install -y python3 python3-pip

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Create output directory with proper permissions
RUN mkdir -p /app/images/output && chmod -R 755 /app/images/output

# Copy the rest of your application code into the container
COPY . .

# Set execute permissions for the antsBrainExtraction.sh script
RUN chmod +x /app/utils/antsBrainExtraction.sh

# Expose the port Streamlit runs on
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableXsrfProtection=false"]