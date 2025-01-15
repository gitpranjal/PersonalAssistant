# Developer Assistant Project

This project provides a chatbot interface powered by Gradio and an AI-based assistant capable of dynamically applying Retrieval-Augmented Generation (RAG) to analyze directories and provide intelligent responses.

---

## Project Structure

- **`chat_window.py`**: The main entry point for running the chatbot application.
- **`RAG/`**: Contains the RAG (Retrieval-Augmented Generation) implementation and vector storage logic.
- **`Tools/`**: Includes utilities like the repository analyzer.
- **`static/scout.jpg`**: A static image used as an icon in the chatbot interface.
- **`environment.yml`**: Defines the virtual environment and dependencies required for the project.
- **`model_handler.py`**: Manages interactions between the chatbot and various tools.

---

## Prerequisites

1. **Anaconda/Miniconda**: Ensure you have Anaconda or Miniconda installed on your system.
2. **Python 3.11**: The project requires Python version 3.11.
3. **Ollama**: The project uses Ollama to run Llama models locally. Ensure you have Ollama installed.

### Setting up Ollama and Llama 3.2

1. **Install Ollama**:
   Visit the [Ollama website](https://ollama.com) and follow the instructions to install Ollama on your system.

2. **Download Llama 3.2**:
   Use the following command to download and set up Llama 3.2:
   ```bash
   ollama pull llama3.2
   ```

3. **Run Ollama Locally**:
   Ensure Ollama is running locally on port 11434. Start the server with:
   ```bash
   ollama serve --port 11434
   ```

4. **Localhost Endpoint**:
   The chatbot communicates with the model using the endpoint:
   ```
   http://localhost:11434/api/chat
   ```
   Since the model runs locally, no data is sent to the cloud, making it secure for confidential company information and code.

---

## Steps to Run the Project

### 1. Set Up the Virtual Environment

1. **Remove any existing environment** (if applicable):
   ```bash
   conda env remove -n llmenv
   ```

2. **Create a new environment** using the provided `environment.yml` file:
   ```bash
   conda env create -f environment.yml
   ```

3. **Activate the environment**:
   ```bash
   conda activate llmenv
   ```

### 2. Run the Project

1. **Launch the chatbot application**:
   ```bash
   /opt/anaconda3/envs/llmenv/bin/python chat_window.py
   ```

2. The chatbot will open in a Gradio web interface, allowing interaction through a user-friendly UI.

---

## How It Works

### Dynamic Retrieval-Augmented Generation (RAG)
- The chatbot can dynamically apply RAG to any directory provided by the user.
- Users can upload or reference a directory, and the assistant will extract, process, and analyze the content.
- **File Processing**:
  - Fetches files from the provided directory.
  - Downloads and extracts their content.
  - Vectorizes the content using Chroma vector store.
  - Adds metadata for efficient querying.
  - Uses the vectorized data to answer queries using RAG.

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

