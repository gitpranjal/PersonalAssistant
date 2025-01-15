import json
import requests
from Tools.tool import Tool
from RAG.rag_handler import RAGHandler
import re
import os
import gradio as gr
import shutil
import time
import sys



# Constants

OLLAMA_API = "http://localhost:11434/api/chat"
MODEL = "llama3.2"
os.environ["ALLOW_RESET"] = "TRUE"

class Modelhandler:
    def __init__(self, localAPIUrl, model, tool:Tool):
        self.localAPIUrl = localAPIUrl
        self.model = model
        self.header = {"Content-Type": "application/json"}
        self.tools = [
            {"type": "function", "function": tool.get_tool_function_object()}
        ]
        self.tool = tool
        self.rag_handler = RAGHandler()


    
    def extract_local_directory_path(self, prompt):
        """
        Extracts a local directory path from a given prompt string.

        Args:
            prompt (str): The user prompt containing the directory path.

        Returns:
            str: The extracted local directory path if valid, otherwise None.
        """
        # Use a regular expression to find potential file paths
        path_pattern = r"(/\S+)"  # Matches paths starting with '/'
        matches = re.findall(path_pattern, prompt)
        
        # Validate if the matched paths are existing directories
        for match in matches:
            if os.path.isdir(match):
                return match

        return None


    def _is_code_analysis_request(self, message):
        """
        Check if the message is likely a request for repository analysis.
        """
        keywords = ["analyze", "repository", "codebase", "directory"]
        return any(keyword in message.lower() for keyword in keywords)
    
    def _is_rag_request(self, message):
        """
        Check if the message is likely a request for repository analysis.
        """
        if "using rag" in message.lower() or "use rag" in message.lower() or "use retrieval augmented generation" in message.lower() or "use retrieval augmented generation" in message.lower():
            return True
        
    
    def _is_clear_history_request(self, message):
        """
        Check if the user wants to clear hostory
        """
        if "clear history" in message.lower() or "clear context" in message.lower() or "clear data" in message.lower():  
            return True
        

    
    def delete_directory_with_files(self, directory_path):
        """
        Deletes all files and subdirectories in a given directory and then deletes the directory itself.

        Args:
            directory_path (str): The path to the directory to be deleted.

        Returns:
            str: A success message if the operation is completed successfully.
        """
        if os.path.exists(directory_path) and os.path.isdir(directory_path):
            # Remove all contents inside the directory
            shutil.rmtree(directory_path)
            return f"Directory '{directory_path}' and all its contents have been deleted successfully."
        else:
            return f"Directory '{directory_path}' does not exist."

    
    def chat_with_tool(self, message, history):
        # Build the conversation history with system, previous messages, and the current user input

        if self._is_clear_history_request(message):

            # Restart the application
            gr.update(history=[])
            self.delete_directory_with_files("knowledge_base")
            self.rag_handler.reset_vectorstore_data()
            return "Reset the history and cleared stored data"


        
        repository_path = self.extract_local_directory_path(message)
        print(f"Extracted repository: {repository_path}")

        if repository_path and self._is_rag_request(message):
            self.rag_handler.update_vectorstore(repository_path)
            return "Rag vector store updated"
        
        rag_response = self.rag_handler.chat(message).strip()
        print(f"Response from rag_handler object: \n{rag_response}")
        if  rag_response != "NIL":
            print(f"Responding through rag vector store which gave the following response \n\n {rag_response}")
            return rag_response

        if not repository_path:
            # Skip tool processing and directly respond to general messages
            payload = {
                "model": self.model,
                "messages": [{"role": "system", "content": "You are a helpful assistant"}] + history + [{"role": "user", "content": message}],
                "stream": False
            }
            response = requests.post(self.localAPIUrl, json=payload, headers=self.header)
            if response.status_code == 200:
                return response.json().get("message", {}).get("content", "")
            else:
                raise Exception(f"Error: {response.status_code}, {response.text}")
            
       

        messages = [{"role": "system", "content": "You are a helpful assistant to that analyzes code, folders repositories for their content"}] + history + [{"role": "user", "content": message}]

        # Prepare the payload
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": self.tools,  # Pass tools to the model
            "stream": False       # Non-streaming request
        }

        # Make the API request
        response = requests.post(self.localAPIUrl, json=payload, headers=self.header)


        if response.status_code == 200:
            response_data = response.json()
            assistant_message = response_data.get("message", {})
            
            # Check if a tool is being called
            tool_calls = assistant_message.get("tool_calls", [])
            print(f"Tool calls: {tool_calls}")
            if tool_calls:
                tool_call = tool_calls[0]  # Assume a single tool call for simplicity
                

                arguments = tool_call["function"]["arguments"]
                # Call the corresponding tool handler
                tool_response = self.tool.handle_tool_call(arguments)
                
                # Append the tool response to the conversation
                messages.append({"role": "assistant", "content": "", "tool_calls": [tool_call]})
                messages.append({"role": "tool", "content": tool_response})

                # Make a follow-up API call with updated messages
                follow_up_payload = {
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                }
                follow_up_response = requests.post(self.localAPIUrl, json=follow_up_payload, headers=self.header)
                if follow_up_response.status_code == 200:
                    follow_up_data = follow_up_response.json()
                    final_content = follow_up_data.get("message", {}).get("content", "")
                    return final_content  # Return the assistant's final response
                else:
                    raise Exception(f"Follow-up Error: {follow_up_response.status_code}, {follow_up_response.text}")

            else:
                # If no tool is called, return the assistant's content directly
                return assistant_message.get("content", "")
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")
        

    def chat_with_tool_icon(self, message, history):

        ICON_PATH = os.path.join(os.path.dirname(__file__), "static/scout.jpg")

        # ICON_URL = f"file://{ICON_PATH}"  # Replace with your actual icon URL
        ICON_URL = "https://uxwing.com/squirrel-color-icon/"

        print(ICON_URL)
        
        if not history:
            initial_response = f"![icon]({ICON_URL}) Woof! Woof! How can I assist you today?"
            return initial_response

        # Check if the history needs to be cleared
        if self._is_clear_history_request(message):
            gr.update(history=[])
            self.delete_directory_with_files("knowledge_base")
            self.rag_handler.reset_vectorstore_data()
            return [{"role": "assistant", "content": "Reset the history and cleared stored data"}]

        repository_path = self.extract_local_directory_path(message)
        print(f"Extracted repository: {repository_path}")

        # Update vectorstore if necessary
        if repository_path and self._is_rag_request(message):
            self.rag_handler.update_vectorstore(repository_path)
            return [{"role": "assistant", "content": "Rag vector store updated"}]

        # Check RAG handler response
        rag_response = self.rag_handler.chat(message).strip()
        print(f"Response from rag_handler object: \n{rag_response}")
        if rag_response != "NIL":
            print(f"Responding through rag vector store which gave the following response \n\n {rag_response}")
            return [{"role": "assistant", "content": f"![icon]({ICON_URL}) {rag_response}"}]

        # Handle cases without repository path
        if not repository_path:
            payload = {
                "model": self.model,
                "messages": [{"role": "system", "content": "You are a helpful assistant"}]
                        + history
                        + [{"role": "user", "content": message}],
                "stream": False
            }
            response = requests.post(self.localAPIUrl, json=payload, headers=self.header)
            if response.status_code == 200:
                assistant_response = response.json().get("message", {}).get("content", "")
                return [{"role": "assistant", "content": f"![icon]({ICON_URL}) {assistant_response}"}]
            else:
                raise Exception(f"Error: {response.status_code}, {response.text}")

        # Prepare messages for the API call
        messages = [{"role": "system", "content": "You are a helpful assistant to that analyzes code, folders repositories for their content"}]
        messages += history + [{"role": "user", "content": message}]

        # Prepare the payload
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": self.tools,
            "stream": False
        }

        # Make the API call
        response = requests.post(self.localAPIUrl, json=payload, headers=self.header)
        if response.status_code == 200:
            response_data = response.json()
            assistant_message = response_data.get("message", {})

            # Check if a tool is being called
            tool_calls = assistant_message.get("tool_calls", [])
            print(f"Tool calls: {tool_calls}")
            if tool_calls:
                tool_call = tool_calls[0]
                arguments = tool_call["function"]["arguments"]

                # Call the tool handler
                tool_response = self.tool.handle_tool_call(arguments)

                # Append tool response to messages
                messages.append({"role": "assistant", "content": "", "tool_calls": [tool_call]})
                messages.append({"role": "tool", "content": tool_response})

                # Make a follow-up API call
                follow_up_payload = {
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                }
                follow_up_response = requests.post(self.localAPIUrl, json=follow_up_payload, headers=self.header)
                if follow_up_response.status_code == 200:
                    follow_up_data = follow_up_response.json()
                    final_content = follow_up_data.get("message", {}).get("content", "")
                    return [{"role": "assistant", "content": f"![icon]({ICON_URL}) {final_content}"}]
                else:
                    raise Exception(f"Follow-up Error: {follow_up_response.status_code}, {follow_up_response.text}")

            else:
                # Return the assistant's content with an icon
                return [{"role": "assistant", "content": f"![icon]({ICON_URL}) {assistant_message.get('content', '')}"}]
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")


    def stream_responses(self, response):
        """
        Stream responses from a given HTTP response.

        Args:
            response (requests.Response): The HTTP response object with streaming enabled.

        Yields:
            str: Accumulated content from the streamed response.
        """
        accumulated_content = ""

        for line in response.iter_lines(decode_unicode=True):
            if line:
                data = json.loads(line)  # Parse each line as JSON
                message = data.get("message", {})
                content = message.get("content", "")

                if content:
                    accumulated_content += content  # Accumulate content
                    yield accumulated_content  # Yield the accumulated content
