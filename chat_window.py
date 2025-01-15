from model_handler import Modelhandler
from Tools.repo_analyzer import RepoAnalyzer
import gradio as gr


OLLAMA_API = "http://localhost:11434/api/chat"
MODEL = "llama3.2"

if __name__ == "__main__":
    # Initialize the tool and model handler
    tool = RepoAnalyzer()
    api = Modelhandler(OLLAMA_API, MODEL, tool)


    gr.ChatInterface(fn=api.chat_with_tool_icon, type="messages").launch()

