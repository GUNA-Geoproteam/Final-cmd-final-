# utils.py
import os
import logging

def get_default_output_folder():
    """
    Returns the default output folder located in the user's Documents folder.
    """
    documents_folder = os.path.join(os.path.expanduser("~"), "Documents")
    default_folder = os.path.join(documents_folder, "Extracted_Files")
    os.makedirs(default_folder, exist_ok=True)
    return default_folder

class MockSocketIO:
    """
    A mock implementation of the SocketIO class for testing purposes.
    """
    def emit(self, event, data, broadcast=False):
        logging.info(f"Mock emit: {event}, {data}")
