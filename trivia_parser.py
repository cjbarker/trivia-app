import re
from models import Question

class TriviaParser:
    def __init__(self, file_path):
        self.file_path = file_path
    
    def parse(self):
        questions = []
        
        with open(self.file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Split content by question markers
        question_blocks = self._split_questions(content)
        
        for block in question_blocks:
            question = self._parse_question_block(block)
            if question:
                questions.append(question)
        
        return questions
    
    def _split_questions(self, content):
        # Split by markdown headers (## or ###) or numbered questions
        patterns = [
            r'\n##\s+',  # ## headers
            r'\n###\s+', # ### headers  
            r'\n\d+\.\s+', # Numbered questions like "1. "
            r'\n\*\*Question\s+\d+\*\*', # **Question 1**
        ]
        
        for pattern in patterns:
            if re.search(pattern, content):
                blocks = re.split(pattern, content)
                # Remove empty blocks and header-only blocks, return non-empty ones
                filtered_blocks = []
                for block in blocks:
                    block = block.strip()
                    # Skip empty blocks and header-only blocks (like "# Sample Trivia Questions")
                    if block and not re.match(r'^#[^#].*$', block):
                        filtered_blocks.append(block)
                return filtered_blocks
        
        # If no clear separators found, treat as single question
        return [content.strip()] if content.strip() else []
    
    def _parse_question_block(self, block):
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        
        if not lines:
            return None
        
        # First line is typically the question
        question_text = lines[0]
        
        # Clean up common question prefixes
        question_text = re.sub(r'^(Question\s+\d+[:\.]?\s*)', '', question_text, flags=re.IGNORECASE)
        question_text = re.sub(r'^\d+\.\s*', '', question_text)
        question_text = re.sub(r'^\*\*(.*?)\*\*', r'\1', question_text)
        
        # Determine question type and parse accordingly
        if self._is_multiple_choice(lines):
            return self._parse_multiple_choice(question_text, lines)
        else:
            return self._parse_fill_in_blank(question_text, lines)
    
    def _is_multiple_choice(self, lines):
        # Look for option patterns like A), a), 1), - A), etc.
        option_patterns = [
            r'^\s*[A-Da-d]\)\s+',
            r'^\s*[1-4]\)\s+',
            r'^\s*-\s*[A-Da-d][\)\.]?\s+',
            r'^\s*\*\s*[A-Da-d][\)\.]?\s+',
        ]
        
        for line in lines[1:]:  # Skip first line (question)
            for pattern in option_patterns:
                if re.match(pattern, line):
                    return True
        return False
    
    def _parse_multiple_choice(self, question_text, lines):
        options = []
        correct_answer = None
        
        option_patterns = [
            r'^[A-Da-d]\)\s+(.+)',
            r'^[1-4]\)\s+(.+)',
            r'^-\s*[A-Da-d][\)\.]?\s+(.+)',
            r'^\*\s*[A-Da-d][\)\.]?\s+(.+)',
        ]
        
        for line in lines[1:]:
            option_text = None
            option_label = None
            
            # Try to match option patterns
            for pattern in option_patterns:
                match = re.match(pattern, line)
                if match:
                    option_text = match.group(1).strip()
                    # Extract option label (A, B, C, D, etc.)
                    label_match = re.match(r'^([A-Da-d1-4])', line)
                    if label_match:
                        option_label = label_match.group(1).upper()
                    break
            
            if option_text:
                # Clean up bold formatting from option text
                clean_option_text = re.sub(r'^\*\*(.*?)\*\*$', r'\1', option_text)
                options.append(clean_option_text)
                
                # Check if this option is marked as correct
                if self._is_marked_correct(line):
                    correct_answer = clean_option_text
        
        # If no option was marked correct, look for separate answer line
        if correct_answer is None:
            correct_answer = self._find_answer_in_lines(lines)
        
        return Question(question_text, 'multiple_choice', options, correct_answer)
    
    def _parse_fill_in_blank(self, question_text, lines):
        # Look for answer in subsequent lines
        correct_answer = self._find_answer_in_lines(lines)
        
        return Question(question_text, 'fill_in_blank', [], correct_answer)
    
    def _is_marked_correct(self, line):
        # Check for various ways to mark correct answers
        markers = [
            r'\*\*.*?\*\*',  # **bold**
            r'_.*?_',        # _italic_
            r'\(correct\)',  # (correct)
            r'\[correct\]',  # [correct]
            r'✓',            # checkmark
        ]
        
        for marker in markers:
            if re.search(marker, line, re.IGNORECASE):
                return True
        return False
    
    def _find_answer_in_lines(self, lines):
        # Look for lines that indicate the answer
        answer_patterns = [
            r'^Answer:\s*(.+)',
            r'^Correct\s*Answer:\s*(.+)',
            r'^Solution:\s*(.+)',
            r'^\*\*Answer\*\*:\s*(.+)',
            r'^\*\*Answer:\s*(.+?)\*\*$',  # **Answer: text**
        ]
        
        for line in lines:
            for pattern in answer_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    answer = match.group(1).strip()
                    # Remove bold formatting if present
                    answer = re.sub(r'^\*\*(.*?)\*\*$', r'\1', answer)
                    return answer
        
        return None