FROM python:3.12-slim

# Install PostgreSQL dependencies and clean up to reduce image size
RUN apt-get update && \
    apt-get install -y libmagic1 libpq-dev python3-dev build-essential gcc && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Set the working directory
WORKDIR /app

# Copy the requirements.txt file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app

# Set the default command to run Django's development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:15576"]
