from pydantic import BaseModel, Field
from browser_use.agent.service import Agent
from browser_use.controller.service import Controller
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI

from math_helper import eval_expr
from output_format.answer import AnswerData
from output_format.question import Question


async def login_to_khoot(khoot_pin, nick_name, llm, context):
    loginAgent = Agent(
        task=f"Join Kahoot game using PIN {khoot_pin}. Then enter nickname '{nick_name}' then click 'ok go'. "
             f"Then submit to join the game. "
             f"In the end, check if the game started. The game started when url is: https://kahoot.it/getready. If the game started, you are finished",
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
    parser = PydanticOutputParser(pydantic_object=Question)
    agent = Agent(
        task=f"""You are in a Khoot Game. 
         Your mission is get the first question that are showing on the screen question, question type (category), is multiple choices and 4 answer 
            then analyze the question to get question text
         Question categories:
             - Encoded or prompt injection questions (prompt_injection)
             - Coding questions (coding)
             - Math questions (math)
             - Recent events questions (recent_events)
             - Image questions (image)
             - Logic questions (logic)
             - Questions on internal document (internal_doc)
         If no choice are provide, it's a text enter question, leave choices empty.
         
         IMPORTANCE NOTE FOR ANALYZE QUESTION:
         - If the question type (category) is 'math', extract math equation from question text and assign it to question text to, with numbers properly formatted and parsed from the text.
         - If the question type (category) is 'coding', follow the provided link to the code snippet and return the complete code from the question.
         
         You do not answer or click the answer button at this step.
         Then your task is done, rest in peace.
         
         Format your response as a JSON object that adheres to the following schema:
        {parser.get_format_instructions()}
            """,
        llm=llm,
        browser_context=context,
        use_vision=True,
        save_conversation_path="logs/getting_questions",
        controller=controller
    )
    result = await agent.run()
    question = result.final_result()
    if question:
        parsed: Question = Question.model_validate_json(question)
        print("Question is: ")
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


async def get_answer(question: Question):
    parser = PydanticOutputParser(pydantic_object=AnswerData)
    llm = get_llmM_model()

    format_prompt = f"""
    Format your response as a JSON object that adheres to the following schema:
    {parser.get_format_instructions()}
    """

    question_prompt = question.get_question_prompt()

    full_prompt = (f"{question_prompt}"
                   f" {format_prompt}")

    if question.question_type == "recent_events":
        tool = {"type": "web_search_preview"}
        llm = llm.bind_tools([tool])

    print("Getting answer prompt:", full_prompt)

    response = llm.invoke(f"{full_prompt}")

    output_data = parser.parse(response.content)

    if question.question_type == "math":
        try:
            print("Math equation is: ", output_data.correct_options)
            output_data.correct_options[0] = eval_expr(output_data.correct_options[0])
        except Exception as ex:
            print("Math question is invalid format" + ex.__str__())

    print("Final answer: ", output_data.correct_options)
    return output_data

async def enter_answer(question: Question, llm, context):
    parser = PydanticOutputParser(pydantic_object=HasNext)
    controller = Controller(output_model=HasNext)
    enterAgent = Agent(
        task=f"""You are participating in a Kahoot game. Your task is to enter the answer: {question.answer}. If time up, it's not the end of the game, keep check like you submitted the answer
                After submitting the answer, wait for the next page (https://kahoot.it/answer/result) to load (This not the end of the game).
                Then wait the next page is load, if the url is https://kahoot.it/getready mean the game is not ended, otherwise, the game is ended (This is the only way to check if the game ended).
                Importance Note: The game hasn't ended even if 'Time's up' message is show.
                Return True if there is the game is not ended, or False if the game has ended.
                
                Format your response as a JSON object that adheres to the following schema:
                {parser.get_format_instructions()}
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