# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app
RUN rm /app/.env || true
COPY requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

ENV ENV=production

# Make port 80 available to the world outside this container
EXPOSE 80

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3100"]