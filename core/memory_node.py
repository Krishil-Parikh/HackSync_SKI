"""Memory Node for Mirage Memory System."""

from dataclasses import dataclass, field, asdict
from typing import Dict, List
from datetime import datetime


@dataclass
class MemoryNode:
	"""A single memory node in Mirage's brain."""
	
	id: int
	text: str
	timestamp: str
	concepts: List[str]
	emotions: List[str]
	importance: float
	links: List[int] = field(default_factory=list)
	tier: str = "active"  # active, passive, super_passive
	
	def to_dict(self) -> Dict:
		return asdict(self)
	
	@classmethod
	def from_dict(cls, data: Dict) -> "MemoryNode":
		return cls(**data)
	
	def __str__(self) -> str:
		return (
			f"Node {{\n"
			f"  id: {self.id}\n"
			f"  text: \"{self.text[:50]}{'...' if len(self.text) > 50 else ''}\"\n"
			f"  concepts: {self.concepts}\n"
			f"  emotions: {self.emotions}\n"
			f"  importance: {self.importance:.2f}\n"
			f"  links: {self.links}\n"
			f"  tier: {self.tier}\n"
			f"}}"
		)


def create_timestamp() -> str:
	"""Create current timestamp."""
	return datetime.now().strftime("%H:%M")
