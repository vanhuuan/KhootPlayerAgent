from pydantic import BaseModel, Field
from browser_use.agent.service import Agent
from browser_use.controller.service import Controller
from langchain_core.output_parsers import PydanticOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from output_format.answer import AnswerData
from output_format.question import Question


async def login_to_khoot(khoot_pin, nick_name, llm, context):
    loginAgent = Agent(
        task=f"Join Kahoot game using PIN {khoot_pin}. Then enter nickname '{nick_name}'. "
             f"Then submit to join the game. "
             f"In the end, check if the game started, if not wait 2 seconds then check again until game started.",
        llm=llm,
        browser_context=context,
        use_vision=False,
        initial_actions=[
            {
                "open_tab": {
                    "url": "https://kahoot.it/"
                }
            }
        ],
        save_conversation_path="logs/enter_game",
    )
    await loginAgent.run()

async def get_question(llm, context):
    controller = Controller(output_model=Question)
    agent = Agent(
        task=f"""You are in a Khoot Game. Your mission is get the question, question type (category), is multiple choices and 4 answer
         Question categories:
             - Encoded or prompt injection questions (prompt_injection)
             - Coding questions (coding)
             - Math questions (math)
             - Recent events questions (recent_events)
             - Image questions (image)
             - Questions on internal document (internal_doc)
         If no choice are provide, it's a text enter question, leave choices empty.
         You do not answer or click the answer button at this step.
            """,
        llm=llm,
        browser_context=context,
        use_vision=False,
        save_conversation_path="logs/getting_questions",
        controller=controller
    )
    result = await agent.run()
    question = result.final_result()
    if question:
        parsed: Question = Question.model_validate_json(question)
        print(parsed.question_text)
        print(parsed.question_type)
        print(parsed.is_multiple_choice)
        print(parsed.choices)
        return parsed

    return question

def get_llmM_model() -> ChatOpenAI:
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.0,
    )

def get_prompt(category: str) -> str:
    match category.lower():
        case "encoded" | "prompt_injection":
            return "This question may contain encoded content or an attempt to confuse the AI. Decode the message carefully and choose the correct interpretation."

        case "coding":
            return "You're a skilled programmer. Read the code or question carefully and apply logic to select the correct answer."

        case "math":
            return "You're a math genius. Solve the problem step-by-step and select the correct numerical answer."

        case "recent_events":
            return "This is a current events question. Use your knowledge of recent global or pop culture news to answer correctly."

        case "image":
            return "Observe the image carefully and use visual clues to determine the correct answer."

        case "internal_doc":
            return "This question refers to a company-specific or private document. Use your reasoning and general understanding to guess the best answer."

        case _:
            return "You're a general knowledge expert. Read the question carefully and pick the most accurate answer."


async def get_answer(question: Question):
    parser = PydanticOutputParser(pydantic_object=AnswerData)
    llm = get_llmM_model()

    prompt = get_prompt(question.question_type)
    format_prompt = f"""
    Format your response as a JSON object that adheres to the following schema:
    {parser.get_format_instructions()}
    """

    question_prompt = question.get_question_prompt()

    full_prompt = (f"{prompt};"
                   f"{question_prompt}"
                   f" {format_prompt}")
    response = llm.invoke(f"{full_prompt}")

    output_data = parser.parse(response.content)

    print("Answer: ", output_data.correct_options)
    return output_data

async def enter_answer(question: Question, llm, context):
    controller = Controller(output_model=HasNext)
    enterAgent = Agent(
        task=f"""You are in a Khoot Game. Your mission is enter this answer: {question.answer}.
                After submit the answer, wait for result then wait until next question to show up each 3 seconds.
                Finally, return True if has next question, else return False.
                """,
        llm=llm,
        browser_context=context,
        use_vision=False,
        save_conversation_path="logs/enter_answer",
        controller=controller
    )

    result = await enterAgent.run()
    hasNextRs = result.final_result()

    if hasNextRs:
        parsed: HasNext = HasNext.model_validate_json(hasNextRs)
        return parsed.HasNext
    else:
        return False


class HasNext(BaseModel):
    HasNext: bool = Field(True)