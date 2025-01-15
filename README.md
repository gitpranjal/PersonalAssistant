# Developer Assistant Project

This project provides a chatbot interface powered by Gradio and an AI-based assistant capable of dynamically applying Retrieval-Augmented Generation (RAG) to analyze directories and provide intelligent responses.

---

## Prerequisites

1. **Anaconda/Miniconda**: Ensure you have Anaconda or Miniconda installed on your system.
2. **Python 3.11**: The project requires Python version 3.11.
3. **Ollama**: The project uses Ollama to run Llama models locally. Ensure you have Ollama installed.

### Setting up Ollama and Llama 3.2

1. **Install Ollama**: Visit the [Ollama website](https://ollama.com) and follow the instructions to install Ollama on your system.

2. **Download Llama 3.2**: Use the following command to download and set up Llama 3.2:

   ```bash
   ollama pull llama3.2
   ```

3. **Run Ollama Locally**: Ensure Ollama is running locally on port 11434. Start the server with:

   ```bash
   ollama serve --port 11434
   ```

4. **Localhost Endpoint**: The chatbot communicates with the model using the endpoint:

   ```
   http://localhost:11434/api/chat
   ```

   Since the model runs locally, no data is sent to the cloud, making it secure for confidential company information and code.

---

## Automated Setup and Run

To streamline the setup and execution process, you can use the following Bash scripts:

### setup.sh

Create a `setup.sh` file with the following content:

```bash
#!/bin/bash

# Remove existing environment
conda env remove -n llmenv

# Create new environment
conda env create -f environment.yml

echo "Environment setup complete. Activate it using: conda activate llmenv"
```

### run.sh

Create a `run.sh` file with the following content:

```bash
#!/bin/bash

# Activate the environment
conda activate llmenv

# Run the chatbot application
/opt/anaconda3/envs/llmenv/bin/python chat_window.py
```

### Usage

1. **Set up the environment**:

   ```bash
   bash setup.sh
   ```

2. **Run the project**:

   ```bash
   bash run.sh
   ```

---

## Project Structure

- **`chat_window.py`**: The main entry point for running the chatbot application.
- **`RAG/`**: Contains the RAG (Retrieval-Augmented Generation) implementation and vector storage logic.
- **`Tools/`**: Includes utilities like the repository analyzer.
- **`static/scout.jpg`**: A static image used as an icon in the chatbot interface.
- **`environment.yml`**: Defines the virtual environment and dependencies required for the project.
- **`model_handler.py`**: Manages interactions between the chatbot and various tools.

---

## How It Works

### Dynamic Retrieval-Augmented Generation (RAG)

- **Initialization**:

  - The `RAGHandler` initializes a Chroma vector store with a dummy dataset to ensure functionality.
  - The dummy document contains placeholder content and metadata for the vector store.

- **File Processing**:

  - When a repository is provided, the handler recursively collects all files with supported extensions (e.g., `.py`, `.txt`, `.md`).
  - Each file is read, and its content is loaded into LangChain's `Document` objects.
  - Metadata (e.g., file name, path, type) is added to each document.
  - The content is divided into manageable chunks and added to the Chroma vector store.

- **Query Execution**:

  - When the user submits a query, the vector store retrieves the most relevant documents.
  - If no relevant document is found, the query falls back to the LLM for a response.
  - Retrieved documents provide context for the LLM to generate accurate and relevant answers.

### Code Repository Analysis

- Supports analyzing repositories and answering questions about their structure, content, and logic.
- Provides responses based on insights derived from the repository.

### Customizable Responses

- Includes a personalized icon (`static/scout.jpg`) in all responses to enhance the user experience.
- The chatbot greets the user with an initial message when it launches.

### Secure and Confidential

- Since the model runs locally, no data is sent to the cloud.
- Ideal for analyzing confidential company information and code securely.

---

