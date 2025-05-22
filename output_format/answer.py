from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Step(BaseModel):
    step: int
    instruction: str
    value: Any
    option: Optional[str] = None

class AnswerData(BaseModel):
    answer: List[Step]
    correct_options: List[str]