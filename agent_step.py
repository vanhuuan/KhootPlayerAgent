from langchain_core.prompts import PromptTemplate
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
             f"In the end, check if the game started. The game started when url is: https://kahoot.it/getready. If "
             f"the game started, you are finished",
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
        task=f"""
        Update default wait time to one second
        You are in a Khoot Game. 
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

def get_llm_model(question_type=None):
    """Get appropriate LLM model based on question type"""
    base_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    if question_type == "logic":
        # Wrap with a chain-of-thought template
        cot_prompt = PromptTemplate.from_template("""
        You are a reasoning assistant. Think step-by-step to solve the following problem carefully.

        {input}
        """)
        return cot_prompt | base_llm
    elif question_type == "coding":
        # Enhanced prompt for coding questions
        coding_prompt = PromptTemplate.from_template("""
        You are a programming expert. Analyze the following code question carefully.
        Consider the code structure, syntax, logic, and expected output.
        All answers should be in lowercase for case-insensitive matching.

        {input}
        """)
        return coding_prompt | base_llm
    elif question_type == "encoded":
        # Enhanced prompt for encoded questions
        encoded_prompt = PromptTemplate.from_template("""
        You are analyzing a question that was previously encoded (Base64, URL encoding, etc.).
        The question has been decoded for you. Focus on the decoded content to provide the correct answer.
        All answers should be in lowercase for case-insensitive matching.

        {input}
        """)
        return encoded_prompt | base_llm
    else:
        return base_llm


async def get_answer(question: Question):
    parser = PydanticOutputParser(pydantic_object=AnswerData)
    
    # Convert question text and choices to lowercase for case insensitive handling
    question.question_text = question.question_text.lower()
    question.choices = [choice.lower() for choice in question.choices]
    
    # Handle encoded questions - decode them first
    if question.question_type == "encoded" and question.decoded_text:
        # Use the decoded text for AI processing
        original_text = question.question_text
        question.question_text = question.decoded_text.lower()
        print(f"🔐 Using decoded text for AI: {question.decoded_text}")
    
    llm = get_llm_model(question.question_type)

    format_prompt = f"""
    Format your response as a JSON object that adheres to the following schema:
    {parser.get_format_instructions()}
    
    IMPORTANT: All answers must be in lowercase for case-insensitive matching.
    """

    question_prompt = question.get_question_prompt()

    full_prompt = (f"{question_prompt}"
                   f" {format_prompt}")

    if question.question_type == "recent_events":
        tool = {"type": "web_search_preview"}
        llm = llm.bind_tools([tool])
    elif question.question_type == "coding":
        # Add specific instructions for coding questions
        full_prompt += "\n\nFor coding questions: Analyze the code structure, syntax, and logic. Consider what the code does, its output, or any errors it might have."
    elif question.question_type == "encoded":
        # Add specific instructions for encoded questions
        full_prompt += "\n\nFor encoded questions: The question has been decoded for you. Answer based on the decoded content."

    print("Getting answer prompt:", full_prompt)

    response = llm.invoke(f"{full_prompt}")

    output_data = parser.parse(response.content)

    if question.question_type == "math":
        try:
            print("Math equation is: ", output_data.correct_options)
            output_data.correct_options[0] = eval_expr(output_data.correct_options[0])
        except Exception as ex:
            print("Math question is invalid format" + ex.__str__())
    
    # Ensure all answers are lowercase
    output_data.correct_options = [str(option).lower() for option in output_data.correct_options]

    print("Final answer: ", output_data.correct_options)
    return output_data


async def enter_answer(question: Question, llm, context):
    # parser = PydanticOutputParser(pydantic_object=HasNext)
    # controller = Controller(output_model=HasNext)
    enterAgent = Agent(
        task=f"""Your task is to submit the correct answer: {question.answer}.
                If can't click answer. Mission is completed
                Then you are done. Mission is completed
                Mission is completed.
                """,
        llm=llm,
        browser_context=context,
        use_vision=False,
        save_conversation_path="logs/enter_answer",
        # controller=controller
    )

    result = await enterAgent.run()
    # has_next_rs = result.final_result()
    #
    # if has_next_rs:
    #     parsed: HasNext = HasNext.model_validate_json(has_next_rs)
    #     return parsed.HasNext
    # else:
    #     return False


class HasNext(BaseModel):
    HasNext: bool = Field(True)