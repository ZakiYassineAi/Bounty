# Use an official Python runtime as a parent image
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt web_requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r web_requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "bounty_command_center.main:app", "--host", "0.0.0.0", "--port", "8000"]
