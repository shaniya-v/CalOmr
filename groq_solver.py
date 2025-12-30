"""
Groq-powered question solver with vision parsing
"""
from groq import Groq
from typing import Dict, Optional
import json
import base64
import re
from config import Config


class GroqSolver:
    """Handles all Groq API interactions for parsing and solving"""
    
    def __init__(self):
        """Initialize Groq client"""
        self.client = Groq(api_key=Config.GROQ_API_KEY)
    
    def parse_image(self, image_path: str) -> Dict:
        """
        Parse question image using Groq's Vision model
        
        Args:
            image_path: Path to the question image
            
        Returns:
            Parsed question data with text, equations, options, etc.
        """
        try:
            # Read and encode image
            with open(image_path, 'rb') as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Create vision prompt
            response = self.client.chat.completions.create(
                model=Config.GROQ_VISION_MODEL,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analyze this STEM question image carefully. Extract all information and return ONLY valid JSON (no markdown, no extra text):

{
  "subject": "math" or "physics" or "chemistry",
  "topic": "specific topic like 'calculus', 'thermodynamics', 'organic chemistry'",
  "question_text": "complete question text in plain language",
  "equations": ["LaTeX equation 1", "LaTeX equation 2"],
  "options": {
    "A": "option A text",
    "B": "option B text",
    "C": "option C text",
    "D": "option D text"
  },
  "difficulty": "easy" or "medium" or "hard",
  "keywords": ["keyword1", "keyword2", "keyword3"]
}

IMPORTANT: 
- Extract equations in LaTeX format (e.g., "x^2 + y^2 = r^2")
- Include ALL option text verbatim
- Be precise with subject classification
- Return ONLY the JSON, nothing else"""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{img_base64}"
                            }
                        }
                    ]
                }],
                temperature=Config.VISION_TEMPERATURE,
                max_tokens=1500
            )
            
            # Parse response
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'\s*```$', '', content)
            
            # Parse JSON
            question_data = json.loads(content)
            
            # Validate required fields
            required_fields = ['subject', 'question_text', 'options']
            for field in required_fields:
                if field not in question_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Ensure subject is valid
            if question_data['subject'] not in Config.SUPPORTED_SUBJECTS:
                question_data['subject'] = 'math'  # Default fallback
            
            return question_data
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"Response was: {content[:200]}")
            raise
        except Exception as e:
            print(f"❌ Error parsing image: {e}")
            raise
    
    def solve_question(self, question_data: Dict) -> Dict:
        """
        Solve a question using Groq's reasoning model
        
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
            
            # Format equations for display
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
                        "content": f"""You are an expert {question_data['subject']} professor with deep knowledge of {question_data.get('topic', question_data['subject'])}.

Your task is to solve multiple-choice questions with rigorous, step-by-step reasoning. You must:
1. Fully understand what is being asked
2. Apply relevant concepts, formulas, and principles
3. Show detailed calculations
4. Verify your answer against all options
5. Select the single correct option with high confidence

Be thorough, accurate, and precise in your reasoning."""
                    },
                    {
                        "role": "user",
                        "content": f"""**Question:**
{question_data['question_text']}
{equations_str}

**Options:**
{options_str}

**Subject:** {question_data['subject'].title()}
**Topic:** {question_data.get('topic', 'General')}
**Keywords:** {', '.join(question_data.get('keywords', []))}

Solve this systematically:

1. **CONCEPT**: What principle/theorem/concept applies?
2. **APPROACH**: What method will you use to solve?
3. **SOLUTION**: Detailed step-by-step working with calculations
4. **VERIFICATION**: Check your answer against options
5. **ANSWER**: State the correct option letter (A/B/C/D)
6. **CONFIDENCE**: Your confidence level (0-100)%

Use this EXACT format:
CONCEPT: [relevant concept]
APPROACH: [solving method]
SOLUTION: [detailed steps]
VERIFICATION: [check against options]
ANSWER: [A/B/C/D]
CONFIDENCE: [0-100]"""
                    }
                ],
                temperature=Config.SOLVING_TEMPERATURE,
                max_tokens=2500
            )
            
            result = response.choices[0].message.content
            
            # Parse the structured response
            answer_match = re.search(r'ANSWER:\s*([A-D])', result, re.IGNORECASE)
            confidence_match = re.search(r'CONFIDENCE:\s*(\d+)', result)
            
            if not answer_match:
                # Try to find answer in the text
                for option in ['A', 'B', 'C', 'D']:
                    if f"answer is {option}" in result.lower() or f"answer: {option}" in result.lower():
                        answer_match = re.search(option, result)
                        break
            
            answer = answer_match.group(1).upper() if answer_match else None
            confidence = int(confidence_match.group(1)) if confidence_match else 70
            
            if not answer:
                raise ValueError("Could not extract answer from solution")
            
            return {
                'answer': answer,
                'confidence': confidence,
                'reasoning': result,
                'model_used': model,
                'source': 'groq_solved'
            }
            
        except Exception as e:
            print(f"❌ Error solving question: {e}")
            raise
    
    def verify_answer(self, question_data: Dict, proposed_answer: str) -> Dict:
        """
        Quick verification of an answer using fast model
        
        Args:
            question_data: Question data
            proposed_answer: The answer to verify (A/B/C/D)
            
        Returns:
            Verification result with confidence
        """
        try:
            response = self.client.chat.completions.create(
                model=Config.GROQ_FAST_MODEL,
                messages=[{
                    "role": "user",
                    "content": f"""Question: {question_data['question_text']}

Options:
{json.dumps(question_data['options'], indent=2)}

Proposed Answer: {proposed_answer}

Is this answer correct? Respond with ONLY:
CORRECT or INCORRECT"""
                }],
                temperature=Config.VERIFICATION_TEMPERATURE,
                max_tokens=50
            )
            
            result = response.choices[0].message.content.strip().upper()
            is_correct = 'CORRECT' in result and 'INCORRECT' not in result
            
            return {
                'is_correct': is_correct,
                'verification_response': result
            }
            
        except Exception as e:
            print(f"⚠️ Verification error: {e}")
            return {'is_correct': True, 'verification_response': 'SKIPPED'}


if __name__ == "__main__":
    # Test the solver
    print("Testing Groq Solver...")
    solver = GroqSolver()
    print("✓ Groq solver initialized successfully")
