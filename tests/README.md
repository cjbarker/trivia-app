# Trivia Application Tests

This directory contains all test files for the trivia application.

## Test Files

### Python Tests
- `test_admin.py` - Tests admin login and game control functionality
- `test_answer_restrictions.py` - Tests answer submission restrictions (no re-answering)
- `test_pause.py` - Tests pause/resume functionality with WebSocket events
- `test_team_management.py` - Comprehensive team management tests
- `test_team_simple.py` - Basic team functionality tests
- `test_team_simple_mgmt.py` - Simple team management tests
- `test_team_validation.py` - Team membership validation tests

### HTML Test Interfaces
- `test_team_ui.html` - Interactive team management testing interface
- `test_ui_answers.html` - Interactive answer restriction testing interface  
- `test_ui_pause.html` - Interactive pause/resume testing interface

## Running Tests

### Run Individual Tests
```bash
# From the project root directory
source venv/bin/activate
python tests/test_admin.py
```

### Run All Tests
```bash
# From the project root directory
source venv/bin/activate
python run_tests.py
```

### Interactive Testing
Open the HTML test files in a browser while the application is running:
```bash
# Start the application
source venv/bin/activate
python app.py

# Open test interfaces
open tests/test_team_ui.html
open tests/test_ui_answers.html
open tests/test_ui_pause.html
```

## Test Requirements

Before running tests, make sure:
1. The trivia application is running (`python app.py`)
2. The virtual environment is activated (`source venv/bin/activate`)
3. Required dependencies are installed (`pip install -r requirements.txt`)

## Known Issues

- `test_team_validation.py` has one expected failure in multi-session validation
- `test_answer_restrictions.py` may fail if answer state is not properly maintained across question navigation