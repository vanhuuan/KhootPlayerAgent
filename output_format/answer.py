from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AnswerData(BaseModel):
    correct_options: List[str]