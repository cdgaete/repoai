import os
import re
import fnmatch
import string
import chardet
from datetime import datetime
from pathlib import Path
from typing import List, Union, Tuple
from ..utils.logger import get_logger

logger = get_logger(__name__)


def validate_project_path(name: str) -> bool:
    pattern = r'^[a-zA-Z][a-zA-Z0-9_-]{0,253}[a-zA-Z0-9]$'
    return bool(re.match(pattern, name))

def filter_files(files: List[str], omit_patterns: List[str]) -> List[str]:
    return [f for f in files if not should_ignore(f, omit_patterns)]

def should_ignore(file: str, patterns: List[str]) -> bool:
    file = file.rstrip(os.sep)
    file_parts = file.split(os.sep)
    
    for pattern in patterns:
        pattern = pattern.rstrip(os.sep)
        pattern_parts = pattern.split(os.sep)
        
        if match_pattern_parts(file_parts, pattern_parts):
            return True
    
    return False

def match_pattern_parts(file_parts: List[str], pattern_parts: List[str]) -> bool:
    if not pattern_parts:
        return True
    if not file_parts:
        return False
    
    if pattern_parts[0] == '**':
        for i in range(len(file_parts)):
            if match_pattern_parts(file_parts[i:], pattern_parts[1:]):
                return True
        return False
    
    if re.match(fnmatch.translate(pattern_parts[0]), file_parts[0]):
        return match_pattern_parts(file_parts[1:], pattern_parts[1:])
    
    return False

def read_file_sample(filepath: Union[str, Path], sample_size: int = 1024) -> bytes:
    filepath = Path(filepath)
    if not filepath.is_file():
        return b''
    
    try:
        with filepath.open('rb') as file:
            return file.read(sample_size)
    except IOError:
        return b''

def is_binary_signature(data: bytes) -> bool:
    return data.startswith((b'\x00', b'\xFF\xFE', b'\xFE\xFF'))

def is_ascii(data: bytes) -> bool:
    return all(char < 128 for char in data)

def is_utf8(data: bytes) -> bool:
    try:
        data.decode('utf-8')
        return True
    except UnicodeDecodeError:
        return False

def check_chardet_confidence(data: bytes, threshold: float = 0.8) -> bool:
    result = chardet.detect(data)
    return result['encoding'] is not None and result['confidence'] > threshold

def calculate_printable_ratio(data: bytes) -> float:

    printable = set(bytes(string.printable, 'ascii'))
    return sum(byte in printable for byte in data) / len(data)

def is_text_file(filepath: Union[str, Path], sample_size: int = 1024) -> bool:
    raw_data = read_file_sample(filepath, sample_size)
    return is_text_content(raw_data)
    
def is_text_content(content: bytes) -> bool:
    if not content:
        return False

    if is_binary_signature(content):
        return False

    if is_ascii(content) or is_utf8(content):
        return True
    
    if check_chardet_confidence(content):
        return True
    
    if calculate_printable_ratio(content) > 0.7:
        return True
    return False

def extract_paths(text):
    lines = text.strip().split('\n')
    paths = []
    for line in lines:
        paths.append(extract_path_from_textline(line))
    cleaned_paths = sorted(set([path.strip() for path in paths if path.strip()]))
    return cleaned_paths

def extract_path_from_textline(line):
    path_pattern = re.compile(r'^[\w./-]+')
    match = path_pattern.match(line.strip())
    if match:
        return match.group()
    else:
        return ""
    
def yaml_multiline_string_presenter(dumper, data):
    if len(data.splitlines()) > 1:
        # Pyyaml does not allow trailing space at the end of line for block string
        data = '\n'.join([line.rstrip() for line in data.strip().splitlines()])
        # Pyyaml does not allow tab in a block string
        data = data.replace('\t', '    ')
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
        
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

def get_formated_datetime() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


from typing import Dict, Any, List
import re

def lines_lstrip_backticks_with_indices(content: str) -> tuple[List[str], list[int]]:
    lines = content.split('\n')
    processed_lines = []
    backtick_indices = []
    
    for index, line in enumerate(lines):
        stripped_line = line.strip()
        if stripped_line.startswith('```'):
            processed_lines.append(stripped_line)
            backtick_indices.append(index)
        else:
            processed_lines.append(line)
    
    return processed_lines, backtick_indices

def join_split_code(content1: str, content2: str, placeholder: str = "<::PLACEHOLDER::>") -> List[str]:
    processed_content1, _ = lines_lstrip_backticks_with_indices(content1)
    processed_content2, backtick_indices2 = lines_lstrip_backticks_with_indices(content2)
    first_opening_index = backtick_indices2[0]
    content2_part2 = processed_content2[first_opening_index+1:]
    joined_content = processed_content1 + [placeholder] + content2_part2
    return joined_content

def count_triple_backticks_at_line_start(content: str) -> int:
    pattern = re.compile(r'(?m)^```')
    matches = pattern.findall(content)
    return len(matches)

def incomplete_code(content: str):
    return count_triple_backticks_at_line_start(content) % 2 == 1

def join_generated_code(contents: List[str], placeholder: str = "<::PLACEHOLDER::>") -> str:
    joined_content, _ = lines_lstrip_backticks_with_indices(contents[0])
    for content in contents[1:]:
        if incomplete_code("\n".join(joined_content)):
            joined_content = join_split_code("\n".join(joined_content), content, placeholder=placeholder)
        else:
            content_list, _ = lines_lstrip_backticks_with_indices(content)
            joined_content.extend(content_list)
    join_code = "\n".join(joined_content)
    return join_code

def extract_code_blocks(content: str) -> list[Tuple[str, str]]:
    if incomplete_code(content):
        return []
    content_lines, _ = lines_lstrip_backticks_with_indices(content)
    preprocessed_content = "\n".join(content_lines)

    pattern = re.compile(r'```(\w*)\n(.*?)```', re.DOTALL)
    matches = re.findall(pattern, preprocessed_content)
    # list of tuples to list of lists
    return [list(match) for match in matches]

def extract_outer_code_block(content: str):
    # Preprocess the content
    content_lines, _ = lines_lstrip_backticks_with_indices(content)
    preprocessed_content = "\n".join(content_lines)

    if incomplete_code(preprocessed_content):
        return None, None

    start = preprocessed_content.find('```')
    end = preprocessed_content.rfind('```')
    
    if start == -1 or end == -1 or start == end:
        return None, None
    
    # Extract the outer block
    outer_block = preprocessed_content[start:end+3]
    outer_lines = outer_block.split('\n')
    
    # Get the language of the outer block (if specified)
    outer_lang = outer_lines[0][3:].strip()
    
    # Get the content of the outer block
    outer_content = '\n'.join(outer_lines[1:-1])
    
    return outer_lang, outer_content
