"""
CalOmr - Complete Question Solving Pipeline
Combines Groq Vision + RAG (Supabase) for efficient STEM question solving
"""
import time
from typing import Dict, Optional
from pathlib import Path

from groq_solver import GroqSolver
from database import DatabaseManager
from config import Config


class CalOmrPipeline:
    """Main pipeline for solving STEM questions"""
    
    def __init__(self):
        """Initialize pipeline components"""
        print("🚀 Initializing CalOmr Pipeline...")
        
        # Initialize Groq solver
        print("  ⚡ Loading Groq solver...")
        self.groq_solver = GroqSolver()
        
        # Initialize database
        print("  🗄️  Connecting to Supabase...")
        self.db = DatabaseManager()
        
        print("✓ Pipeline ready!\n")
    
    def solve_question(self, image_path: str, verify: bool = False) -> Dict:
        """
        Solve a question from an image
        
        Args:
            image_path: Path to question image
            verify: Whether to verify answer with fast model
            
        Returns:
            Complete solution with answer, reasoning, and metadata
        """
        start_time = time.time()
        question_id = None
        cache_hit = False
        
        try:
            # Validate image exists
            if not Path(image_path).exists():
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            print("="*70)
            print("🔍 STEP 1: PARSING IMAGE WITH GROQ VISION")
            print("="*70)
            
            parse_start = time.time()
            question_data = self.groq_solver.parse_image(image_path)
            parse_time = time.time() - parse_start
            
            print(f"✓ Parsed in {parse_time:.2f}s")
            print(f"\n📚 Subject: {question_data['subject'].upper()}")
            print(f"📖 Topic: {question_data.get('topic', 'General')}")
            print(f"💪 Difficulty: {question_data.get('difficulty', 'Unknown')}")
            print(f"\n❓ Question: {question_data['question_text'][:150]}...")
            
            if question_data.get('equations'):
                print(f"📐 Equations: {len(question_data['equations'])} found")
            
            print(f"\n🔘 Options: {', '.join(question_data['options'].keys())}")
            
            # STEP 2: Search database for similar questions (RAG)
            print("\n" + "="*70)
            print("🗄️  STEP 2: SEARCHING RAG DATABASE")
            print("="*70)
            
            db_start = time.time()
            rag_result = self.db.search_similar_questions(
                question_data['question_text'],
                question_data.get('equations', []),
                question_data['subject']
            )
            db_time = time.time() - db_start
            
            print(f"✓ Searched in {db_time:.2f}s")
            
            # If found in database with high confidence, use it
            if rag_result and rag_result['confidence'] >= Config.HIGH_CONFIDENCE_THRESHOLD * 100:
                cache_hit = True
                total_time = time.time() - start_time
                
                print(f"\n🎯 FOUND IN DATABASE!")
                print(f"   Confidence: {rag_result['confidence']:.1f}%")
                print(f"   Similar to: {rag_result.get('similar_question', '')[:100]}...")
                
                # Log the query
                self.db.log_query(None, int(total_time * 1000), cache_hit)
                
                result = {
                    **rag_result,
                    'question_data': question_data,
                    'total_time_seconds': total_time,
                    'parse_time_seconds': parse_time,
                    'db_search_time_seconds': db_time,
                    'solve_time_seconds': 0
                }
                
                self._print_final_result(result)
                return result
            
            print("❌ No high-confidence match in database")
            
            # STEP 3: Solve with Groq
            print("\n" + "="*70)
            print("⚡ STEP 3: SOLVING WITH GROQ AI")
            print("="*70)
            
            solve_start = time.time()
            solution = self.groq_solver.solve_question(question_data)
            solve_time = time.time() - solve_start
            
            print(f"✓ Solved in {solve_time:.2f}s")
            print(f"   Model: {solution['model_used']}")
            print(f"   Initial confidence: {solution['confidence']}%")
            
            # STEP 4: Verify if requested or low confidence
            if verify or solution['confidence'] < 85:
                print("\n" + "="*70)
                print("🔍 STEP 4: VERIFYING ANSWER")
                print("="*70)
                
                verification = self.groq_solver.verify_answer(
                    question_data,
                    solution['answer']
                )
                
                if not verification['is_correct']:
                    print("⚠️  Verification failed - answer may be incorrect")
                    solution['confidence'] = min(solution['confidence'], 60)
                else:
                    print("✓ Answer verified")
                    solution['confidence'] = min(solution['confidence'] + 10, 100)
            
            # STEP 5: Store in database for future RAG
            print("\n" + "="*70)
            print("💾 STEP 5: STORING IN DATABASE")
            print("="*70)
            
            total_solve_time = int((time.time() - start_time) * 1000)
            
            question_id = self.db.store_question(
                question_data,
                solution['answer'],
                solution['reasoning'],
                solution['confidence'],
                total_solve_time,
                f"groq_{solution['model_used']}"
            )
            
            if question_id:
                print(f"✓ Stored with ID: {question_id[:8]}...")
            else:
                print("⚠️  Failed to store (but solution is still valid)")
            
            # Log the query
            total_time = time.time() - start_time
            self.db.log_query(question_id, int(total_time * 1000), cache_hit)
            
            # Compile final result
            result = {
                **solution,
                'question_data': question_data,
                'question_id': question_id,
                'total_time_seconds': total_time,
                'parse_time_seconds': parse_time,
                'db_search_time_seconds': db_time,
                'solve_time_seconds': solve_time
            }
            
            self._print_final_result(result)
            return result
            
        except Exception as e:
            total_time = int((time.time() - start_time) * 1000)
            self.db.log_query(question_id, total_time, cache_hit, str(e))
            print(f"\n❌ ERROR: {e}")
            raise
    
    def _print_final_result(self, result: Dict):
        """Print formatted final result"""
        print("\n" + "="*70)
        print("✅ FINAL RESULT")
        print("="*70)
        print(f"\n🎯 ANSWER: {result['answer']}")
        print(f"📊 Confidence: {result['confidence']}%")
        print(f"⚡ Total Time: {result['total_time_seconds']:.2f}s")
        print(f"🔧 Method: {result['source']}")
        
        if result['source'] != 'rag_database':
            print(f"\n💡 REASONING:")
            # Print first few lines of reasoning
            reasoning_lines = result['reasoning'].split('\n')[:8]
            for line in reasoning_lines:
                if line.strip():
                    print(f"   {line}")
            if len(result['reasoning'].split('\n')) > 8:
                print("   ...")
        
        print("\n" + "="*70)
    
    def get_statistics(self) -> Dict:
        """Get pipeline statistics"""
        return self.db.get_statistics()
    
    def batch_solve(self, image_paths: list) -> list:
        """
        Solve multiple questions
        
        Args:
            image_paths: List of image paths
            
        Returns:
            List of results
        """
        results = []
        total = len(image_paths)
        
        print(f"\n🔄 Batch solving {total} questions...\n")
        
        for i, path in enumerate(image_paths, 1):
            print(f"\n{'='*70}")
            print(f"Question {i}/{total}: {Path(path).name}")
            print('='*70)
            
            try:
                result = self.solve_question(path)
                results.append(result)
            except Exception as e:
                print(f"❌ Failed: {e}")
                results.append({'error': str(e), 'image_path': path})
        
        # Print summary
        print("\n" + "="*70)
        print("📊 BATCH SUMMARY")
        print("="*70)
        
        successful = sum(1 for r in results if 'answer' in r)
        cache_hits = sum(1 for r in results if r.get('source') == 'rag_database')
        
        print(f"Total: {total}")
        print(f"Successful: {successful}")
        print(f"Cache Hits: {cache_hits} ({cache_hits/total*100:.1f}%)")
        
        return results


def main():
    """Main entry point for CLI"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python main.py <image_path>")
        print("   or: python main.py <image1> <image2> ... (batch mode)")
        sys.exit(1)
    
    # Initialize pipeline
    pipeline = CalOmrPipeline()
    
    # Get image paths
    image_paths = sys.argv[1:]
    
    if len(image_paths) == 1:
        # Single question mode
        result = pipeline.solve_question(image_paths[0])
        print(f"\n📋 Answer: {result['answer']}")
    else:
        # Batch mode
        results = pipeline.batch_solve(image_paths)
        
        # Print answers
        print("\n📋 ANSWERS:")
        for i, (path, result) in enumerate(zip(image_paths, results), 1):
            if 'answer' in result:
                print(f"{i}. {Path(path).name}: {result['answer']}")
            else:
                print(f"{i}. {Path(path).name}: ERROR")


if __name__ == "__main__":
    main()
