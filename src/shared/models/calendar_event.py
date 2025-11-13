from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class CalendarEvent:
    id: str
    title: str
    calendar: str
    calendar_type: str
    description: Optional[str]
    location: Optional[str]
    participants: List[str]
    start_ts: str
    end_ts: str

    def to_str(self) -> str:
        parts: List[str] = []
        if self.title: parts.append(self.title)
        if self.description: parts.append(self.description)
        if self.location: parts.append(f"Location: {self.location}")
        if self.participants: parts.append("Participants: " + ", ".join(self.participants))
        if self.start_ts and self.end_ts:
            parts.append(f"Time: {self.start_ts} – {self.end_ts}")
        return " | ".join(parts)
