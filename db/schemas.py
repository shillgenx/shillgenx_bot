from enum import Enum
from dataclasses import dataclass
from typing import List, Dict

class Schemas(Enum):
    projects = 1
    targets = 2

@dataclass
class Project:
    _id: str
    group_chat_id: str
    name: str
    description: str
    x_handle: str
    telegram: str
    website: str
    tags: List[str]
    topics: Dict[str, str]


@dataclass
class ShillgenXTarget:
    _id: str
    project_id: str
    group_chat_id: str
    x_target_link: str
    lock_duration: int


if __name__ == '__main__':
    pass
