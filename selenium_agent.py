import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from output_format.question import Question
from output_format.answer import AnswerData
from math_helper import eval_expr
from encoding_helper import handle_encoded_question
import re


class SeleniumKahootAgent:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
        self.early_answer = None  # Add this to store early answer
        
    def setup_driver(self):
        """Initialize Chrome driver with appropriate options"""
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Additional anti-detection measures
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Execute script to hide webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Add additional stealth measures
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        self.wait = WebDriverWait(self.driver, 10)
        
    def check_for_gameblock(self):
        """Check if we're on the gameblock page - this is actually the main game page"""
        try:
            current_url = self.driver.current_url
            if "gameblock" in current_url:
                print("✅ On gameblock page - this is the main game interface")
                return False  # Not actually blocked, this is the game page
                    
            return False  # Not on gameblock page
            
        except Exception as e:
            print(f"Error checking URL: {e}")
            return False
        
    def login_to_kahoot(self, pin: str, nickname: str):
        """Login to Kahoot game"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Navigate to Kahoot
                self.driver.get("https://kahoot.it/")
                time.sleep(3)  # Wait for page to load
                
                # Add human-like delay
                time.sleep(2)
                
                # Try multiple selectors for PIN input
                pin_input = None
                pin_selectors = [
                    "input[data-functional-selector='game-id-input']",
                    "input[placeholder*='PIN']",
                    "input[placeholder*='Game PIN']",
                    "#game-input",
                    "input[type='text']"
                ]
                
                for selector in pin_selectors:
                    try:
                        pin_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        break
                    except:
                        continue
                
                if not pin_input:
                    raise Exception("Could not find PIN input field")
                
                # Type PIN slowly to mimic human behavior
                pin_input.clear()
                for char in pin:
                    pin_input.send_keys(char)
                    time.sleep(0.1)  # Small delay between keystrokes
                
                time.sleep(1)
                
                # Try multiple selectors for enter/submit button
                enter_button = None
                enter_selectors = [
                    "button[data-functional-selector='join-game-pin']",
                    "button[type='submit']",
                    "//button[contains(text(), 'Enter')]",
                    "//button[contains(@class, 'enter')]",
                    "//button[contains(@class, 'submit')]"
                ]
                
                for selector in enter_selectors:
                    try:
                        if selector.startswith("//"):
                            enter_button = self.driver.find_element(By.XPATH, selector)
                        else:
                            enter_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if enter_button.is_displayed() and enter_button.is_enabled():
                            break
                    except:
                        continue
                
                if not enter_button:
                    # Try pressing Enter key instead
                    from selenium.webdriver.common.keys import Keys
                    pin_input.send_keys(Keys.RETURN)
                else:
                    enter_button.click()
                
                time.sleep(3)
                
                # Try multiple selectors for nickname input
                nickname_input = None
                nickname_selectors = [
                    "input[data-functional-selector='nickname-input']",
                    "input[placeholder*='nickname']",
                    "input[placeholder*='Nickname']",
                    "#nickname",
                    "input[type='text']"
                ]
                
                for selector in nickname_selectors:
                    try:
                        nickname_input = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        break
                    except:
                        continue
                
                if not nickname_input:
                    raise Exception("Could not find nickname input field")
                
                # Type nickname slowly
                nickname_input.clear()
                for char in nickname:
                    nickname_input.send_keys(char)
                    time.sleep(0.1)
                
                time.sleep(1)
                
                # Try multiple selectors for OK/Go button
                ok_button = None
                ok_selectors = [
                    "button[data-functional-selector='join-game-nickname']",
                    "//button[contains(text(), 'OK')]",
                    "//button[contains(text(), 'Go')]",
                    "//button[contains(text(), 'Join')]",
                    "//button[contains(@class, 'ok')]",
                    "//button[contains(@class, 'join')]",
                    "button[type='submit']"
                ]
                
                for selector in ok_selectors:
                    try:
                        if selector.startswith("//"):
                            ok_button = self.driver.find_element(By.XPATH, selector)
                        else:
                            ok_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if ok_button.is_displayed() and ok_button.is_enabled():
                            break
                    except:
                        continue
                
                if not ok_button:
                    # Try pressing Enter key instead
                    from selenium.webdriver.common.keys import Keys
                    nickname_input.send_keys(Keys.RETURN)
                else:
                    ok_button.click()
                
                # Wait for game to start - be more flexible with URL checking
                print("Waiting for game to start...")
                start_time = time.time()
                while time.time() - start_time < 30:  # Wait up to 30 seconds
                    current_url = self.driver.current_url
                    
                    # gameblock is actually the main game page
                    if any(keyword in current_url for keyword in ["getready", "game", "question", "lobby", "gameblock"]):
                        print("Successfully joined Kahoot game!")
                        print(f"Current URL: {current_url}")
                        return
                    time.sleep(2)  # Check every 2 seconds
                
                # If we get here, check if we're still on the join page
                if "kahoot.it" in self.driver.current_url:
                    print("Still on join page, game might not have started yet")
                    print("Current URL:", self.driver.current_url)
                    return  # Consider this a success, wait for game to start
                
            except Exception as e:
                print(f"Error logging into Kahoot (attempt {retry_count + 1}): {e}")
                print(f"Current URL: {self.driver.current_url}")
                retry_count += 1
                if retry_count < max_retries:
                    print(f"Retrying in 5 seconds... ({retry_count}/{max_retries})")
                    time.sleep(5)
                else:
                    print("Page source preview:")
                    print(self.driver.page_source[:500])
                    raise
            
    def get_question_data(self) -> Question:
        """Extract question data from the current page"""
        try:
            # Wait for question to load
            time.sleep(2)
            
            # Get question text
            question_text = self._extract_question_text()
            if not question_text:
                raise Exception("Could not find question text")
            
            # Convert question text to lowercase
            question_text = question_text.lower()
            
            # Get answer choices and selectors
            choices, answer_selectors = self._extract_answer_choices()
            
            # Format choices with their indices
            formatted_choices = []
            for i, choice in enumerate(choices):
                formatted_choices.append(f"Option {i+1}: {choice}")

            question_text = self._extract_code_from_url(question_text)
            
            # Determine question type based on content
            question_type = self._classify_question(question_text, choices)
            
            # Handle encoded questions
            decoded_text = None
            if question_type == "encoded":
                decoded_text, encoding_type = handle_encoded_question(question_text)
                if encoding_type != "none":
                    print(f"✅ Successfully decoded {encoding_type} question")
                else:
                    print("❌ Could not decode question, treating as regular text")
                    question_type = "logic"  # Fallback to logic if decoding fails
            
            # Check if multiple choice
            is_multiple_choice = len(choices) > 1
            
            # Store the metadata for answer selectors separately from the question text
            metadata = ""
            if answer_selectors:
                metadata = "\n\nAnswer selectors:"
                for i, selector in enumerate(answer_selectors):
                    if selector:
                        metadata += f"\n  {i}: {selector}"
            
            question = Question(
                question_text=question_text,  # Add metadata but keep it separate from question content
                choices=formatted_choices,  # Use formatted choices with indices
                answer=[],  # Will be filled later
                is_multiple_choice=is_multiple_choice,
                question_type=question_type,
                decoded_text=decoded_text
            )
            
            # Handle image questions - capture screenshot
            if question_type == "image":
                question.image_data = self._capture_question_image()
            
            print(f"Question extracted: {question_text[:50]}...")
            print(f"Choices: {choices}")
            print(f"Type: {question_type}")
            
            return question
            
        except Exception as e:
            print(f"Error extracting question: {e}")
            raise
            
    def _extract_question_text(self):
        """Extract question text from the page"""
        # Try multiple selectors for question text
        question_selectors = [
            "[data-functional-selector='block-title']",
            "[data-functional-selector='question-title']", 
            "h1",
            ".question-title",
            ".block-title",
            "[class*='question']",
            "[class*='title']"
        ]
        
        for selector in question_selectors:
            try:
                question_element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                text = question_element.text.strip()
                if text:
                    return text
            except:
                continue
        
        # Try XPath selectors as fallback
        xpath_selectors = [
            "//h1",
            "//div[contains(@class, 'question')]//span",
            "//div[contains(@class, 'title')]",
            "//*[contains(text(), '?')]"
        ]
        
        for xpath in xpath_selectors:
            try:
                question_element = self.driver.find_element(By.XPATH, xpath)
                text = question_element.text.strip()
                if text and len(text) > 5:  # Ensure it's substantial text
                    return text
            except:
                continue
                
        return ""
        
    def _extract_answer_choices(self):
        """Extract answer choices and their selectors"""
        choices = []
        answer_selectors = []
        
        # Try Kahoot-specific question choice pattern first
        kahoot_choice_selectors = [
            "[data-functional-selector='question-choice-text-0']",
            "[data-functional-selector='question-choice-text-1']",
            "[data-functional-selector='question-choice-text-2']",
            "[data-functional-selector='question-choice-text-3']"
        ]
        
        # Answer button selectors
        button_selectors = [
            "[data-functional-selector='answer-0']",
            "[data-functional-selector='answer-1']",
            "[data-functional-selector='answer-2']",
            "[data-functional-selector='answer-3']"
        ]
        
        # Try Kahoot-specific pattern first
        kahoot_elements_found = False
        for i, selector in enumerate(kahoot_choice_selectors):
            try:
                element = self.driver.find_element(By.CSS_SELECTOR, selector)
                if element:
                    element_text = element.text.strip().lower()
                    
                    # Find the corresponding button
                    try:
                        button_selector = button_selectors[i]
                        button = self.driver.find_element(By.CSS_SELECTOR, button_selector)
                        if button:
                            answer_selectors.append(button_selector)
                    except:
                        answer_selectors.append(None)
                    
                    choices.append(f"{element_text}")
                    kahoot_elements_found = True
            except:
                continue
                
        # If Kahoot-specific elements not found, try generic approach
        if not kahoot_elements_found:
            # Try to find buttons/choices with various selectors
            elements = []
            
            # List of selectors to try, in order of preference
            selectors = [
                "button[data-functional-selector^='answer-']",
                "button[class*='answer']",
                ".answer-button",
                ".choice-container",
                "[class*='choice']",
                "button[aria-label*='Answer']",
                "//button[contains(@class, 'answer')]",
                "//div[contains(@class, 'choice')]"
            ]
            
            # Try each selector until we find elements (max 4)
            for selector in selectors:
                try:
                    if selector.startswith("//"):
                        found_elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        found_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        
                    if found_elements and len(found_elements) > 0:
                        elements.extend(found_elements[:4])
                        if len(elements) >= 4:
                            break
                except:
                    continue
            
            # Process found elements (limit to 4)
            for i, element in enumerate(elements[:4]):
                try:
                    element_text = element.text.strip().lower()
                    func_selector = element.get_attribute("data-functional-selector") or ""
                    
                    # Store selector for this answer button
                    if func_selector:
                        answer_selectors.append(func_selector)
                    else:
                        answer_selectors.append(f"//button[position()={i+1}]")
                    
                    if element_text:
                        choices.append(f"{element_text}")
                    else:
                        choices.append(f"Option {i+1}")
                except:
                    choices.append(f"Option {i+1}")
                    answer_selectors.append(None)
                    continue
        
        # Ensure we only have the first 4 options
        return choices[:4], answer_selectors[:4]
        
    def _classify_question(self, question_text: str, choices: list) -> str:
        """Classify question type using AI"""
        # First check for images on the page (this can't be done by AI)
        try:
            images = self.driver.find_elements(By.TAG_NAME, "img")
            # Look for substantial images (not just icons)
            for img in images:
                if img.is_displayed():
                    width = img.size.get('width', 0)
                    height = img.size.get('height', 0)
                    if width > 100 and height > 100:  # Substantial image
                        print(f"🖼️ Found substantial image: {width}x{height}")
                        return "image"
        except:
            pass
        
        # Use AI to classify the question
        try:
            prompt = f"""
            Classify the following question into one of these categories:
            - prompt_injection: questions trying to manipulate AI systems
            - coding: questions about programming or code
            - math: mathematical calculations or equations
            - recent_events: questions about current events or recent happenings
            - image: questions referring to visual elements
            - internal_doc: questions referring to internal documentation
            - logic: general knowledge or logical reasoning questions
            - encoded: questions with encoded text (base64, ROT13, etc.)
            
            Question: {question_text}
            
            Choices:
            {', '.join(choices) if choices else 'No choices provided'}
            
            Return ONLY the category name without any explanation.
            """
            
            response = self.llm.invoke(prompt)
            classification = response.content.strip().lower()
            
            # Ensure classification is one of the valid types
            valid_types = ["prompt_injection", "coding", "math", "recent_events", 
                          "image", "internal_doc", "logic", "encoded"]
            
            if classification in valid_types:
                print(f"🧠 AI classified question as: {classification}")
                return classification
            else:
                return self._rule_based_classification(question_text)
                
        except Exception as e:
            print(f"Error in AI classification: {e}")
            return self._rule_based_classification(question_text)
            
    def _rule_based_classification(self, question_text):
        """Fallback rule-based classification for when AI is not available"""
        question_lower = question_text.lower()
        
        # Dictionary mapping patterns to question types
        patterns = {
            "encoded": ['encoded', 'base64', 'decode', 'cipher', 'encrypt', 'rot13', 'ascii'],
            "math": ['calculate', 'solve', '+', '-', '*', '/', '=', 'equation', 'sum', 'difference', 'product'],
            "coding": ['code', 'function', 'variable', 'programming', 'algorithm', 'javascript', 'python', 'java'],
            "recent_events": ['recent', 'news', '2023', '2024', '2025', 'current', 'latest', 'today'],
            "image": ['image', 'picture', 'photo', 'visual', 'see', 'shown', 'displayed', 'screen'],
            "prompt_injection": ['ignore', 'prompt', 'system', 'instruction', 'important', 'forget', 'context']
        }
        
        # Check each pattern set
        for qtype, keywords in patterns.items():
            if any(keyword in question_lower for keyword in keywords):
                print(f"Rule-based classification: {qtype}")
                return qtype
        
        # Default to logic if no patterns match
        return "logic"
        
    def get_answer_from_ai(self, question: Question) -> AnswerData:
        """Get answer from AI model"""
        try:
            # Convert question text and choices to lowercase for case insensitive handling
            question.question_text = question.question_text.lower()
            question.choices = [choice.lower() for choice in question.choices]
            
            parser = PydanticOutputParser(pydantic_object=AnswerData)
            
            format_prompt = f"""
            Format your response as a JSON object that adheres to the following schema:
            {parser.get_format_instructions()}
            
            IMPORTANT: All answers must be in lowercase for case-insensitive matching.
            """
            
            question_prompt = question.get_question_prompt()
            full_prompt = f"{question_prompt}\n{format_prompt}"
            
            # Select appropriate LLM based on question type
            llm = self._get_specialized_llm(question.question_type)
            
            # Handle image questions with vision model
            if question.question_type == "image" and question.image_data:
                response = self._get_vision_answer(question, full_prompt)
            else:
                # Call the specialized LLM function directly
                response = llm(full_prompt)
            
            output_data = parser.parse(response.content)
            
            # Handle math questions
            if question.question_type == "math":
                try:
                    print(f"Math equation: {output_data.correct_options}")
                    output_data.correct_options[0] = str(eval_expr(output_data.correct_options[0]))
                except Exception as ex:
                    print(f"Math question invalid format: {ex}")
            
            # Post-process answers to handle "option X" format
            processed_options = []
            for option in output_data.correct_options:
                option_str = str(option).lower()
                
                # Extract just the number if it says "option X"
                if "option" in option_str:
                    import re
                    # Try to extract just the number
                    number_match = re.search(r'\d+', option_str)
                    if number_match:
                        option_str = number_match.group(0)
                
                processed_options.append(option_str)
            
            # Replace with processed options
            output_data.correct_options = processed_options
            
            print(f"AI Answer: {output_data.correct_options}")
            return output_data
            
        except Exception as e:
            print(f"Error getting AI answer: {e}")
            raise
            
    def _get_specialized_llm(self, question_type, prompt=None):
        """Get appropriate LLM model based on question type"""
        base_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
        
        if question_type == "logic":
            # Improved logic question prompt with better answer format instructions
            cot_prompt = PromptTemplate.from_template("""
            You are a reasoning assistant. Think step-by-step to solve the following problem carefully.
            
            IMPORTANT ANSWER FORMAT INSTRUCTIONS:
            1. For multiple choice questions, provide ONLY the number or letter of the correct option.
            2. Do NOT include the word "option" in your answer - just return "1", "2", "3", or "4".
            3. If the answer is a specific value, provide only that value.
            4. All answers must be in lowercase for case-insensitive matching.
            
            {input}
            """)
            # Return a callable that will format the prompt then call the LLM
            return lambda p: base_llm.invoke(cot_prompt.format(input=p))
            
        elif question_type == "coding":
            # Enhanced prompt for coding questions
            coding_prompt = PromptTemplate.from_template("""
            You are a programming expert. Analyze the following code question carefully.
            Consider the code structure, syntax, logic, and expected output.
            All answers should be in lowercase for case-insensitive matching.

            {input}
            """)
            return lambda p: base_llm.invoke(coding_prompt.format(input=p))
            
        elif question_type == "math":
            # Enhanced prompt for math questions
            math_prompt = PromptTemplate.from_template("""
            You are a mathematics expert. Solve the following problem step-by-step.
            Show your work and provide the exact numerical answer.
            If the answer is a number, provide it directly without words.
            All answers should be in lowercase for case-insensitive matching.

            {input}
            """)
            return lambda p: base_llm.invoke(math_prompt.format(input=p))
            
        elif question_type == "encoded":
            # Enhanced prompt for encoded questions
            encoded_prompt = PromptTemplate.from_template("""
            You are analyzing a question that was previously encoded (Base64, URL encoding, etc.).
            The question has been decoded for you. Focus on the decoded content to provide the correct answer.
            All answers should be in lowercase for case-insensitive matching.

            {input}
            """)
            return lambda p: base_llm.invoke(encoded_prompt.format(input=p))
            
        elif question_type == "recent_events":
            # Enhanced prompt for recent events questions
            events_prompt = PromptTemplate.from_template("""
            You are a current events expert. Answer the following question about recent happenings.
            Be factual and precise. If you're uncertain, indicate the most likely answer based on recent events.
            All answers should be in lowercase for case-insensitive matching.

            {input}
            """)
            return lambda p: base_llm.invoke(events_prompt.format(input=p))
            
        else:
            # Default case - use base LLM directly
            return base_llm
            
    def enter_answer(self, question: Question):
        """Enter the answer by clicking the appropriate choice"""
        try:
            if not question.answer:
                print("No answer to enter")
                return
                
            print(f"Trying to click answer: {question.answer}")
            
            # Extract answer selectors if available in question text
            answer_selectors = {}
            selector_pattern = r'(\d+): (\[data-functional-selector=[\'"].*?[\'"]\]|//.*)'
            question_text = question.question_text
            
            # Extract selectors from question text if present
            selector_matches = re.findall(selector_pattern, question_text)
            if selector_matches:
                for index, selector in selector_matches:
                    answer_selectors[int(index)] = selector
            
            # Find and click the correct answer
            for answer in question.answer:
                clicked = False
                answer_lower = answer.lower()  # Convert to lowercase for comparison
                
                # STRATEGY 0: Find position of answer in choices (most accurate approach)
                answer_position = self._find_answer_position(answer_lower, question.choices)
                if answer_position is not None:
                    print(f"Found answer '{answer_lower}' at position {answer_position}")
                    try:
                        selector = f"[data-functional-selector='answer-{answer_position}']"
                        answer_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if answer_button.is_displayed():
                            answer_button.click()
                            print(f"Clicked answer at position {answer_position} using selector: {selector}")
                            clicked = True
                            break
                    except Exception as e:
                        print(f"Error clicking position-based selector: {e}")
                
                if clicked:
                    break
                
                # STRATEGY 1: Use Kahoot-specific selectors with answer index
                if answer_lower.isdigit() and 0 <= int(answer_lower) < 4:
                    choice_index = int(answer_lower)
                    
                    # First try text matching to find which button contains this value
                    answer_text_match_found = False
                    for i in range(4):  # Try all 4 possible answer positions
                        try:
                            text_selector = f"[data-functional-selector='question-choice-text-{i}']"
                            text_element = self.driver.find_element(By.CSS_SELECTOR, text_selector)
                            if text_element and answer_lower in text_element.text.strip().lower():
                                # Found the element with matching text
                                button_selector = f"[data-functional-selector='answer-{i}']"
                                button = self.driver.find_element(By.CSS_SELECTOR, button_selector)
                                if button.is_displayed():
                                    button.click()
                                    print(f"Clicked answer by text match at position {i}: {button_selector}")
                                    clicked = True
                                    answer_text_match_found = True
                                    break
                        except:
                            continue
                    
                    if answer_text_match_found:
                        break
                    
                    # 1a: Use extracted selector if available
                    if choice_index in answer_selectors:
                        selector = answer_selectors[choice_index]
                        try:
                            if selector.startswith("//"):  # XPath
                                answer_button = self.driver.find_element(By.XPATH, selector)
                            else:  # CSS selector
                                answer_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                                
                            if answer_button.is_displayed():
                                answer_button.click()
                                print(f"Clicked answer using selector: {selector}")
                                clicked = True
                                break
                        except Exception as e:
                            pass
                    
                    # 1b: Try using direct answer-N selector
                    if not clicked:
                        try:
                            selector = f"[data-functional-selector='answer-{choice_index}']"
                            answer_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                            if answer_button.is_displayed():
                                answer_button.click()
                                print(f"Clicked answer using data-functional-selector: answer-{choice_index}")
                                clicked = True
                                break
                        except:
                            pass
                        
                    # 1c: Try using question-choice-text-N selector
                    if not clicked:
                        try:
                            choice_selector = f"[data-functional-selector='question-choice-text-{choice_index}']"
                            choice_element = self.driver.find_element(By.CSS_SELECTOR, choice_selector)
                            
                            if choice_element:
                                # Try clicking element directly
                                try:
                                    choice_element.click()
                                    print(f"Clicked Kahoot choice element directly: {choice_selector}")
                                    clicked = True
                                    break
                                except:
                                    # Try to find and click parent button
                                    try:
                                        parent_element = choice_element.find_element(By.XPATH, "./..")
                                        # Keep going up until we find a button or clickable element
                                        attempts = 0
                                        while parent_element and attempts < 5:
                                            try:
                                                parent_element.click()
                                                print(f"Clicked parent of choice element (level {attempts})")
                                                clicked = True
                                                break
                                            except:
                                                try:
                                                    parent_element = parent_element.find_element(By.XPATH, "./..")
                                                    attempts += 1
                                                except:
                                                    break
                                    except:
                                        pass
                        except:
                            pass
                
                if clicked:
                    break
                
                # Continue with other strategies...
                # [rest of the method unchanged]
            
            # Wait for the answer to register
            time.sleep(2)
            
        except Exception as e:
            print(f"Error entering answer: {e}")
            print(f"Current URL: {self.driver.current_url}")
            
    def _find_answer_position(self, answer_text, choices):
        """Find the position of an answer in the list of choices"""
        try:
            # For numerical answers, try to find the exact match
            for i, choice in enumerate(choices):
                choice_lower = choice.lower()
                
                # Extract just the text part from "Option N: text"
                if ":" in choice_lower:
                    choice_text = choice_lower.split(":", 1)[1].strip()
                else:
                    choice_text = choice_lower
                
                # Check for exact match
                if choice_text == answer_text:
                    return i
                
                # Check if choice contains the answer (for numerical answers)
                if answer_text.isdigit() and answer_text in choice_text.split():
                    return i
            
            # If no match found
            return None
        except:
            return None
            
    def is_game_finished(self) -> bool:
        """Check if the game has finished"""
        try:
            return "/ranking" in self.driver.current_url or "podium" in self.driver.current_url
        except:
            return False
            
    def wait_for_next_question(self):
        """Wait for the next question to appear and prepare answer if possible"""
        try:
            print("Waiting for next question...")
            start_time = time.time()
            self.early_answer = None  # Store early answer here
            
            while time.time() - start_time < 120:  # Wait up to 2 minutes
                current_url = self.driver.current_url
                
                # Check if game is finished
                if self.is_game_finished():
                    print("Game finished detected")
                    return
                
                # Check if we're viewing answer results
                if "answer/result" in current_url or "/result" in current_url:
                    print("📊 Viewing answer results - waiting for next question...")
                    time.sleep(2)  # Check every 2 seconds
                    continue
                
                # First check if an active question is already visible
                # If a question with answer options is already visible, return immediately
                if self._check_for_active_question(current_url, []):
                    print("Full question with answer options already visible")
                    return
                
                # Check for "get ready" page - this appears before the question
                get_ready_indicators = [
                    "Get ready", "get ready", "question countdown",
                    "countdown", "loading question", "ready", "up next"
                ]
                
                page_text = self.driver.page_source.lower()
                page_title = self._extract_potential_question_title()
                
                # Try to prepare early answer if we're on the "get ready" page
                # AND no answer buttons are visible yet
                is_get_ready = any(indicator in page_text for indicator in get_ready_indicators)
                answer_buttons_visible = self._are_answer_buttons_visible()
                
                if is_get_ready and page_title and not answer_buttons_visible:
                    print(f"🔍 On 'get ready' page with potential question: {page_title}")
                    self._prepare_early_answer(page_title)
                    time.sleep(1)
                    continue
                
                # If answer buttons are visible, we're on the actual question
                if answer_buttons_visible:
                    print("Answer buttons visible - question is ready")
                    return
                
                # Check for lobby/waiting messages (not questions)
                lobby_indicators = [
                    "You're in! See your nickname on screen?",
                    "you're in", "see your nickname",
                    "waiting for", "get ready", "starting soon"
                ]
                
                is_in_lobby = any(indicator in page_text for indicator in lobby_indicators)
                if is_in_lobby:
                    print("In lobby/waiting area - waiting for game to start...")
                    time.sleep(2)
                    continue
                
                # Check for question indicators one more time
                if self._check_for_active_question(current_url, lobby_indicators):
                    time.sleep(1)  # Brief wait for content to load
                    return
                
                time.sleep(1)  # Check more frequently
            
            print("Timeout waiting for next question")
            
        except Exception as e:
            print(f"Error waiting for next question: {e}")
    
    def _extract_potential_question_title(self):
        """Extract potential question title from current page"""
        try:
            title_selectors = [
                "h1", "h2", ".title", "[class*='title']", 
                "[class*='question']", "[data-functional-selector*='title']"
            ]
            
            for selector in title_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            text = elem.text.strip()
                            if text and len(text) > 5:
                                return text
                except:
                    continue
            
            return ""
        except:
            return ""
    
    def _prepare_early_answer(self, question_title):
        """Prepare an answer in advance during the 'get ready' phase"""
        try:
            # Early classification and preparation
            question = Question(
                question_text=question_title.lower(),
                choices=[],  # We don't have choices yet
                answer=[],  # Will be filled later
                is_multiple_choice=True,  # Assume multiple choice
                question_type="logic"  # Default type
            )
            
            # Try to classify the question early
            question_type = self._classify_question(question_title.lower(), [])
            question.question_type = question_type
            
            # Add answer selectors as metadata
            button_selectors = [
                "[data-functional-selector='answer-0']",
                "[data-functional-selector='answer-1']",
                "[data-functional-selector='answer-2']",
                "[data-functional-selector='answer-3']"
            ]
            
            # Create placeholder choices (will be replaced with real ones later)
            formatted_choices = []
            for i in range(4):
                formatted_choices.append(f"Option {i+1}: [Unknown option {i+1}]")
            question.choices = formatted_choices
            
            # Add selectors as metadata
            metadata = "\n\nAnswer selectors:"
            for i, selector in enumerate(button_selectors):
                metadata += f"\n  {i}: {selector}"
            
            question.question_text += metadata
            
            # Get an early answer from AI
            answer_data = self.get_answer_from_ai(question)
            question.answer = answer_data.correct_options
            # Store the early answer for later use
            self.early_answer = question.answer
            print(f"🧠 Early answer preparation: {question.answer}")
        except Exception as e:
            print(f"Error preparing early answer: {e}")
    
    def _check_for_active_question(self, current_url, lobby_indicators):
        """Check if an active question is currently displayed"""
        try:
            # Check for question title indicators
            question_indicators = [
                "[data-functional-selector='block-title']",
                "[data-functional-selector='question-title']",
                "h1", ".question-title", ".block-title"
            ]
            
            for selector in question_indicators:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            text = elem.text.strip()
                            # Make sure it's actually a question, not lobby or results
                            if text and len(text) > 10 and not any(lobby in text.lower() for lobby in lobby_indicators):
                                # Also check it's not showing results/scores
                                if not any(result_word in text.lower() for result_word in ["correct", "incorrect", "score", "points", "leaderboard"]):
                                    print(f"Question detected: {text[:50]}...")
                                    return True
                except:
                    continue
            
            # Check URL patterns for question pages
            if any(keyword in current_url for keyword in ["question", "quiz", "gameblock"]) and "lobby" not in current_url and "result" not in current_url:
                # Look for answer buttons as confirmation of actual question
                try:
                    answer_buttons = self.driver.find_elements(By.CSS_SELECTOR, "[data-functional-selector^='answer-'], button[class*='answer']")
                    if answer_buttons and any(btn.is_displayed() for btn in answer_buttons):
                        print("Question detected with answer buttons")
                        return True
                except:
                    pass
            
            return False
            
        except:
            return False
            
    def is_in_lobby(self) -> bool:
        """Check if we're in the lobby/waiting area"""
        try:
            lobby_indicators = [
                "You're in! See your nickname on screen?",
                "you're in",
                "see your nickname",
                "waiting for",
                "get ready",
                "starting soon",
                "lobby"
            ]
            
            page_text = self.driver.page_source.lower()
            current_url = self.driver.current_url.lower()
            
            # Check page content
            content_match = any(indicator in page_text for indicator in lobby_indicators)
            
            # Check URL
            url_match = any(keyword in current_url for keyword in ["lobby", "getready", "waiting"])
            
            return content_match or url_match
            
        except Exception as e:
            print(f"Error checking lobby state: {e}")
            return False
            
    def debug_page_state(self):
        """Print debug information about current page state"""
        try:
            print(f"Current URL: {self.driver.current_url}")
            print(f"Page title: {self.driver.title}")
            
            # Check for common elements
            common_selectors = [
                "h1", "h2", "button", "input", 
                "[class*='question']", "[class*='answer']", 
                "[class*='title']", "[class*='choice']"
            ]
            
            print("Elements found:")
            for selector in common_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"  {selector}: {len(elements)} elements")
                        for i, elem in enumerate(elements[:3]):  # Show first 3
                            text = elem.text.strip()[:50]
                            if text:
                                print(f"    {i}: {text}")
                except:
                    continue
                    
        except Exception as e:
            print(f"Error in debug: {e}")
            
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit() 

    def _extract_code_from_url(self, question_text: str) -> str:
        """Extract code from a URL in a coding question"""
        import re
        
        # Look for URLs in the question text
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, question_text)
        
        if not urls:
            print("No URLs found in coding question")
            return question_text
        
        print(f"Found URLs in coding question: {urls}")
        
        for url in urls:
            try:
                # Store current window handle
                original_window = self.driver.current_window_handle
                
                # Open URL in new tab
                self.driver.execute_script(f"window.open('{url}', '_blank');")
                
                # Switch to new tab
                self.driver.switch_to.window(self.driver.window_handles[-1])
                
                # Wait for page to load
                time.sleep(3)
                
                extracted_code = ""
                
                # Handle Google Drive documents
                if "drive.google.com" in url or "docs.google.com" in url:
                    extracted_code = self._extract_from_google_drive()
                
                # Handle GitHub or other code hosting sites
                elif "github.com" in url or "gist.github.com" in url:
                    extracted_code = self._extract_from_github()
                
                # Handle Pastebin
                elif "pastebin.com" in url:
                    extracted_code = self._extract_from_pastebin()
                
                # Generic code extraction for other sites
                else:
                    extracted_code = self._extract_code_generic()
                
                # Close the tab and switch back
                self.driver.close()
                self.driver.switch_to.window(original_window)
                
                if extracted_code:
                    print(f"Extracted code from {url}:")
                    print(extracted_code[:200] + "..." if len(extracted_code) > 200 else extracted_code)
                    return f"{question_text}\n\nCode from {url}:\n{extracted_code}"
                
            except Exception as e:
                print(f"Error extracting code from {url}: {e}")
                # Make sure we switch back to original window
                try:
                    self.driver.switch_to.window(original_window)
                except:
                    pass
        
        return question_text
    
    def _extract_from_google_drive(self) -> str:
        """Extract code from Google Drive document"""
        try:
            current_url = self.driver.current_url
            print(f"Extracting from Google Drive URL: {current_url}")
            
            # Convert Google Drive view URL to direct access if needed
            if "/file/d/" in current_url and "/view" in current_url:
                # Extract file ID and convert to direct access URL
                import re
                file_id_match = re.search(r'/file/d/([a-zA-Z0-9-_]+)', current_url)
                if file_id_match:
                    file_id = file_id_match.group(1)
                    # Try to navigate to the direct view URL
                    direct_url = f"https://drive.google.com/file/d/{file_id}/view"
                    print(f"Converting to direct URL: {direct_url}")
                    self.driver.get(direct_url)
                    time.sleep(5)
            
            # Wait for Google Drive to load
            time.sleep(5)
            
            # Try to click "Open with Google Docs" if it's a document
            try:
                open_with_docs_selectors = [
                    "//span[contains(text(), 'Open with Google Docs')]",
                    "//div[contains(text(), 'Open with Google Docs')]",
                    "[aria-label*='Open with Google Docs']",
                    ".ndfHFb-c4YZDc-Wrql6b"  # Google Drive open button
                ]
                
                for selector in open_with_docs_selectors:
                    try:
                        if selector.startswith("//"):
                            element = self.driver.find_element(By.XPATH, selector)
                        else:
                            element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if element.is_displayed() and element.is_enabled():
                            element.click()
                            print("Clicked 'Open with Google Docs'")
                            time.sleep(5)
                            break
                    except:
                        continue
            except:
                pass
            
            # Try different selectors for Google Docs content
            code_selectors = [
                ".kix-page-content-wrap",  # Google Docs main content
                ".kix-page",
                ".docs-text-editing",
                ".kix-wordhtmlgenerator-word-node",  # Google Docs text nodes
                "pre",  # Code blocks
                "code",  # Inline code
                ".prettyprint",  # Syntax highlighted code
                "[class*='code']",
                "[class*='highlight']",
                ".ndfHFb-c4YZDc-GSWXbd",  # Google Drive preview content
                "[data-drive-file-content]"  # Drive file content
            ]
            
            extracted_text = ""
            for selector in code_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 10:  # Ensure substantial content
                            extracted_text = text
                            print(f"Found content with selector {selector}: {text[:100]}...")
                            break
                    if extracted_text:
                        break
                except:
                    continue
            
            # If no specific content found, try to get all visible text
            if not extracted_text:
                try:
                    # Try to get text from the main content area
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    body_text = body.text.strip()
                    
                    # Filter out common Google Drive UI text
                    ui_text_to_remove = [
                        "Google Drive", "Sign in", "Open with", "Download", "Share",
                        "File", "Edit", "View", "Insert", "Format", "Tools", "Add-ons", "Help"
                    ]
                    
                    lines = body_text.split('\n')
                    filtered_lines = []
                    for line in lines:
                        line = line.strip()
                        if line and len(line) > 3 and not any(ui_text in line for ui_text in ui_text_to_remove):
                            filtered_lines.append(line)
                    
                    if filtered_lines:
                        extracted_text = '\n'.join(filtered_lines)
                        print(f"Extracted filtered text: {extracted_text[:200]}...")
                except:
                    pass
            
            # Try to extract from iframe if present (for embedded documents)
            if not extracted_text:
                try:
                    iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                    for iframe in iframes:
                        try:
                            self.driver.switch_to.frame(iframe)
                            iframe_body = self.driver.find_element(By.TAG_NAME, "body")
                            iframe_text = iframe_body.text.strip()
                            if iframe_text and len(iframe_text) > 10:
                                extracted_text = iframe_text
                                print(f"Found content in iframe: {iframe_text[:100]}...")
                                break
                        except:
                            pass
                        finally:
                            self.driver.switch_to.default_content()
                except:
                    pass
            
            return extracted_text
                
        except Exception as e:
            print(f"Error extracting from Google Drive: {e}")
        
        return ""
    
    def _extract_from_github(self) -> str:
        """Extract code from GitHub"""
        try:
            # GitHub code selectors
            code_selectors = [
                ".blob-code-inner",  # GitHub file content
                ".highlight pre",
                ".js-file-line",
                "pre",
                "code"
            ]
            
            code_lines = []
            for selector in code_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text:
                            code_lines.append(text)
                    if code_lines:
                        return "\n".join(code_lines)
                except:
                    continue
                    
        except Exception as e:
            print(f"Error extracting from GitHub: {e}")
        
        return ""
    
    def _extract_from_pastebin(self) -> str:
        """Extract code from Pastebin"""
        try:
            # Pastebin code selectors
            code_selectors = [
                ".de1",  # Pastebin code content
                "#paste_code",
                ".source",
                "pre",
                "code"
            ]
            
            for selector in code_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    text = element.text.strip()
                    if text:
                        return text
                except:
                    continue
                    
        except Exception as e:
            print(f"Error extracting from Pastebin: {e}")
        
        return ""
    
    def _extract_code_generic(self) -> str:
        """Generic code extraction for other sites"""
        try:
            # Try common code-related selectors
            code_selectors = [
                "pre",
                "code",
                ".code",
                ".highlight",
                ".prettyprint",
                ".syntax",
                "[class*='code']",
                "[class*='highlight']",
                "[class*='syntax']"
            ]
            
            for selector in code_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 10:  # Ensure substantial content
                            return text
                except:
                    continue
            
            # Fallback: look for text that looks like code
            try:
                body_text = self.driver.find_element(By.TAG_NAME, "body").text
                # Simple heuristic: if text contains common programming keywords
                code_keywords = ['function', 'def ', 'class ', 'import ', 'include', 'var ', 'let ', 'const ', '{', '}', ';']
                if any(keyword in body_text for keyword in code_keywords):
                    return body_text.strip()
            except:
                pass
                
        except Exception as e:
            print(f"Error in generic code extraction: {e}")
        
        return ""

    def _capture_question_image(self) -> bytes:
        """Capture a screenshot of the current question"""
        try:
            # Take a screenshot of the current page
            screenshot = self.driver.get_screenshot_as_png()
            
            return screenshot
            
        except Exception as e:
            print(f"Error capturing question image: {e}")
            return None

    def _get_vision_answer(self, question: Question, prompt: str):
        """Get answer for image questions using vision model"""
        try:
            import base64
            from langchain_openai import ChatOpenAI
            
            # Use GPT-4 Vision model
            vision_llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
            
            # Convert image to base64
            image_base64 = base64.b64encode(question.image_data).decode('utf-8')
            
            # Create message with image
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
            
            print("🖼️ Sending image question to vision model...")
            response = vision_llm.invoke(messages)
            
            return response
            
        except Exception as e:
            print(f"Error with vision model: {e}")
            # Fallback to text-only model
            return self.llm.invoke(prompt) 

    def _are_answer_buttons_visible(self):
        """Check if answer buttons are visible on the page"""
        try:
            # Try to find answer buttons with Kahoot-specific selectors
            button_selectors = [
                "[data-functional-selector='answer-0']",
                "[data-functional-selector='answer-1']",
                "[data-functional-selector='answer-2']",
                "[data-functional-selector='answer-3']"
            ]
            
            for selector in button_selectors:
                try:
                    button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if button and button.is_displayed():
                        return True
                except:
                    continue
            
            # Try more generic selectors
            other_selectors = [
                "button[data-functional-selector^='answer-']",
                "button[class*='answer']",
                ".answer-button"
            ]
            
            for selector in other_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if buttons and any(btn.is_displayed() for btn in buttons):
                        return True
                except:
                    continue
            
            return False
        except:
            return False 