
import re
import sys
from pathlib import Path

def input_file_location(input_path):
   
    """
    Function to take input and validate if its is path object or not.
    arguments: input_path: (of type: Path)
    error: ValueError if the input is not a valid Path object.
    """
   
    if isinstance(input_path, Path):
        return input_path
    raise ValueError(f"{input_path} is not a valid Path object.")

def check_path_exists(input_path):
    
    """
    Function to check if the input path exists.
    arguments: input_path: (of type: Path)
    error: ValueError if the input path does not exist.
    """
    
    if input_path.exists():
        return True
    raise ValueError(f"{input_path} does not exist.")

def check_is_folder_or_file(input_path):
    
    """
    Function to check if the input is a folder or file.
    arguments: input_path: (of type: Path)
    error: ValueError if the input is not a valid Path object.
    """
    
    if input_path.is_file():
        return "file"
    elif input_path.is_dir():
        return "folder"
    raise ValueError(f"{input_path} is neither a file nor a folder.")



def validate_file_name(file_name, regex_pattern):
    """
    Function to validate the file name against a regex pattern.
    arguments: file_name: (of type: str), regex_pattern: (of type: str)
    error: ValueError if the file name does not match the regex pattern.
    """
    
    if not isinstance(regex_pattern, str):
        raise ValueError(f"{regex_pattern} must be of type str.")

    if re.match(regex_pattern, file_name):
        return True

    raise ValueError(f"{file_name} does not match the regex pattern {regex_pattern}.")

def validate_file_extension(file_location, allowed_extensions):
    
    """
    Function to validate the file extension against a list of allowed extensions.
    arguments: file_location: (of type: Path), allowed_extensions: (of type: list)
    error: ValueError if the file extension is not in the list of allowed extensions.
    """

    if not isinstance(allowed_extensions, list):
        raise ValueError(f"{allowed_extensions} must be of type list.")
    if file_location.suffix in allowed_extensions:
        return True
    raise ValueError(f"{file_location.name} has an invalid extension.")

def validate_name_and_extension(file_location, regex_pattern, allowed_extensions):
    """
    Function to validate the file name and extension.
    arguments: file_location: (of type: Path), regex_pattern: (of type: str), allowed_extensions: (of type: list)
    error: ValueError if the file name does not match the regex pattern or if the file extension is not in the list of allowed extensions.
    """

    validate_file_name(file_location.name, regex_pattern)
    validate_file_extension(file_location, allowed_extensions)
    return True

def check_file_empty(file_path):
    """
    Function to check if the file is empty.
    arguments: file_path: (of type: Path)
    returns: True if the file is empty, False otherwise.
    """
    if file_path.stat().st_size == 0:
        return True
    return False


def check_folder_empty(folder_path):
    """
    Function to check if the folder is empty.
    arguments: folder_path: (of type: Path)
    returns: True if the folder is empty, False otherwise.
    """
    if not any(folder_path.iterdir()):
        return True
    return False
    
def parse_file(file_location, pattern_for_splitting):
    
    """
    Function to parse the file.
    arguments: file_location: (of type: Path), pattern_for_splitting: (of type: str)
    error: ValueError if the file does not exist.
    """

    check_path_exists(file_location)

    if check_file_empty(file_location):
        raise ValueError(f"{file_location} is empty.")

    content = file_location.read_text(encoding='utf-8')
    content = re.split(pattern_for_splitting, content, flags=re.MULTILINE)
    content = [  
        line.replace("\n", " ").strip()
        for line in content
        if len(line) > 0
    ]
    return content


    

def parse_folder(folder_location, pattern_for_files):
    """
    Function to parse the folder.
    arguments: folder_location: (of type: Path), pattern_for_files: (of type: str)
    """


    if not isinstance(pattern_for_files, str):
        raise ValueError(f"{pattern_for_files} must be of type str.")

    if check_folder_empty(folder_location):
        raise ValueError(f"{folder_location} is empty.")
    
    files = [
        file for file in folder_location.rglob("*")
        if file.is_file() and re.match(pattern_for_files, file.name)
    ]

    if not files:
        raise ValueError(f"No valid rule files found in {folder_location}.")
    
    return files


# To be changed
def main():
    """
    Main function to demonstrate the usage of the above functions.
    """
    
    #Path Input from command line argument
    input_path = input_file_location(Path(sys.argv[1]))
    print("Input path:" , input_path)

    # Check if the path exists
    check_path_exists(input_path)

    # check if the path is a folder or file
    path_type = check_is_folder_or_file(input_path)
    print(f"{input_path} is a {path_type}.")


    regex_pattern = r"^exceptions-rule\d*\.txt$"
    
    if path_type == "file" and validate_name_and_extension(input_path, regex_pattern, [".txt"]):
        content = parse_file(input_path, r"(?=^Rule\s+\d+:)")
        print(f"Parsed content from file {input_path}:")
        print(content)
    elif path_type == "folder":
        files = parse_folder(input_path, regex_pattern)
        for file in files:
            content = parse_file(file, r"(?=^Rule\s+\d+:)")
            print(f"Parsed content from file {file}:")
            print(content)


if __name__ == "__main__":
    main()