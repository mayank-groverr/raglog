
import re
from pathlib import Path

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



def validate_file_name(path, regex_pattern):
    """
    Function to validate the file name against a regex pattern.
    arguments: file_name: (of type: str), regex_pattern: (of type: str)
    error: ValueError if the file name does not match the regex pattern.
    """
    
    if not isinstance(regex_pattern, str):
        raise ValueError(f"{regex_pattern} must be of type str.")

    if re.match(regex_pattern, path.name):
        return True

    raise ValueError(f"{path.name} does not match the regex pattern {regex_pattern}.")


def check_file_empty(file_path):
    """
    Function to check if the file is empty.
    arguments: file_path: (of type: Path)
    returns: ValueError if the file is empty, False otherwise.
    """
    if file_path.stat().st_size == 0:
        raise ValueError(f"{file_path} has no content.")
    return False


def check_folder_empty(folder_path):
    """
    Function to check if the folder is empty.
    arguments: folder_path: (of type: Path)
    returns: ValueError if the folder is empty, False otherwise.
    """
    if not any(folder_path.iterdir()):
        raise ValueError(f"{folder_path} is empty.")
    return False
    
def parse_file(file_location):
    check_file_empty(file_location)

    print(f"\nParsing file: {file_location}")

    content = file_location.read_text(encoding="utf-8")

    pattern_for_splitting = r"(?=^Rule\s+\d+:)"
    pattern_for_rules = r"^(Rule\s+\d+):\s*(.*)$"

    content = re.split(
        pattern_for_splitting,
        content,
        flags=re.MULTILINE
    )

    parsed_rules = []

    for line in content:
        line = line.replace("\n", " ").strip()

        if len(line) == 0:
            continue

        match = re.match(
            pattern_for_rules,
            line
        )

        if match:
            rule_identifier = match.group(1)
            rule_text = match.group(2)

            print(f"{rule_identifier}: {rule_text}")

            parsed_rules.append(
                (
                    file_location,
                    rule_identifier,
                    rule_text
                )
            )

    return parsed_rules


    

def parse_folder(folder_location, pattern_for_files):
    """
    Function to parse the folder.
    """

    if not isinstance(pattern_for_files, str):
        raise ValueError(
            f"{pattern_for_files} must be of type str."
        )

    check_folder_empty(folder_location)

    files = []

    for file in folder_location.rglob("*"):

        if not file.is_file():
            continue

        try:
            validate_file_name(
                file,
                pattern_for_files,
            )

            files.append(file)

        except ValueError:
            # File doesn't match the required name/extension.
            continue

    if not files:
        raise ValueError(
            f"No valid rule files found in {folder_location} matching the {pattern_for_files} pattern."
        )

    return files

def rules_parser(input_path: str, pattern_for_files: str):
    if not isinstance(input_path, str):    
        raise TypeError("Input path must be a string.")

    path = Path(input_path);
    check_path_exists(path)
    type_of_path = check_is_folder_or_file(path)

    content = []
    if type_of_path == "file" and validate_file_name(path, pattern_for_files):
        content.extend(parse_file(path))
    elif type_of_path == "folder":
        files = parse_folder(path, pattern_for_files)
        for file in files:
            content.extend(parse_file(file))
    return content