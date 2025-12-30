"""
Enhanced CalOmr Pipeline with multi-question support and web search
"""
import time
from typing import Dict, List
from pathlib import Path

from multi_question_solver import GroqMultiQuestionSolver
from web_search import WebSearcher
from database import DatabaseManager
from config import Config


class EnhancedCalOmrPipeline:
    """Enhanced pipeline for solving multiple STEM questions with web search"""
    
    def __init__(self):
        """Initialize pipeline components"""
        print("🚀 Initializing Enhanced CalOmr Pipeline...")
        
        print("  ⚡ Loading multi-question solver...")
        self.groq_solver = GroqMultiQuestionSolver()
        
        print("  🌐 Loading web searcher...")
        self.web_searcher = WebSearcher()
        
        print("  🗄️  Connecting to database...")
        self.db = DatabaseManager()
        
        print("✓ Enhanced pipeline ready!\n")
    
    def solve_all_questions(self, image_path: str) -> List[Dict]:
        """
        Solve ALL questions from an image
        
        Strategy:
        1. Parse all questions from image
        2. For each question:
           a. Check database cache
           b. If not found, search web
           c. If not found, calculate with AI
           d. Store result in database
        
        Args:
            image_path: Path to question image
            
        Returns:
            List of solutions for all questions
        """
        start_time = time.time()
        
        try:
            # Validate image
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            print("="*70)
            print("🔍 STEP 1: PARSING ALL QUESTIONS FROM IMAGE")
            print("="*70)
            
            parse_start = time.time()
            all_questions = self.groq_solver.parse_all_questions(image_path)
            parse_time = time.time() - parse_start
            
            print(f"✓ Found {len(all_questions)} questions in {parse_time:.2f}s")
            
            if not all_questions:
                raise ValueError("No questions found in image")
            
            # Process each question
            results = []
            
            for idx, question_data in enumerate(all_questions, 1):
                print(f"\n{'='*70}")
                print(f"📝 PROCESSING QUESTION {idx}/{len(all_questions)}")
                print(f"   Number: {question_data.get('question_number', 'N/A')}")
                print(f"   Subject: {question_data.get('subject', 'Unknown').upper()}")
                print(f"{'='*70}")
                
                try:
                    result = self._solve_single_question(question_data)
                    results.append(result)
                    
                    print(f"\n✓ Question {idx} solved: Answer = {result['answer']} "
                          f"(Confidence: {result['confidence']}%, Method: {result['source']})")
                except Exception as e:
                    print(f"\n❌ Failed to solve question {idx}: {e}")
                    # Add a placeholder result so we don't skip the question
                    results.append({
                        'answer': 'ERROR',
                        'confidence': 0,
                        'reasoning': f'Failed to solve: {str(e)}',
                        'source': 'error',
                        'question_data': question_data
                    })
            
            total_time = time.time() - start_time
            
            print(f"\n{'='*70}")
            print(f"✅ ALL QUESTIONS SOLVED!")
            print(f"   Total questions: {len(results)}")
            print(f"   Total time: {total_time:.2f}s")
            print(f"   Average per question: {total_time/len(results):.2f}s")
            print(f"{'='*70}\n")
            
            return {
                'questions': results,
                'total_questions': len(results),
                'total_time_seconds': total_time,
                'parse_time_seconds': parse_time
            }
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            raise
    
    def _solve_single_question(self, question_data: Dict) -> Dict:
        """
        Solve a single question using the 3-tier strategy
        
        Tier 1: Check database cache
        Tier 2: Search web for exact match
        Tier 3: Calculate with AI
        
        Args:
            question_data: Parsed question data
            
        Returns:
            Solution dictionary
        """
        question_text = question_data['question_text']
        question_number = question_data.get('question_number')
        
        # TIER 1: Check database cache
        print("\n🗄️  Tier 1: Checking database cache...")
        
        db_start = time.time()
        rag_result = self.db.search_similar_questions(
            question_text,
            question_data.get('equations', []),
            question_data.get('subject', 'math')
        )
        db_time = time.time() - db_start
        
        if rag_result and rag_result['confidence'] >= Config.HIGH_CONFIDENCE_THRESHOLD * 100:
            print(f"✓ Found in database! (Confidence: {rag_result['confidence']:.1f}%)")
            
            return {
                **rag_result,
                'question_data': question_data,
                'source': 'database_cache',
                'db_search_time': db_time
            }
        
        print(f"❌ Not in database (searched in {db_time:.2f}s)")
        
        # TIER 2: Search web for exact match (DISABLED - too slow with low success rate)
        # Uncommment below to enable web search
        # print("\n🌐 Tier 2: Searching web for exact match...")
        # web_start = time.time()
        # web_result = self.web_searcher.search_question(question_text, question_number)
        # web_time = time.time() - web_start
        # if web_result:
        #     print(f"✓ Found on web! (Source: {web_result['source'][:50]}...)")
        #     self._store_in_database(question_data, web_result)
        #     return {...web_result, 'question_data': question_data, 'web_search_time': web_time}
        # print(f"❌ Not found on web (searched in {web_time:.2f}s)")
        print("\n⚡ Tier 2: Web search disabled (using AI solver)")
        
        # TIER 3: Calculate with AI
        print("\n⚡ Tier 3: Calculating with Groq AI...")
        
        solve_start = time.time()
        solution = self.groq_solver.solve_question(question_data)
        solve_time = time.time() - solve_start
        
        print(f"✓ Calculated answer (Time: {solve_time:.2f}s, Confidence: {solution['confidence']}%)")
        
        # Store in database
        self._store_in_database(question_data, solution)
        
        return {
            **solution,
            'question_data': question_data,
            'solve_time': solve_time
        }
    
    def _store_in_database(self, question_data: Dict, solution: Dict):
        """Store question and answer in database"""
        try:
            self.db.store_question(
                question_data,
                solution['answer'],
                solution.get('reasoning', ''),
                solution.get('confidence', 85),
                int(solution.get('solve_time', 0) * 1000),  # solve_time_ms
                solution.get('source', 'groq_solved')  # solved_by
            )
            print("💾 Stored in database for future use")
        except Exception as e:
            print(f"❌ Error storing question: {e}")
