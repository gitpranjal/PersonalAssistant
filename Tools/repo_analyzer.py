import os
import json

import requests
from .tool import Tool

class RepoAnalyzer(Tool):
    def __init__(self, **kwargs):
        self.localApiUrl = kwargs.get('localApiUrl', 'http://localhost:11434/api/chat')
        self.model = kwargs.get('model')
        self.header = kwargs.get("header", {"Content-Type": "application/json"})
        self.tool_function = {
            "name": "analyze_repository",
            "description": (
                "Analyze a repository given a valid directory path. "
                "This tool should only be invoked when the user explicitly mentions analyzing a repository "
                "or provides a directory path for code analysis."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "repository_path": {
                        "type": "string",
                        "description": "The local file path to the repository that needs to be analyzed."
                    }
                },
                "required": ["repository_path"],
                "additionalProperties": False
            }
        }

    
    def get_tool_function_object(self):
        return self.tool_function
    
        
        

    def handle_tool_call(self, arguments):
        """
        Handles the invocation of the summarize_repository tool.
        """
        def chat(message):
            messages = [{"role": "system", "content": "You are a helpful assistant. Use all the given tools"}] + [{"role": "user", "content": message}]
            payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }

            response = requests.post(self.localApiUrl, json=payload, headers=self.header, stream=True)

            if response.status_code == 200:
                return response.content
            else:
                raise Exception(f"Error: {response.status_code}, {response.text}")
            
        # Function to read all files in a repository
        def read_repository_files(repo_path):

            directory_path = "knowledge_base"
            os.makedirs(directory_path, exist_ok=True)
            print(f"Directory '{directory_path}' is ready.")
            

            content = None
            try:
                for root, dirs, files in os.walk(repo_path):
                    allowed_extensions = {".py", ".java", ".js", ".rs", ".sh", ".txt", ".log", ".md"}  # Allowed file extensions
                    for file in files:
                        file_extension = os.path.splitext(file)[1]
                        if file_extension not in allowed_extensions:
                            continue
                        file_path = os.path.join(root, file)
                        if "node_modules" in file_path:
                            continue
                        try:
                            # Read the file content
                            with open(file_path, 'r', encoding="utf-8") as f:
                                content = f.read()
                                f.close()
                                                            
                            with open(f"./knowledge_base/{os.path.basename(repo_path)}.txt", "a", encoding="utf-8") as f:
                                print(f"{file_path} being read.....")
                                f.write(f"\n\n{file_path}\n")
                                f.write(content)
                                f.close()
                        except Exception as e:
                            print(f"Error reading file {file_path}: {str(e)}")
            except Exception as e:
                return {"error": f"Failed to read repository: {str(e)}"}

        # Function to summarize the repository
        def summarize_repository(repo_content):
            message = f"""You are supposed to analyze and summarize the content of a repositoy, 
                which could be code or text given. You should be able to answer any question or generate additional 
                content based upon this. The content is such that each file name is followed by it's content. 
                Summarize what's happenning, mentioning variable names, class names, imports and creating a short summary of how different compenents are interacting.
                    First mention the path and name of the file followed by the content.
                Here is the content \n\n {repo_content}"""
            
            return chat(message)

        # Handle the tool call dynamically
        repository_path = arguments.get("repository_path", "")

        print(f"Repository Path found: {repository_path}")
        
        if not repository_path or not os.path.exists(repository_path):
            return json.dumps({"error": "Invalid or non-existent repository path provided."})

        # Read the repository files
        read_repository_files(repository_path)
        with open(f"knowledge_base/{os.path.basename(repository_path)}.txt", "rb") as f:
            repo_content = f.read()
            try:
                repo_content = repo_content.decode('utf-8')  # Decode bytes to string
            except UnicodeDecodeError:
                repo_content = "Error decoding content as UTF-8."
            f.close()

        # Summarize the repository
        repo_summary = summarize_repository(repo_content)
        tool_response = {
            "repository_path": repository_path,
            "summary": repo_summary.decode('utf-8') if isinstance(repo_summary, bytes) else repo_summary
        }
        return json.dumps(tool_response)