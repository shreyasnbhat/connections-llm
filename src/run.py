import json
import os
import random
from flask import Flask, redirect, render_template, request, url_for, session
from connections_llm import ConnectionsLLM

os.environ["GOOGLE_API_KEY"] = "AIzaSyDuEc50CK1T3dRYfhMx2_-r1igsSd0PY54"
testing = False

# LLM Agent Setup
ConnectionsLLM.initialize_model(api_key=os.environ["GOOGLE_API_KEY"])

# Flask Deployment
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for sessions

class ConnectionsGameState:
    def __init__(self, categories, theme = "", 
                 words = [], 
                 correct_difficulty_to_category_map = {}, 
                 correct_category_to_words_map = {}, 
                 attempts=4):
        self.theme = theme
        self.categories = categories
        
        # Force cast integers where applicable. Ideally should type these functions.
        self.correct_difficulty_to_category_map = {}
        for difficulty, category in correct_difficulty_to_category_map.items():
            self.correct_difficulty_to_category_map[int(difficulty)] = category

        self.correct_category_to_words_map = correct_category_to_words_map
        self.attempts = int(attempts)
        
        self.words = []
        self.category_difficulty_map = {}
        self.word_to_category = {}
        game_init = (len(words) == 0)
        for category_info in self.categories:
            category = category_info['category']
            difficulty = int(category_info['difficulty'])
            items = category_info['items']

            self.category_difficulty_map[category] = difficulty
            for word in items:
                self.word_to_category[word] = category
            if game_init:
                self.words.extend(items)

        # Shuffle the word list, override with existing word list if it exists. 
        if game_init:
            random.shuffle(self.words)
        else:
            self.words = words


    def to_json(self):
        return {
            'theme': self.theme,
            'categories': self.categories,
            'words' : self.words,
            'correct_category_to_words_map': self.correct_category_to_words_map,
            'correct_difficulty_to_category_map': self.correct_difficulty_to_category_map,
            'attempts': self.attempts
        }
    
    def get_word_difficulty(self, word):
        return self.category_difficulty_map[self.word_to_category[word]]
    
    def get_incorrect_words(self):
        return list(set(self.words) - set(sum(self.correct_category_to_words_map.values(), [])))
    
    def get_incorrect_word_chunks(self):
        incorrect_words = self.get_incorrect_words()
        return [incorrect_words[i:i+4] for i in range(0, len(incorrect_words), 4)]
    
    def generate_word_grid(self):
        # Instantiate the word grid.
        word_grid = [[] for _ in range(4)]
        
        # Add correct words in the grid in the respective row based on difficulty.
        for difficulty, category in self.correct_difficulty_to_category_map.items():
            correct_words = self.correct_category_to_words_map[category]
            word_grid[int(difficulty) - 1] = correct_words
        
        # Add the remaining words
        idx = 0
        incorrect_words_chunks = self.get_incorrect_word_chunks()
        for row in range(4):
            if word_grid[row] == []:
                word_grid[row] = incorrect_words_chunks[idx]
                idx += 1

        return word_grid


    def verify(self, selected_words):
        # Check from word_to_category if the category for all words is the same.
        if self.attempts == 0 or len(selected_words) != 4:
            return False

        categories = [self.word_to_category[word] for word in selected_words]
        if len(set(categories)) == 1:
            if categories[0] not in self.correct_category_to_words_map:
                self.correct_category_to_words_map[categories[0]] = selected_words
                self.correct_difficulty_to_category_map[self.category_difficulty_map[categories[0]]] = categories[0]
            return True
        else:
            self.attempts = self.attempts - 1
            return False

@app.route('/')
def index():
    return redirect(url_for('new_game'))

@app.route('/new_game', methods=['GET', 'POST'])
def new_game():
    # Clear the session to start a new game
    session.pop('game_state', None)

    # Keep generating if we don't find anything valid.
    theme = None
    if not testing:
        while True:
            if request.form.get('theme'):
                theme = request.form.get('theme')
                ConnectionsLLM.generate_categories(theme = theme)
            else:
                ConnectionsLLM.generate_categories()
            try:
                categories = ConnectionsLLM.get_structured_generation()
                print(categories)
            except json.JSONDecodeError:
                continue
            break
    else:
        theme = "Movies"
        with open('/Users/shreyasbhat/Code/llms/auto_connections/src/testdata/simple.json', 'r') as f:
            categories = json.load(f)

        
    # Initialze a new game state, which triggers word shuffling.
    game_state = ConnectionsGameState(categories=categories, 
                                      theme=theme)
    incorrect_words = game_state.get_incorrect_words()
    word_grid = game_state.generate_word_grid()
    session['game_state'] = game_state.to_json()
    return render_template('index.html', theme = game_state.theme, 
                           words=session['game_state']['words'], 
                           incorrect_words = incorrect_words,
                           word_grid = word_grid,
                           correct_difficulty_to_category_map=session['game_state']['correct_difficulty_to_category_map'],
                           correct_category_to_words_map=session['game_state']['correct_category_to_words_map'], 
                           attempts=session['game_state']['attempts'])

@app.route('/verify', methods=['POST'])
def verify():
    game_state = ConnectionsGameState(**session['game_state'])
    if request.form.get('selected_words'):
        selected_words = json.loads(request.form.get('selected_words'))
        print('Selected Words: %s' %selected_words)
        print("Verify: %s" % game_state.verify(selected_words))
    session['game_state'] = game_state.to_json()
    incorrect_words = game_state.get_incorrect_words()
    word_grid = game_state.generate_word_grid()
    return render_template('index.html', theme=game_state.theme, 
                           words=game_state.words, 
                           incorrect_words = incorrect_words,
                           word_grid = word_grid,
                           correct_difficulty_to_category_map=session['game_state']['correct_difficulty_to_category_map'],
                           correct_category_to_words_map=session['game_state']['correct_category_to_words_map'], 
                           attempts=session['game_state']['attempts'])

if __name__ == '__main__':
    app.run(debug=True)
