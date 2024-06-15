import json
import os
from flask import Flask, redirect, render_template, request, url_for, session
from connections_llm import ConnectionsLLM, AlreadyGuessedMessagesLLM
from connections_game_state import ConnectionsGameState, VerificationResult

os.environ["GEMINI_API_KEY"] = "AIzaSyDuEc50CK1T3dRYfhMx2_-r1igsSd0PY54"

ConnectionsLLM.initialize_model(api_key=os.environ["GEMINI_API_KEY"])
AlreadyGuessedMessagesLLM.initialize_model(api_key=os.environ["GEMINI_API_KEY"])
TESTING = False

# Flask Deployment
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for sessions

@app.route('/')
def index():
    return redirect(url_for('new_game'))

@app.route('/new_game', methods=['GET', 'POST'])
def new_game():
    # Clear the session to start a new game
    session.pop('game_state', None)

    # Keep generating if we don't find anything valid.
    theme = None
    if not TESTING:
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
        test_config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "testdata", "simple.json")
        with open(test_config_path, 'r') as f:
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
    verification_result = VerificationResult.FAILED
    if request.form.get('selected_words'):
        selected_words = json.loads(request.form.get('selected_words'))
        print('Selected Words: %s' %selected_words)
        verification_result, already_guessed_attempts = game_state.verify(selected_words)
        print('Verification Result: %s' %verification_result)
    
    session['game_state'] = game_state.to_json()
    incorrect_words = game_state.get_incorrect_words()
    word_grid = game_state.generate_word_grid()
    return render_template('index.html', theme=game_state.theme, 
                           words=game_state.words, 
                           incorrect_words = incorrect_words,
                           word_grid = word_grid,
                           correct_difficulty_to_category_map=session['game_state']['correct_difficulty_to_category_map'],
                           correct_category_to_words_map=session['game_state']['correct_category_to_words_map'], 
                           verification_result = verification_result,
                           already_guessed_alert_message = AlreadyGuessedMessagesLLM.get_alert_message(already_guessed_attempts),
                           attempts=session['game_state']['attempts'])

if __name__ == '__main__':
    app.run(debug=True)
