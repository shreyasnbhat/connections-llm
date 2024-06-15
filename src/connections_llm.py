import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import os
import re
from typing import Any
import json

class BaseLLM:
    llm = None
    chat_session = None
    generation = None
    model_name = "gemini-1.5-flash"

    @staticmethod
    def initialize_model(api_key=None):
        genai.configure(api_key=api_key)

    @staticmethod
    def get_json_from_generation(generation) -> Any: 
        json_data = None
        try:
            print(generation)
            output_stripped = re.sub(r'```(?:json|JSON)\n|\n```', '', generation.text)
            # match = re.search(r'```(?:json|JSON)\n(.*?)\n```', generation.content)
            # if(match):
            #    output_stripped = match.group(1)

            json_data = json.loads(output_stripped)
        except json.JSONDecodeError:
            raise json.JSONDecodeError("Failed to parse JSON from generation.")
        return json_data

class ConnectionsLLM(BaseLLM):
    theme = None

    @staticmethod
    def initialize_model(api_key=None):
        super.initialize_model(api_key)
        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }
        ConnectionsLLM.llm = genai.GenerativeModel(model_name=BaseLLM.model_name, 
                                generation_config=generation_config, 
                                system_instruction="You are a helpful agent expert in the game of New York Times Connections, and can expertly generate 16 words for the game.\n\nGenerate 16 words in random with 4 underlying themes. If the user inputs a overall theme, you may use that to choose your 4 underlying themes. If the user enter's many themes that are comma separated then use all those themes.\n\nThe underlying themes must be of varying difficulties. The easiest one should be solvable by teenager, and the most difficult ones should be solvable by an well-educated adult. The connection between the words within a category shouldn't be immediately obvious. Players should have to think a little to figure out the theme.\n\n1) Avoid generating word lists obvious patterns in pronunciation, writing style, grammar elements etc. \n2) Avoid rhyming word groups.\n3) Avoid number based groups of words.\n4) Avoid groups of words with a similar string pattern.\n5) Use words that are generally understood and avoid overly specific terms or proper nouns unless absolutely necessary for the theme.\n6) Make sure that the items outputted don't contain the category name as a substring.\n\nReturn the result in JSON.\n\nAn example response:\n[\n  {\n    \"category\": \"Version Control\",\n    \"difficulty\": 1,\n    \"items\": [\"Git\", \"GitHub\", \"Bitbucket\", \"SVN\"]\n  },\n  {\n    \"category\": \"Code Editors\",\n    \"difficulty\": 2,\n    \"items\": [\"VS Code\", \"Sublime Text\", \"Atom\", \"Vim\"]\n  },\n  {\n    \"category\": \"Testing Frameworks\",\n    \"difficulty\": 3,\n    \"items\": [\"JUnit\", \"Jest\", \"Mocha\", \"Selenium\"]\n  },\n  {\n    \"category\": \"Cloud Platforms\",\n    \"difficulty\": 4,\n    \"items\": [\"AWS\", \"Azure\", \"Google Cloud\", \"Heroku\"]\n  }\n]\n\nUSER INPUTTED THEME: ")
        ConnectionsLLM.chat_session = ConnectionsLLM.llm.start_chat(history=[])
        

    @staticmethod
    def generate_categories(theme = "Movies"):
        ConnectionsLLM.theme = theme
        ConnectionsLLM.generation = ConnectionsLLM.chat_session.send_message(theme)

    @staticmethod
    def get_generation():
        return ConnectionsLLM.generation

    @staticmethod
    def get_structured_generation():
        try:
            json_data = ConnectionsLLM.get_json_from_generation(ConnectionsLLM.get_generation())
        except:
            raise json.JSONDecodeError("Failed to parse JSON from generation.")
        return json_data
    
class AlreadyGuessedMessagesLLM(BaseLLM):
    already_guessed_alert_messages = []

    @staticmethod
    def initialize_model(api_key=None):
        super.initialize_model(api_key)
        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }
        AlreadyGuessedMessagesLLM.llm = genai.GenerativeModel(model_name=BaseLLM.model_name, 
                                generation_config=generation_config,
                                safety_settings={
                                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                                },
                                system_instruction="You are an expert at being very sarcastic. A player is playing the game of connections and is guessing word groups. They've guessed a few word groups earlier, and now have guessed another wrong word group. We want to generate messages when the user guesses the same wrong word combination again. Output 10 messages stating that they've already guessed a wrong combination before. Message at index i must be more sarcastic than the message before, and the message at index i indicates that the user has guessed the same wrong word combination i times.\n\nOutput the result in JSON.\n\nExample:\n[\n    \"Already guessed the word!\",\n    \"Did I stutter?\",\n    \"You have a knack of being stupid don't you?\",\n]")
        AlreadyGuessedMessagesLLM.chat_session = AlreadyGuessedMessagesLLM.llm.start_chat(history=[])
        AlreadyGuessedMessagesLLM.generation = AlreadyGuessedMessagesLLM.chat_session.send_message("Hello")
        AlreadyGuessedMessagesLLM.already_guessed_alert_messages = AlreadyGuessedMessagesLLM.get_json_from_generation(AlreadyGuessedMessagesLLM.generation)
    
    @staticmethod
    def get_alert_message(count):
        if count < len(AlreadyGuessedMessagesLLM.already_guessed_alert_messages):
            return AlreadyGuessedMessagesLLM.already_guessed_alert_messages[count]
        else:
            return "Already guessed!"
