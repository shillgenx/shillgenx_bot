from enum import Enum
from dataclasses import dataclass, field
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
    tags: List[str] = field(default_factory=list)
    topics: Dict[str, str] = field(default_factory=lambda: {
        'product': '',
        'technology': '',
        'security': '',
        'narrative': '',
        'roadmap': '',
        'use_case': '',
        'community': ''
    })

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

    def set_topics(self, value: Dict[str, str]):
        self.topics = value


@dataclass
class ShillgenXTarget:
    _id: str = ''
    project_id: str = ''
    group_chat_id: str = ''
    x_target_link: str = ''
    lock_duration: int = 1
    goals: Dict[str, int] = field(default_factory=lambda: {
        'comments': 1,
        'reposts': 1,
        'likes': 1,
        'bookmarks': 1
    })

    def set_project_id(self, value: str):
        self.project_id = value

    def set_group_chat_id(self, value: str):
        self.group_chat_id = value

    def set_x_target_link(self, value: str):
        # Assuming the x_target_link should be a valid URL
        if isinstance(value, str) and re.match(r'https?://\S+', value):
            self.x_target_link = value
        else:
            raise ValueError("Invalid X post link.")

    def set_lock_duration(self, value: int):
        if isinstance(value, int) and value > 0:
            self.lock_duration = value
        else:
            raise ValueError("Invalid lock duration, must be a positive number.")

    def set_goals(self, value: Dict[str, int]):
        if isinstance(value, dict) and all(isinstance(k, str) and isinstance(v, int) and v > 0 for k, v in value.items()):
            self.goals = value
        else:
            raise ValueError("Invalid goals.")

    def set_goals(self, value: str):
        if isinstance(value, str):
            # Split the string by commas and convert each part to an integer
            parts = value.split(',')
            if len(parts) == 4:
                try:
                    # Convert string values to integers and validate if they are positive
                    goals_values = [int(part) for part in parts]
                    if all(val > 0 for val in goals_values):
                        # Assign the values to the corresponding goals
                        self.goals = {
                            'comments': goals_values[0],
                            'reposts': goals_values[1],
                            'likes': goals_values[2],
                            'bookmarks': goals_values[3]
                        }
                    else:
                        raise ValueError("All goal values must be positive integers")
                except ValueError:
                    # Raised if conversion to int fails
                    raise ValueError("Invalid input: All values must be integers")
            else:
                raise ValueError("Invalid input: Exactly four comma-separated values are required")
        else:
            raise ValueError("Goals must be provided as a comma-separated string")

@dataclass
class ShillPost:
    _id: str
    shill_target_id: str
    group_chat_id: str
    shill: str

if __name__ == '__main__':
    pass
