#!/bin/bash
set -e
git checkout -b add-github-actions-ci-final
cat > Dockerfile <<EOD
# Use an official Python runtime as a parent image
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt web_requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r web_requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "bounty_command_center.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOD
mkdir -p .github/workflows
cat > .github/workflows/ci.yml <<EOD
name: Python CI
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r web_requirements.txt
          pip install -r requirements-dev.txt
      - name: Run linters
        run: |
          black --check .
          ruff .
          bandit -r .
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r web_requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests with coverage
        run: |
          PYTHONPATH=. pytest --cov=bounty_command_center
  build-and-push-docker:
    runs-on: ubuntu-latest
    needs: [lint, test]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Log in to Docker Hub
        uses: docker/login-action@v2
        with:
          username: \${{ secrets.DOCKERHUB_USERNAME }}
          password: \${{ secrets.DOCKERHUB_TOKEN }}
      - name: Build and push
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: \${{ secrets.DOCKERHUB_USERNAME }}/bounty-command-center:latest
EOD
cat > requirements-dev.txt <<EOD
pytest
pytest-cov
black
ruff
bandit
EOD
git add .
git commit -m "feat: Add CI workflow and dev requirements"
git log -1
