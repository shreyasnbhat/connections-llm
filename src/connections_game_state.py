import enum
import random

class VerificationResult(enum.Enum):
    SUCCESS = enum.auto()
    ALREADY_GUESSED = enum.auto()
    ONE_AWAY = enum.auto()
    FAILED = enum.auto()

class ConnectionsGameState:
    def __init__(self, categories, theme = "", 
                 words = [], 
                 incorrect_guesses = {}, 
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
        self.incorrect_guesses = incorrect_guesses

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
            'incorrect_guesses' : self.incorrect_guesses,
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


    def verify(self, selected_words) -> VerificationResult:
        # Check from word_to_category if the category for all words is the same.
        if self.attempts == 0 or len(selected_words) != 4:
            return VerificationResult.FAILED, 0

        categories = [self.word_to_category[word] for word in selected_words]
        selected_words.sort()
        selected_words_key = ",".join(selected_words)
        if len(set(categories)) == 1:
            if categories[0] not in self.correct_category_to_words_map:
                self.correct_category_to_words_map[categories[0]] = selected_words
                self.correct_difficulty_to_category_map[self.category_difficulty_map[categories[0]]] = categories[0]
            return VerificationResult.SUCCESS, 0
        elif selected_words_key in self.incorrect_guesses:
            self.incorrect_guesses[selected_words_key] += 1
            return VerificationResult.ALREADY_GUESSED, self.incorrect_guesses[selected_words_key]
        else:
            self.attempts = self.attempts - 1
            self.incorrect_guesses[selected_words_key] = 0

            guess_category_count_map = {}
            for word in selected_words:
                guess_category_count_map[self.word_to_category[word]] = guess_category_count_map.get(self.word_to_category[word], 0) + 1
            if max(guess_category_count_map.values()) == 3:
                return VerificationResult.ONE_AWAY
            return VerificationResult.FAILED, 0
