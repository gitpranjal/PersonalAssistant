#!/bin/bash

# Remove existing environment
conda env remove -n llmenv

# Create new environment
conda env create -f environment.yml

# Activate the environment
conda activate llmenv

echo "Environment setup complete. Activated it using: conda activate llmenv"