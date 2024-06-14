import google.generativeai as genai
import os
import re
from typing import Any
import json

class ConnectionsLLM:
    llm = None
    chat_session = None
    generation = None
    theme = None

    @staticmethod
    def initialize_model(api_key=None):
        generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
        }
        genai.configure(api_key=api_key)
        ConnectionsLLM.llm = genai.GenerativeModel(model_name="gemini-1.5-pro", 
                                generation_config=generation_config, 
                                system_instruction="Give me 4 sub-category of the user suggested category or theme. Each sub-category must have 4 things / objects or concepts. Also, rank these sub-categories on a scale of difficulty from 1-4, there should be one sub-category of each difficulty level.\n\nThese 4 things / objects or concepts must preferably be a single word. Format the result as JSON.\n\nExample:\n{\n  \"categories\": [\n    {\n      \"category\": \"Characters\",\n      \"difficulty\": 1,\n      \"items\": [\"Iron Man\", \"Spider-Man\", \"Captain America\", \"Hulk\"]\n    },\n    {\n      \"category\": \"Locations\",\n      \"difficulty\": 2,\n      \"items\": [\"Asgard\", \"Wakanda\", \"X-Mansion\", \"Avengers Tower\"]\n    },\n    {\n      \"category\": \"Villains\",\n      \"difficulty\": 3,\n      \"items\": [\"Thanos\", \"Doctor Doom\", \"Magneto\", \"Loki\"]\n    },\n    {\n      \"category\": \"Artifacts\",\n      \"difficulty\": 4,\n      \"items\": [\"Infinity Gauntlet\", \"Mjolnir\", \"Vibranium\", \"Tesseract\"]\n    }\n  ]\n}\n")
        ConnectionsLLM.chat_session = ConnectionsLLM.llm.start_chat(history=[])
        

    @staticmethod
    def generate_categories(theme = "Movies"):
        ConnectionsLLM.theme = theme
        ConnectionsLLM.generation = ConnectionsLLM.chat_session.send_message(theme)

    @staticmethod
    def get_json_from_generation(generation) -> Any: 
        json_data = None
        try:
            print(generation)
            output_stripped = re.sub(r'```(?:json|JSON)\n|\n```', '', generation.text)
            # match = re.search(r'```(?:json|JSON)\n(.*?)\n```', generation.content)
            # if(match):
            #    output_stripped = match.group(1)
            json_data = json.loads(output_stripped)['categories']
        except json.JSONDecodeError:
            raise json.JSONDecodeError("Failed to parse JSON from generation.")
        return json_data

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
