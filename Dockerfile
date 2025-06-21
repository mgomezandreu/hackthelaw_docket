# Use the official lightweight Python 3.12 image.
# https://hub.docker.com/_/python
FROM python:3.12-slim

# Set environment variables for production.
# 1. Prevents Python from buffering stdout and stderr.
# 2. Sets the version of tini to install.
ENV PYTHONUNBUFFERED=1
ENV TINI_VERSION v0.19.0

# Install tini, a lightweight and robust init system that reaps zombie
# processes and forwards signals. This is a best practice for containers.
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini

# Set the working directory in the container.
WORKDIR /app

# Copy the requirements file and install dependencies first.
# This leverages Docker's layer caching. The dependencies will only be
# re-installed if the requirements.txt file changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application source code into the container.
COPY . .

# Expose the port that the application will run on.
# Cloud Run automatically provides the PORT environment variable.
EXPOSE ${PORT}

# Set the entrypoint to tini. This ensures that the main application
# process (gunicorn) runs as PID 1 and receives signals correctly.
ENTRYPOINT ["/tini", "--"]

# Run the web server.
# Gunicorn is a production-ready WSGI server.
# The number of workers can be adjusted based on the application's needs
# and the Cloud Run instance's resources. A common starting point is (2 * Gunicorn) + 1.
# We're binding to 0.0.0.0 so it can be reached from outside the container,
# and to the $PORT variable provided by Cloud Run.
# Replace 'main:app' with '{your_main_python_file}:{your_wsgi_app_variable}'.
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT}", "--workers", "1", "main:app"]
