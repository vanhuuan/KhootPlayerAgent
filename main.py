import os
import sys

from dotenv import load_dotenv
from langchain_core.output_parsers import PydanticOutputParser

from agent_step import login_to_khoot, get_question, get_answer, enter_answer
from output_format.answer import AnswerData
from output_format.question import Question, Khoot

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

from langchain_openai import AzureChatOpenAI, ChatOpenAI

from browser_use.agent.service import Agent, Browser, Controller

load_dotenv()

async def main():
    browser = Browser()
    async with await browser.new_context() as context:

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.0,
        )

        khoot_pin = input("Enter Kahoot PIN: ").strip()

        nick_name = '3695'

        # enter the game and wait for it to start
        await login_to_khoot(khoot_pin, nick_name, llm, context)

        khoot_game = Khoot(pin=khoot_pin, username=nick_name)

        has_next = True

        while has_next:
            print("Getting question")
            question = await get_question(llm, context)
            khoot_game.questions.append(question)

            print("Getting answer")
            answer = await get_answer(question)
            question.answer = answer.correct_options

            print("Enter answer")
            await enter_answer(question, llm, context)

            if "/ranking" in context.current_state.url:
                has_next = False

        input("Press Enter to continue...")
        await browser.close()

asyncio.run(main())


