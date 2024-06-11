import os
from typing import Any
import google.generativeai as genai
import json
import re
import random
from flask import Flask, redirect, render_template, request, url_for, session

os.environ["GOOGLE_API_KEY"] = "AIzaSyDuEc50CK1T3dRYfhMx2_-r1igsSd0PY54"

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for sessions

class AutoConnectionsLLM:
    generation_config = {
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }
    llm = genai.GenerativeModel(model_name="gemini-1.5-pro", 
                                generation_config=generation_config, 
                                system_instruction="Give me 4 sub-category of the user suggested category or theme. Each sub-category must have 4 things / objects or concepts. Also, rank these sub-categories on a scale of difficulty from 1-4, there should be one sub-category of each difficulty level.\n\nThese 4 things / objects or concepts must preferably be a single word. Format the result as JSON.\n\nExample:\n{\n  \"categories\": [\n    {\n      \"category\": \"Characters\",\n      \"difficulty\": 1,\n      \"items\": [\"Iron Man\", \"Spider-Man\", \"Captain America\", \"Hulk\"]\n    },\n    {\n      \"category\": \"Locations\",\n      \"difficulty\": 2,\n      \"items\": [\"Asgard\", \"Wakanda\", \"X-Mansion\", \"Avengers Tower\"]\n    },\n    {\n      \"category\": \"Villains\",\n      \"difficulty\": 3,\n      \"items\": [\"Thanos\", \"Doctor Doom\", \"Magneto\", \"Loki\"]\n    },\n    {\n      \"category\": \"Artifacts\",\n      \"difficulty\": 4,\n      \"items\": [\"Infinity Gauntlet\", \"Mjolnir\", \"Vibranium\", \"Tesseract\"]\n    }\n  ]\n}\n")
    chat_session = llm.start_chat(history=[])
    generation = None
    theme = None

    @staticmethod
    def generate_categories(theme = "Movies"):
        AutoConnectionsLLM.theme = theme
        output = AutoConnectionsLLM.chat_session.send_message(theme)
        AutoConnectionsLLM.generation = output

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
        return AutoConnectionsLLM.generation

    @staticmethod
    def get_structured_generation():
        try:
            json_data = AutoConnectionsLLM.get_json_from_generation(AutoConnectionsLLM.get_generation())
        except:
            raise json.JSONDecodeError("Failed to parse JSON from generation.")
        return json_data


class ConnectionsGameState:
    def __init__(self, categories, theme = "", words = [], correct_words=[], correct_categories=[], attempts=4):
        self.theme = theme
        self.categories = categories
        self.correct_words = correct_words
        self.correct_categories = correct_categories
        self.attempts = attempts
        
        self.words = []
        self.category_difficulty_map = {}
        self.word_to_category = {}
        for category_info in self.categories:
            category = category_info['category']
            difficulty = category_info['difficulty']
            items = category_info['items']

            self.category_difficulty_map[category] = difficulty
            for word in items:
                self.word_to_category[word] = category
            if len(words) == 0:
                self.words.extend(items)

        # Shuffle the word list, override with existing word list if it exists. 
        if len(words) == 0:
            random.shuffle(self.words)
        else:
            self.words = words

    def to_json(self):
        return {
            'theme': self.theme,
            'categories': self.categories,
            'words' : self.words,
            'correct_words': self.correct_words,
            'correct_categories': self.correct_categories,
            'attempts': self.attempts
        }
    
    def get_word_difficulty(self, word):
        return self.category_difficulty_map[self.word_to_category[word]]

    def verify(self, selected_words):
        # Check from word_to_category if the category for all words is the same.
        if self.attempts == 0 or len(selected_words) != 4:
            return False

        categories = [self.word_to_category[word] for word in selected_words]
        if len(set(categories)) == 1:
            if categories[0] not in self.correct_categories:
                self.correct_categories.append(categories[0])
            for word in selected_words:
                self.correct_words.append((word, self.get_word_difficulty(word)))
            return True
        else:
            self.attempts = self.attempts - 1
            return False

@app.route('/')
def index():
    return redirect(url_for('new_game'))

@app.route('/verify', methods=['POST'])
def verify():
    game_state = ConnectionsGameState(**session['game_state'])
    print(game_state.to_json())
    if request.form.get('selected_words'):
        selected_words = json.loads(request.form.get('selected_words'))
        print(selected_words)
        print("Verify: %s" % game_state.verify(selected_words))
    session['game_state'] = game_state.to_json()
    return render_template('index.html', theme=game_state.theme, words=game_state.words, correct_words=session['game_state']['correct_words'], attempts=session['game_state']['attempts'])

@app.route('/new_game', methods=['GET', 'POST'])
def new_game():
    # Clear the session to start a new game
    session.pop('game_state', None)

    # Keep generating if we don't find anything valid.
    theme = None
    while True:
        if request.form.get('theme'):
            theme = request.form.get('theme')
            AutoConnectionsLLM.generate_categories(theme = theme)
        else:
            AutoConnectionsLLM.generate_categories()
        try:
            categories = AutoConnectionsLLM.get_structured_generation()
            print(categories)
        except json.JSONDecodeError:
            continue
        break
        
    # Initialze a new game state, which triggers word shuffling.
    game_state = ConnectionsGameState(categories=categories, theme = AutoConnectionsLLM.theme)
    session['game_state'] = game_state.to_json()
    return render_template('index.html', theme = game_state.theme, words=session['game_state']['words'], correct_words=session['game_state']['correct_words'], attempts=session['game_state']['attempts'])


if __name__ == '__main__':
    app.run(debug=True)
