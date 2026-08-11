from dataclasses import dataclass
from datetime import datetime
@dataclass(frozen=True,slots=True)
class RSSEntryDTO:
    title:str; url:str|None; external_id:str|None; summary:str|None; author:str|None; published_at:datetime|None; image_url:str|None
