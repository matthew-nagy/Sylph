from dataclasses import dataclass


MAX_ERRORS = 20

@dataclass
class SourceInfo:
    source_name: str
    line_number: int
    column_number: int

class CompileError(Exception):
    def __init__(self, message, location):
        self.message = message
        self.location = location
        super().__init__(str(location) + " Uncaught Compiler Error: " + self.message)

class RuntimeError(Exception):
    def __init__(self, message, location):
        self.message = message
        self.location = location
        super().__init__(str(location) + " Internal Runtime Error: " + self.message)

def orError(func):
    def wrapper(*args, **kwargs):
        result = None
        try:
            result = func(*args, **kwargs)
        except CompileError as cError:
            result = cError
        return result
    return wrapper

def orErrorMethod(func):
    def wrapper(self, *args, **kwargs):
        result = None
        try:
            result = func(self, *args, **kwargs)
        except CompileError as cError:
            result = cError
        return result
    return wrapper