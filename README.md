### Auto Connections: A Word-Matching Game
This Python Flask application implements a simple word-matching game called "Auto Connections". The game challenges players to identify sets of four words that belong to the same category, generated by a large language model (LLM).

#### How to Play

1. Start a New Game: Visit the /new_game route. You can optionally provide a theme for the game (e.g., "Movies", "Science Fiction", etc.).
2. Choose Words: The game presents a list of words. Select four words that you believe belong to the same category.
3. Verify Your Choice: Submit your selection. The game will verify if the chosen words belong to the same category.
4. Continue Playing: The game continues until you have correctly identified all the categories or run out of attempts.

#### Features
- AI-Powered Category Generation: The game utilizes Google's Gemini Pro LLM to generate categories and corresponding words.
- Dynamic Themes: Players can choose a theme for the game, allowing for diverse and engaging gameplay.
- Difficulty Levels: Categories are assigned difficulty levels, providing a gradual challenge.
- Attempts: Players have a limited number of attempts to correctly identify categories.

#### Technical Details
- Framework: Flask
- LLM: Google Gemini Pro
- Language: Python

#### Installation and Running
1. Install Dependencies:

```
pip install -r requirements.txt
```

2. Set Environment Variables:
- `GOOGLE_API_KEY`: Your Google AI Studio API key.

3. Run the Application:

```
flask run.py
```

#### Notes
The game currently uses a hardcoded API key for Google Cloud. You should replace this with your own API key.
The game is designed for local development and testing. For deployment, consider using a web server like Gunicorn.

#### Future Improvements
- User Interface: Enhance the user interface for a more engaging experience.
- Scoring System: Implement a scoring system to track player progress.
- Persistence: Store game progress and user data for a more persistent experience.
- Multiplayer: Allow multiple players to compete against each other.