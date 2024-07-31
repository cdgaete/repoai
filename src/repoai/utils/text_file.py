import string
import chardet
from ..config import Config

def is_text_file(filepath, sample_size=Config.SAMPLE_SIZE_FOR_TEXT_DETECTION):
    """
    Check if a file is likely to be a text file.
    
    :param filepath: Path to the file to check
    :param sample_size: Number of bytes to check (default from Config)
    :return: True if the file is likely to be text, False otherwise
    """
    try:
        with open(filepath, 'rb') as file:
            raw_data = file.read(sample_size)
        
        if not raw_data:
            return False

        # Check if file is ASCII
        if all(char < 128 for char in raw_data):
            return True
        
        # Check if file is UTF-8 without BOM
        try:
            raw_data.decode('utf-8')
            return True
        except UnicodeDecodeError:
            pass
        
        # Check for UTF-8 BOM
        if raw_data.startswith(b'\xef\xbb\xbf'):
            return True
        
        # Use chardet to detect encoding
        result = chardet.detect(raw_data)
        if result['encoding'] is not None:
            confidence = result['confidence']
            # Consider it text if confidence is high
            if confidence > Config.CHARDET_CONFIDENCE_THRESHOLD:
                return True
        
        # Check the percentage of printable characters
        printable = set(bytes(string.printable, 'ascii'))
        printable_ratio = sum(byte in printable for byte in raw_data) / len(raw_data)
        if printable_ratio > Config.PRINTABLE_RATIO_THRESHOLD:
            return True
        
        return False
    except IOError:
        return False

# Example usage
if __name__ == "__main__":
    file_path = "path/to/your/file"
    if is_text_file(file_path):
        print(f"{file_path} is likely a text file.")
    else:
        print(f"{file_path} is likely not a text file.")