from model_handler import Modelhandler
from Tools.repo_analyzer import RepoAnalyzer
import gradio as gr


OLLAMA_API = "http://localhost:11434/api/chat"
MODEL = "deepseek-r1"

if __name__ == "__main__":
    # Initialize the tool and model handler
    tool = RepoAnalyzer(model=MODEL, localApiUrl=OLLAMA_API)
    api = Modelhandler(localAPIUrl=OLLAMA_API, model=MODEL, tool=tool)

    gr.ChatInterface(fn=api.chat_with_tool_icon, type="messages").launch()

