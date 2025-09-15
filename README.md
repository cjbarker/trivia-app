# Trivia Web Application

A team-based trivia web application built with Python Flask that reads questions from markdown files.

## Features

- **Team Management**: Create new teams or join existing ones
- **Question Formats**: Supports both multiple choice and fill-in-the-blank questions
- **Real-time Scoring**: Live scoreboard updates using WebSocket connections
- **Markdown Support**: Load questions from markdown files with flexible formatting
- **Responsive Design**: Works on desktop and mobile devices

## Setup Instructions

1. **Create and Activate Virtual Environment**
   ```bash
   # Create virtual environment
   python3 -m venv venv
   
   # Activate virtual environment
   source venv/bin/activate  # On macOS/Linux
   # or on Windows:
   # venv\Scripts\activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare Questions**
   - Edit `questions.md` or create your own markdown file with trivia questions
   - See the existing `questions.md` for formatting examples

4. **Run the Application**
   ```bash
   # Make sure virtual environment is activated
   source venv/bin/activate  # If not already activated
   python app.py
   ```

5. **Access the Game**
   - Open your browser to `http://localhost:5001`
   - Create a team or join an existing one
   - Start playing!

## Testing

To test the application:

1. **Start the application** (following setup instructions above)
2. **Open multiple browser windows** to `http://localhost:5001` to simulate multiple players
3. **Create teams** and add players to test team functionality
4. **Answer questions** to verify scoring and real-time updates work correctly

## Deactivating Virtual Environment

When you're done working with the application:
```bash
deactivate
```

## Question Format

The application supports two question types:

### Multiple Choice
```markdown
## What is the capital of France?

A) London
B) Berlin
C) **Paris**
D) Madrid
```

### Fill in the Blank
```markdown
## The largest planet in our solar system is ________.

**Answer: Jupiter**
```

## Game Flow

1. **Team Selection**: Players can view existing teams and either join one or create a new team
2. **Player Registration**: When joining/creating a team, players provide their name
3. **Question Display**: Questions are presented one at a time to all teams
4. **Answer Submission**: Teams submit their answers
5. **Real-time Scoring**: Scores update live for all participants
6. **Scoreboard**: View current standings after each question

## Technical Architecture

- **Backend**: Flask with SocketIO for real-time communication
- **Frontend**: HTML/CSS/JavaScript with Socket.IO client
- **Data Storage**: In-memory (suitable for single-session games)
- **Question Parser**: Custom markdown parser supporting multiple formats

## File Structure

```
trivia-app/
├── app.py                 # Main Flask application
├── models.py             # Data models (Team, Question, TriviaGame)
├── trivia_parser.py      # Markdown question parser
├── requirements.txt      # Python dependencies
├── questions.md          # Sample trivia questions
├── venv/                 # Python virtual environment (created during setup)
├── templates/
│   ├── index.html        # Team selection page
│   └── game.html         # Game interface
└── static/
    ├── css/
    │   └── style.css     # Application styles
    └── js/
        ├── index.js      # Team selection logic
        └── game.js       # Game interface logic
```

## Requirements

- Python 3.7+
- Virtual environment (venv)
- Modern web browser with JavaScript enabled