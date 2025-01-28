import os
import json
import requests
import time

from RAG.embedding import SentenceTransformerEmbeddings


from langchain.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
import glob
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.schema import Document
import gradio as gr
from chromadb.config import Settings



class RAGHandler:
    def __init__(self, **kwargs):
        self.model_url = kwargs.get("model_url", "http://localhost:11434/api/chat")
        self.model = kwargs.get("model", "llama3.2")
        self.system_message = kwargs.get("system_message", """You are a helpful RAG assistant. 
                                         Use retrival augment geberation only if the user message is relevant to anything stored in vector score. Don't hallucinate. 
                                         Return the exact string 'VOID RAG RESPONSE', don;t add any explaination or string to it. This string will be compared in an if else statemnet, and the control will be transfered to default LLM repose if it is 'VOID RAG RESPONSE'. if the user messsage is not related to the retrieved documents or the retrieved document is dummy document with file_name dummy.txt
                                         """)
        self.db_name = kwargs.get("db_name", "developer_assistant_vectorstore")
        self.vectorstore = None
        

        self.initialize_vectorstore()
        

        # if os.path.exists(self.db_name):
        #     Chroma(persist_directory=self.db_name, embedding_function=embedding_model).delete_collection()

    def initialize_vectorstore(self):
        """
        Initialize the vector store with a dummy document if it doesn't exist.
        """

        # chroma_settings = Settings(persist_directory=os.path.abspath(self.db_name), allow_reset=True)  # Enable reset

        # Define a dummy document
        dummy_document = {
            "page_content": "This is a dummy document for initialization purposes.",
            "metadata": {"file_name": "dummy.txt", "file_path": "/dummy/path", "doc_type": "txt"}
        }

        embedding_model = SentenceTransformerEmbeddings("sentence-transformers/all-MiniLM-L6-v2")
        retry_attempts = 3

        # Check if the vector store already exists
        if not os.path.exists(self.db_name):
            # Create a new vector store with the dummy document
            for attempt in range(retry_attempts):
                try:
                    dummy_chunk = Document(page_content=dummy_document["page_content"], metadata=dummy_document["metadata"])
                    self.vectorstore = Chroma.from_documents(
                        documents=[dummy_chunk],
                        embedding=embedding_model,
                        # client_settings=chroma_settings,
                        persist_directory=self.db_name
                        
                    )
                    print(f"Vectorstore initialized with a dummy document at following path.")
                    print(os.path.abspath(self.vectorstore._persist_directory))
                    os.system(f"chmod -R u+w {os.path.abspath(self.vectorstore._persist_directory)}")
                    break
                except Exception as e:
                    if attempt < retry_attempts - 1:
                        print(f"Retrying vectorstore initialization... Attempt {attempt + 1}")
                        time.sleep(2)  # Small delay before retrying
                    else:
                        print(f"Failed to initialize vectorstore after {retry_attempts} attempts. Error: {e}")
        else:
            # Load existing vector store
            self.vectorstore = Chroma(embedding_function=embedding_model,
                                    #    client_settings=chroma_settings, 
                                       persist_directory=self.db_name)
            print("Vectorstore loaded successfully.")

    
    def update_vectorstore(self, arguments):
        """
        Creates or updates the vector store by processing the arguments. Extracts repository from the arguments
        """
        repository_path = arguments.get("repository_path", "")
        self.update_vectorstore(repository_path)


    def reset_vectorstore_data(self):
        """
        Clear all data from the Chroma vector store and add dummy data.
        """
        try:
            # List existing collections
            collections = self.vectorstore._client.list_collections()
            print("List of collections in vectorstore:", collections)

            # Check if the vector store has a collection
            if self.vectorstore._collection:
                collection_name = self.vectorstore._collection.name
                print(f"Clearing all vectors from the collection: {collection_name}")

                # Retrieve all vector IDs
                all_vectors = self.vectorstore._collection.get()  # Fetch all vectors without a filter
                vector_ids = all_vectors.get("ids", [])

                if vector_ids:
                    self.vectorstore._collection.delete(ids=vector_ids)
                    print(f"All vectors deleted from the collection: {collection_name}")
                else:
                    print("No vectors found in the collection to delete.")
            else:
                print("No collection found in the vector store.")

            # Add dummy data to the vectorstore
            dummy_texts = ["This is a dummy document.", "Another dummy document."]
            dummy_metadatas = [{"source": "dummy1"}, {"source": "dummy2"}]

            print("Adding dummy data to the vectorstore...")
            self.vectorstore.add_texts(texts=dummy_texts, metadatas=dummy_metadatas)
            print("Dummy data added successfully.")

        except Exception as e:
            print(f"Error resetting vector store: {e}")


    def update_vectorstore(self, repo_path):
        """
        Creates or updates the vector store by processing the repository.
        """
        def collect_files_recursive(path):
            """
            Collect files recursively in the directory and filter only the required file types.
            """
            allowed_extensions = [".py", ".java", ".js", ".rs", ".sh", ".txt", ".log", ".md"]
            files = []
            for root, _, filenames in os.walk(path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    if "node_modules" in file_path:
                        continue
                    if any(filename.endswith(ext) for ext in allowed_extensions):
                        files.append(file_path)
            return files

        def add_metadata(doc, file_path):
            doc.metadata["file_path"] = file_path
            doc.metadata["doc_type"] = os.path.splitext(file_path)[-1][1:]
            doc.metadata["file_name"] = os.path.basename(file_path)
            return doc

        # Load files and split into chunks
        text_loader_kwargs = {'encoding': 'utf-8'}
        documents = []
        files = collect_files_recursive(repo_path)

        for file_path in files:
            try:
                loader = TextLoader(file_path, **text_loader_kwargs)
                file_docs = loader.load()
                documents.extend([add_metadata(doc, file_path) for doc in file_docs])
            except Exception as e:
                print(f"Error loading file {file_path}: {str(e)}")

        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = text_splitter.split_documents(documents)

        if not os.path.exists(self.db_name):
            self.initialize_vectorstore()
        else:
            texts = [chunk.page_content for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]
            self.vectorstore.add_texts(texts=texts, metadatas=metadatas)
            print(f"{len(texts)} new docs added to the vector database.")


    def retrieve_documents(self, query):
        """
        Retrieve relevant documents from the vector store using the query.
        """
        if not self.vectorstore:
            return "No vector store found. Please create one first."
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})
        return retriever.get_relevant_documents(query)
    

    def generate_response(self, query, retrieved_documents):
        """
        Generate a response using the LLM with retrieved documents as context.
        """
        context = "\n\n".join([doc.page_content for doc in retrieved_documents])
        prompt = f"Context: {context}\n\nQuestion: {query}\n\nAnswer:"
        
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": self.system_message}, {"role": "user", "content": prompt}],
            "stream": False
        }
        response = requests.post(self.model_url, json=payload)
        if response.status_code == 200:
            return response.json().get("message", {}).get("content", "No content returned.")
        else:
            raise Exception(f"Error: {response.status_code}, {response.text}")
        

    def chat(self, message):
        """
        Unified chat function for general queries and RAG-based responses.
        """
        if self.vectorstore:
            # RAG workflow
            retrieved_docs = self.retrieve_documents(message)
            print(f"Retrieved Docs {retrieved_docs}")
            if retrieved_docs:
                return self.generate_response(message, retrieved_docs)
            
            print(f"No document retrieved: {retrieved_docs}")
            return ""
        
        print(f"Vector store not initiaized: {self.vectorstore}")
        return ""
    
    def close_vectorstore(self):
        if self.vectorstore:
            try:
                self.vectorstore._client.reset()  # Gracefully shut down Chroma
                print("Chroma vectorstore closed.")
            except Exception as e:
                print(f"Error closing vectorstore: {e}")
            
        




            

    
    


    


