from enum import Enum

class Messages(Enum):
    # Success messages
    OPERATION_SUCCESS = "Operation completed successfully"
    SAVE_SUCCESS = "Data saved successfully"
    UPDATE_SUCCESS = "Update completed successfully"
    
    # Error messages
    INVALID_INPUT = "Invalid input provided"
    CONNECTION_ERROR = "Unable to establish connection"
    NOT_FOUND = "Resource not found"

    INPUT_NOT_ALLOWED = "input_not_allowed"
    
    # Info messages
    PROCESSING = "Processing your request"
    PLEASE_WAIT = "Please wait while we process your request"
    
    def format(self, *args):
        """Format message with provided arguments"""
        return self.value.format(*args)