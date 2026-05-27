from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SoundChange:
    rule_id: str
    input_pattern: str
    output: str
    environment_left: str
    environment_right: str
    word_boundary_left: bool
    word_boundary_right: bool
    probability: float
    high_frequency_exceptions: List[str]
    description: str


@dataclass
class Era:
    era_id: str
    name: str
    parent_era_id: Optional[str]
    changes: List[SoundChange]
    description: str
