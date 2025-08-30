# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements files into the container at /app
COPY requirements.txt web_requirements.txt ./

# Install any needed packages specified in requirements.txt and web_requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r web_requirements.txt

# Copy the rest of the application's code into the container at /app
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the application
CMD ["uvicorn", "bounty_command_center.main:app", "--host", "0.0.0.0", "--port", "8000"]
