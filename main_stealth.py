import os
import sys
import time
from dotenv import load_dotenv
from output_format.question import Khoot
from output_format.answer import AnswerData

# Try to import both agents
try:
    from selenium_agent_stealth import StealthKahootAgent
    STEALTH_AVAILABLE = True
except ImportError:
    STEALTH_AVAILABLE = False
    print("Stealth agent not available, install undetected-chromedriver")

from selenium_agent import SeleniumKahootAgent

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

def main():
    print("Kahoot AI Agent - Stealth Mode")
    print("=" * 40)
    
    # Get game PIN and nickname from environment variables or input
    pin = os.getenv("KAHOOT_PIN")
    nickname = os.getenv("KAHOOT_NICKNAME", "AI_Player")
    
    if not pin:
        pin = input("Enter Kahoot Game PIN: ")
    
    # Initialize Selenium agent
    agent = StealthKahootAgent()
    
    try:
        # Setup driver and login to Kahoot
        agent.setup_driver()
        agent.login_to_kahoot(pin, nickname)
        
        # Main game loop
        while True:
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
            question = agent.get_question_data()
            
            # Use early-prepared answer if available
            if hasattr(agent, 'early_answer') and agent.early_answer and len(agent.early_answer) > 0:
                print(f"Using early-prepared answer: {agent.early_answer}")
                question.answer = agent.early_answer
                agent.early_answer = None  # Reset for next question
            else:
                # Get answer from AI
                answer_data = agent.get_answer_from_ai(question)
                
                # Update question with answer
                question.answer = answer_data.correct_options
            
            # Enter the answer
            agent.enter_answer(question)
            
            # Sleep to prevent immediate check for next question
            time.sleep(2)
            
        print(f"\nGame completed! Answered {len(khoot_game.questions)} questions.")
        
        # Show summary
        if khoot_game.questions:
            print("\n--- Game Summary ---")
            for i, q in enumerate(khoot_game.questions, 1):
                print(f"Q{i}: {q.question_text[:50]}...")
                print(f"     Answer: {q.answer}")
                print(f"     Type: {q.question_type}")
        
        input("Press Enter to close browser...")
        
    except Exception as e:
        print(f"Error in main loop: {e}")
    finally:
        # Close browser when done
        agent.close()

if __name__ == "__main__":
    main() 