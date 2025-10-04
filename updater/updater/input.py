import json


def load_extractor_result(file_path):
    """
    Load an ExtractorResult from a JSON file.

    Args:
        file_path (str): Path to the JSON file.

    Returns:
        dict: The parsed ExtractorResult as a Python dictionary.

    Exits:
        Exits the program with code 1 if the file is not found
        or the JSON is invalid.
    """
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"Error reading JSON: {e}")
        exit(1)
