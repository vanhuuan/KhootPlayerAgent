from pydantic import BaseModel, Field, validator
from typing import List, Literal


class Question(BaseModel):
    question_text: str = Field()
    choices: List[str] = Field()
    answer: List[str] = Field()
    is_multiple_choice: bool = Field()
    question_type: Literal["prompt_injection", "coding", "math", "recent_events", "image", "internal_doc", "logic"] = "logic"

    def get_correct_answer(self) -> List[str]:
        return self.answer

    def get_question_prompt(self) -> str:
        base_prompt = f"📢 **Category**: {self.question_type.replace('_', ' ').title()}\n"
        base_prompt += f"**Question**: {self.question_text}\n\n"

        if self.question_type == "math":
            base_prompt = (f"\n🧮 Extract math equation from this: {self.question_text}. "
                           f"IMPORTANCE NOTE: Ignore all calculate result")
            return base_prompt

        for i, choice in enumerate(self.choices):
            base_prompt += f"Option {i + 1}. {choice}\n"

        match self.question_type:
            case "prompt_injection":
                base_prompt += "\n⚠️ Be careful—this might be a trick or injection test. Think twice before answering."
            case "coding":
                base_prompt += "\n💻 Use your programming knowledge to pick the right answer."
            case "recent_events":
                base_prompt += "\n📰 Pick the answer based on recent real-world knowledge."
            case "image":
                base_prompt += "\n🖼️ Consider the visual context if an image is involved."
            case "internal_doc":
                base_prompt += "\n📄 Use info that might be from internal documents or context."
            case "logic":
                base_prompt += "\n📄 Use your all of your intelligent to solve this logic question."

        if self.is_multiple_choice and len(self.choices) > 0:
            base_prompt += "\n\n✅ This is a **multiple choice** question. Select all correct answers."
        elif len(self.choices) > 0:
            base_prompt += "\n\n✅ This is a **single choice** question. Pick the one best answer."
        else:
            base_prompt += "\n\n✅ This is a **text** question. Give me the correct answer and make it short."

        return base_prompt


class Khoot(BaseModel):
    questions: List[Question] = Field(default_factory=list)
    pin: str
    username: str

    def add_question(self, question: Question) -> None:
        self.questions.append(question)

    def get_question_by_index(self, index: int) -> Question | None:
        if 0 <= index < len(self.questions):
            return self.questions[index]
        return None

    def total_questions(self) -> int:
        return len(self.questions)

    def summary(self) -> str:
        return f"Kahoot Game PIN: {self.pin} | Player: {self.username} | Total Questions: {len(self.questions)}"