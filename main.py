import os
import sys

from dotenv import load_dotenv

from agent_step import login_to_khoot, get_question, get_answer, enter_answer
from output_format.question import Question, Khoot

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

from langchain_openai import AzureChatOpenAI, ChatOpenAI

from browser_use import Agent, Browser
from browser_use.agent.service import Agent, Browser, Controller

from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# Retrieve Azure-specific environment variables
# azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
# azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
#
# if not azure_openai_api_key or not azure_openai_endpoint:
#     raise ValueError("AZURE_OPENAI_API_KEY or AZURE_OPENAI_ENDPOINT is not set")

async def main():
    browser = Browser()
    async with await browser.new_context() as context:
        # https://docs.browser-use.com/customize/supported-models
        # Initialize the Azure OpenAI client
        # llm = AzureChatOpenAI(
        #     model_name="gpt-4o-mini",
        #     openai_api_key=azure_openai_api_key,
        #     azure_endpoint=azure_openai_endpoint,  # Corrected to use azure_endpoint instead of openai_api_base
        #     deployment_name="gpt-4o-mini",  # Use deployment_name for Azure models
        #     api_version="2024-08-01-preview",  # Explicitly set the API version here
        # )

        # openAILlm = ChatOpenAI(
        #     model="gpt-4o-mini",
        #     temperature=0.0,
        # )

        llm = ChatGoogleGenerativeAI(model='gemini-2.0-flash-lite')

        khoot_pin = input("Enter Kahoot PIN: ").strip()

        nick_name = '3695'

        # enter the game and wait for it to start
        await login_to_khoot(khoot_pin, nick_name, llm, context)

        khoot_game = Khoot(pin=khoot_pin, username=nick_name)

        question = await get_question(llm, context)

        khoot_game.questions.append(question)

        answer = await get_answer(question)
        question.answer = answer.correct_options

        await enter_answer(question, llm, context)

        input("Press Enter to continue...")
        await browser.close()


asyncio.run(main())


