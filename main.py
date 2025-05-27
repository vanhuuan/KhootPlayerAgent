import os
import sys
import time
import traceback
from dotenv import load_dotenv
from output_format.question import Khoot, Question
from selenium_agent import SeleniumKahootAgent
from output_format.answer import AnswerData

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def main():
    # Get game PIN and nickname from environment variables or input
    pin = os.getenv("KAHOOT_PIN")
    nickname = os.getenv("KAHOOT_NICKNAME", "AI_Player")
    
    if not pin:
        pin = input("Enter Kahoot Game PIN: ")
    
    # Initialize Selenium agent
    agent = SeleniumKahootAgent()
    
    try:
        # Setup driver and login to Kahoot
        agent.setup_driver()
        agent.login_to_kahoot(pin, nickname)
        
        # Main game loop
        while True:
            try:
                # Wait for next question
                agent.wait_for_next_question()
                
                # Check if game is finished
                if agent.is_game_finished():
                    print("Game is finished! Thank you for playing.")
                    break
                
                # Check if we're in the lobby
                if agent.is_in_lobby():
                    print("Still in lobby, waiting for game to start...")
                    time.sleep(3)
                    continue
                
                # Extract question
                try:
                    question = agent.get_question_data()
                    if not question:
                        print("Failed to extract question data, waiting for next question...")
                        time.sleep(5)
                        continue
                except Exception as question_error:
                    print(f"Error extracting question: {str(question_error)}")
                    traceback.print_exc()
                    time.sleep(5)
                    continue
                
                # Use early-prepared answer if available
                if agent.early_answer and len(agent.early_answer) > 0:
                    print(f"Using early-prepared answer: {agent.early_answer}")
                    question.answer = agent.early_answer
                    agent.early_answer = None  # Reset for next question
                else:
                    # Get answer from AI
                    try:
                        answer_data = agent.get_answer_from_ai(question)
                        if not answer_data:
                            print("Failed to get answer from AI, using default answer")
                            answer_data = AnswerData(correct_options=["default_answer"], explanation="Error occurred")
                        
                        # Update question with answer
                        question.answer = answer_data.correct_options
                    except Exception as answer_error:
                        print(f"Error getting answer from AI: {str(answer_error)}")
                        traceback.print_exc()
                        # Use a default answer to prevent stopping
                        question.answer = ["default_answer"]
                
                # Enter the answer
                try:
                    agent.enter_answer(question)
                except Exception as enter_error:
                    print(f"Error entering answer: {str(enter_error)}")
                    traceback.print_exc()
                    # Continue to next question
                
                # Sleep to prevent immediate check for next question
                time.sleep(2)
            
            except Exception as loop_error:
                print(f"Error in game loop iteration: {str(loop_error)}")
                traceback.print_exc()
                print("Continuing to next question...")
                time.sleep(5)
                continue
            
    except Exception as e:
        print(f"Critical error in main loop: {str(e)}")
        traceback.print_exc()
    finally:
        # Close browser when done
        try:
            agent.close()
        except Exception as close_error:
            print(f"Error closing browser: {str(close_error)}")

if __name__ == "__main__":
    main()


