#!/usr/bin/env python3
"""
Ollama Model Download Script
Downloads and prepares Llama 3 8B model for use in Agent47
"""

import os
import sys
import logging
import time
import subprocess
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_llama_model():
    """Download and prepare Llama 3 8B model using Ollama"""
    
    model_name = "llama3:8b"
    ollama_url = "http://localhost:11434"
    
    max_retries = 3
    retry_delay = 30
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Downloading Llama 3 8B model via Ollama (attempt {attempt + 1}/{max_retries})")
            
            # Check if Ollama is running
            try:
                response = requests.get(f"{ollama_url}/api/tags", timeout=10)
                if response.status_code != 200:
                    logger.error("Ollama service not responding")
                    raise Exception("Ollama service not available")
            except Exception as e:
                logger.error(f"Failed to connect to Ollama: {e}")
                raise
            
            # Download model using Ollama
            logger.info("Downloading Llama 3 8B model...")
            pull_response = requests.post(
                f"{ollama_url}/api/pull",
                json={"name": model_name},
                timeout=600  # 10 minute timeout for download
            )
            
            if pull_response.status_code == 200:
                logger.info("Llama 3 8B model downloaded successfully!")
                return
            else:
                logger.error(f"Failed to download model: {pull_response.status_code}")
                raise Exception(f"Download failed: {pull_response.status_code}")
            
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("All download attempts failed")
                sys.exit(1)

if __name__ == "__main__":
    download_llama_model()
