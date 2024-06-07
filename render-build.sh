#!/bin/bash

# Update package list and install system dependencies
apt-get update && apt-get install -y tesseract-ocr libleptonica-dev

# Install the French language data for Tesseract
apt-get install -y tesseract-ocr-fra

# Install Python dependencies
pip install -r requirements.txt
