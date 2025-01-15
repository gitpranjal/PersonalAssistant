from abc import ABC, abstractmethod

class Tool(ABC):
    @abstractmethod
    def handle_tool_call(self, arguments):
        pass

    @abstractmethod
    def get_tool_function_object(self):
        pass

