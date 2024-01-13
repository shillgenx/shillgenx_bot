from enum import Enum
from dataclasses import dataclass
from typing import List, Dict

import re

def validate_non_empty_string(value, min_char):
    return isinstance(value, str) and len(value) >= min_char

"""
print(validate_url("example.com"))  # True
print(validate_url("www.example.com"))  # True
print(validate_url("http://www.example.com"))  # True
print(validate_url("https://www.example.com"))  # True
print(validate_url("www.example.com:8080"))  # False
"""
def validate_url(url):
    # Regex for validating a URL with optional scheme and excluding port
    regex = re.compile(
        r'^(?:http://|https://)?'  # Optional http or https scheme
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'  # Domain
        r'(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?))'  # Top level domain
        r'(?:/?|[/?]\S+)?$', re.IGNORECASE)  # Optional rest of the URL
    return re.match(regex, url) is not None

def find_tags_in_string(text):
    # Regular expression to find words prefixed with '$' or '#', followed by word boundaries
    pattern = r'([$#]\w+)\b'
    return re.findall(pattern, text)

class Schemas(Enum):
    projects = 1
    targets = 2

@dataclass
class Project:
    _id: str = ""
    group_chat_id: str = ""
    name: str = ""
    description: str = ""
    x_handle: str = ""
    telegram: str = ""
    website: str = ""
    tags: List[str] = None
    topics: Dict[str, str] = None

    def set_group_chat_id(self, value):
        self.group_chat_id = value

    def set_name(self, value):
        min_char = 4
        if validate_non_empty_string(value, min_char):
            self.name = value
        else:
            raise ValueError(f"Invalid name. Minimum {min_char} characters.")

    def set_description(self, value):
        min_char = 20
        if validate_non_empty_string(value, min_char):
            self.description = value
        else:
            raise ValueError(f"Invalid description. Minimum {min_char} characters.")

    def set_x_handle(self, value):
        min_char = 4
        if validate_non_empty_string(value, min_char):
            if not value.startswith('@'):
                value = '@' + value
            self.x_handle = value
        else:
            raise ValueError(f"Invalid X handle. Minimum {min_char} characters")

    def set_telegram(self, value):
        min_char = 4
        if validate_non_empty_string(value, min_char) and "t.me" in value:
            self.telegram = value
        else:
            raise ValueError("Invalid Telegram invite link.")

    def set_website(self, value):
        if validate_url(value):
            self.website = value
        else:
            raise ValueError("Invalid website URL.")

    def set_tags(self, tags):
        if all((tag.startswith('$') or tag.startswith('#')) and tag.count('$') + tag.count('#') == 1 and ' ' not in tag for tag in tags):
            self.tags = tags
        else:
            raise ValueError("All tags must be single words starting with either '$' or '#'")

    def set_tags_string(self, tags_string):
        tags = find_tags_in_string(tags_string)
        if all((tag.startswith('$') or tag.startswith('#')) and tag.count('$') + tag.count('#') == 1 and ' ' not in tag for tag in tags):
            self.tags = tags
        else:
            raise ValueError("All tags must be single words starting with either '$' or '#'")


@dataclass
class ShillgenXTarget:
    _id: str
    project_id: str
    group_chat_id: str
    x_target_link: str
    lock_duration: int

@dataclass
class ShillPost:
    _id: str
    shill_target_id: str
    group_chat_id: str
    shill: str

if __name__ == '__main__':
    pass
