"""
Enhanced Groq solver with multi-question parsing
"""
from groq import Groq
from typing import Dict, List, Optional
import json
import base64
import re
from config import Config


class GroqMultiQuestionSolver:
    """Enhanced solver that handles multiple questions from one image"""
    
    def __init__(self):
        """Initialize Groq client"""
        self.client = Groq(api_key=Config.GROQ_API_KEY)
    
    def parse_all_questions(self, image_path: str) -> List[Dict]:
        """
        Parse ALL questions from an image
        
        Args:
            image_path: Path to the question image
            
        Returns:
            List of parsed question data
        """
        try:
            # Read and encode image
            with open(image_path, 'rb') as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Create vision prompt for multiple questions
            response = self.client.chat.completions.create(
                model=Config.GROQ_VISION_MODEL,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analyze this image and extract ALL questions visible. For each question, return ONLY valid JSON array (no markdown, no extra text):

[
  {
    "question_number": "27",
    "subject": "physics",
    "topic": "electricity",
    "question_text": "complete question text",
    "equations": ["LaTeX equation if any"],
    "options": {
      "A": "option A text",
      "B": "option B text",
      "C": "option C text",
      "D": "option D text"
    },
    "difficulty": "medium",
    "keywords": ["keyword1", "keyword2"]
  },
  ... (more questions)
]

CRITICAL INSTRUCTIONS:
- Extract EVERY question you see in the image
- Include question numbers (e.g., "27", "28", "29")
- Extract ALL option texts completely and accurately
- Include scientific notation and equations in LaTeX
- Classify subject accurately (math/physics/chemistry)
- Return ONLY the JSON array, nothing else
- If equations use special symbols, convert to LaTeX"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}"
                            }
                        }
                    ]
                }],
                temperature=0.1,
                max_tokens=8000  # Increased for multiple questions
            )
            
            # Parse response
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'\s*```$', '', content)
            
            # Parse JSON
            questions_data = json.loads(content)
            
            # Validate it's a list
            if not isinstance(questions_data, list):
                questions_data = [questions_data]
            
            # Validate each question
            valid_questions = []
            for q in questions_data:
                if self._validate_question(q):
                    valid_questions.append(q)
            
            print(f"✓ Extracted {len(valid_questions)} questions from image")
            return valid_questions
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"Response was: {content[:300]}")
            # Fallback: try to parse as single question
            return self._parse_as_single_question(image_path)
        except Exception as e:
            print(f"❌ Error parsing image: {e}")
            raise
    
    def _validate_question(self, q: Dict) -> bool:
        """Validate a question has required fields"""
        required = ['question_text', 'options']
        for field in required:
            if field not in q:
                return False
        
        # Ensure subject is valid
        if 'subject' in q and q['subject'] not in Config.SUPPORTED_SUBJECTS:
            q['subject'] = 'math'  # Default
        
        return True
    
    def _parse_as_single_question(self, image_path: str) -> List[Dict]:
        """Fallback: parse as single question"""
        try:
            with open(image_path, 'rb') as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            
            response = self.client.chat.completions.create(
                model=Config.GROQ_VISION_MODEL,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Extract the FIRST visible question. Return ONLY valid JSON:

{
  "question_number": "number or null",
  "subject": "math or physics or chemistry",
  "topic": "specific topic",
  "question_text": "complete question",
  "equations": ["equations if any"],
  "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
  "difficulty": "easy/medium/hard",
  "keywords": ["keyword1", "keyword2"]
}"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}"
                            }
                        }
                    ]
                }],
                temperature=0.1,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'\s*```$', '', content)
            
            question_data = json.loads(content)
            return [question_data] if self._validate_question(question_data) else []
            
        except:
            return []
    
    def solve_question(self, question_data: Dict) -> Dict:
        """
        Solve a single question using Groq
        
        Args:
            question_data: Parsed question data
            
        Returns:
            Solution with answer, reasoning, and confidence
        """
        try:
            # Select model based on difficulty
            if question_data.get('difficulty') == 'hard':
                model = Config.GROQ_REASONING_MODEL
            else:
                model = Config.GROQ_MATH_MODEL
            
            # Format equations
            equations_str = ""
            if question_data.get('equations'):
                equations_str = "\n**Equations:**\n" + "\n".join(
                    [f"- ${eq}$" for eq in question_data['equations']]
                )
            
            # Format options
            options_str = "\n".join(
                [f"**{key}:** {value}" for key, value in question_data['options'].items()]
            )
            
            # Create solving prompt
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": f"""You are an expert {question_data.get('subject', 'STEM')} professor with deep knowledge of fundamental concepts.

**CRITICAL INSTRUCTIONS:**
1. Read the question VERY carefully - understand what is actually being asked
2. Identify the core physics/chemistry/math concept being tested
3. Apply fundamental laws and principles correctly
4. For physics: Consider laws like Ohm's law, Kirchhoff's laws, conservation principles, etc.
5. For conceptual questions: Think about the underlying theory, not just formulas
6. Verify your answer against the concept - does it make physical/logical sense?
7. If unsure between options, explain why each is right or wrong
8. Final answer MUST be A, B, C, or D only
9. Provide confidence: 95-100 for certain, 80-90 for likely, 60-75 for uncertain

**COMMON MISTAKES TO AVOID:**
- Not reading the full question carefully
- Confusing similar concepts (e.g., constant current vs constant voltage)
- Not considering all given conditions
- Rushing to answer without verification

**PHYSICS CONCEPT REMINDERS:**
- Kirchhoff's Current Law (KCL): Conservation of CHARGE (not energy)
- Kirchhoff's Voltage Law (KVL): Conservation of ENERGY
- Constant current source: Needs VERY LARGE internal resistance
- Constant voltage source: Needs VERY SMALL internal resistance
- Maximum power transfer: Load resistance = Source resistance (R=r)
- Non-ohmic: Diode, transistor, thermistor (V-I not linear)
- Ohmic: Resistor, wire (V-I linear, follows Ohm's law)

Solve systematically with clear reasoning."""
                    },
                    {
                        "role": "user",
                        "content": f"""**Question {question_data.get('question_number', '')}:**
{question_data['question_text']}
{equations_str}

**Options:**
{options_str}

**Subject:** {question_data.get('subject', 'General').title()}
**Topic:** {question_data.get('topic', 'General')}

**Instructions:**
1. First, identify what concept/law/principle is being tested
2. Then analyze each option carefully
3. Apply the relevant theory/formula correctly
4. Eliminate wrong answers with reasoning
5. Select the correct answer with confidence

**Required Format:**
CONCEPT: [What is being tested - be specific]
ANALYSIS: [Analyze the question and each option]
SOLUTION: [Apply theory step-by-step]
VERIFICATION: [Why this answer is correct and others are wrong]
ANSWER: [A/B/C/D only]
CONFIDENCE: [0-100 number only]"""
                    }
                ],
                temperature=Config.SOLVING_TEMPERATURE,
                max_tokens=2500
            )
            
            result = response.choices[0].message.content
            
            # Parse answer and confidence with multiple patterns
            answer_match = re.search(r'ANSWER:\s*([A-D])\b', result, re.IGNORECASE)
            confidence_match = re.search(r'CONFIDENCE:\s*(\d+)', result)
            
            if not answer_match:
                # Try many alternative patterns
                patterns = [
                    r'answer\s+is\s+([A-D])\b',
                    r'correct\s+answer:\s*([A-D])\b',
                    r'option\s+([A-D])\s+is\s+correct',
                    r'the\s+answer\s+is\s+([A-D])\b',
                    r'answer:\s*option\s+([A-D])\b',
                    r'\(([A-D])\)\s+is\s+correct',
                    r'select\s+([A-D])\b',
                    r'choose\s+([A-D])\b',
                    r'\b([A-D])\s+is\s+the\s+correct',
                    r'final\s+answer:\s*([A-D])\b',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, result, re.IGNORECASE)
                    if match:
                        answer_match = match
                        break
            
            if not answer_match:
                # Last resort: find any standalone A, B, C, or D near end of text
                last_500 = result[-500:]
                match = re.search(r'\b([A-D])\b(?!.*\b[A-D]\b)', last_500)
                if match:
                    answer_match = match
            
            if not answer_match:
                print(f"⚠️  Could not extract answer. Response: {result[:300]}...")
                # Default to A with low confidence rather than failing
                return {
                    'answer': 'A',
                    'reasoning': result,
                    'confidence': 50,
                    'model_used': model,
                    'source': 'groq_solved_uncertain'
                }
            
            answer = answer_match.group(1).upper()
            confidence = int(confidence_match.group(1)) if confidence_match else 85
            
            return {
                'answer': answer,
                'reasoning': result,
                'confidence': confidence,
                'model_used': model,
                'source': 'groq_solved'
            }
            
        except Exception as e:
            print(f"❌ Error solving question: {e}")
            raise
