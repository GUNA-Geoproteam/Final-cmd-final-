# alignment_utils.py
import json
from alignment_dictionary import alignment_dict as default_alignment

def load_alignment_dict():
    """
    Loads the alignment dictionary from alignment_dict.json if it exists,
    otherwise returns the default alignment dictionary from alignment_dictionary.py.
    """
    # try:
    with open('alignment_dict.json', 'r') as f:
        alignment_data = json.load(f)
    # except FileNotFoundError:
    #     alignment_data = default_alignment
    return alignment_data
