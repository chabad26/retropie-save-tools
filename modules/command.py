from dataclasses import dataclass

@dataclass
class Command:
    id: str
    label: str
    icon: str = ""
    description: str = ""
