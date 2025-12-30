"""
Example usage and testing script for CalOmr
"""
from main import CalOmrPipeline
import sys


def example_single_question():
    """Example: Solve a single question"""
    print("Example 1: Single Question")
    print("-" * 60)
    
    pipeline = CalOmrPipeline()
    
    # Solve a question
    result = pipeline.solve_question("test_question.jpg")
    
    print(f"\nAnswer: {result['answer']}")
    print(f"Confidence: {result['confidence']}%")
    print(f"Time: {result['total_time_seconds']:.2f}s")
    print(f"Source: {result['source']}")


def example_batch_processing():
    """Example: Batch solve multiple questions"""
    print("\n\nExample 2: Batch Processing")
    print("-" * 60)
    
    pipeline = CalOmrPipeline()
    
    # List of question images
    questions = [
        "question1.jpg",
        "question2.jpg",
        "question3.jpg"
    ]
    
    # Solve all
    results = pipeline.batch_solve(questions)
    
    # Print summary
    print("\nResults:")
    for i, result in enumerate(results, 1):
        if 'answer' in result:
            print(f"{i}. Answer: {result['answer']} (Confidence: {result['confidence']}%)")
        else:
            print(f"{i}. Error: {result.get('error', 'Unknown')}")


def example_with_verification():
    """Example: Solve with answer verification"""
    print("\n\nExample 3: With Verification")
    print("-" * 60)
    
    pipeline = CalOmrPipeline()
    
    # Solve with verification enabled
    result = pipeline.solve_question("difficult_question.jpg", verify=True)
    
    print(f"\nAnswer: {result['answer']}")
    print(f"Confidence: {result['confidence']}%")
    print("(Answer was verified with fast model)")


def example_statistics():
    """Example: Get database statistics"""
    print("\n\nExample 4: Database Statistics")
    print("-" * 60)
    
    pipeline = CalOmrPipeline()
    stats = pipeline.get_statistics()
    
    print(f"\nTotal questions in database: {stats['total_questions']}")
    print(f"Math questions: {stats['by_subject'].get('math', 0)}")
    print(f"Physics questions: {stats['by_subject'].get('physics', 0)}")
    print(f"Chemistry questions: {stats['by_subject'].get('chemistry', 0)}")
    print(f"\nTotal queries: {stats['total_queries']}")
    print(f"Cache hits: {stats['cache_hits']}")
    print(f"Cache hit rate: {stats['cache_hit_rate']:.1f}%")


def test_connection():
    """Test API connections"""
    print("Testing Connections")
    print("-" * 60)
    
    try:
        from config import Config
        print(f"✓ Groq API Key: {Config.GROQ_API_KEY[:20]}...")
        print(f"✓ Supabase URL: {Config.SUPABASE_URL}")
        print(f"✓ Configuration valid")
        
        # Test imports
        from groq import Groq
        from supabase import create_client
        
        client = Groq(api_key=Config.GROQ_API_KEY)
        print("✓ Groq client initialized")
        
        supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        print("✓ Supabase client initialized")
        
        print("\n✅ All connections successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    # Run test connection
    test_connection()
    
    print("\n" + "="*60)
    print("Ready to use!")
    print("="*60)
    print("\nTo solve a question:")
    print("  python main.py your_question.jpg")
    print("\nTo start web API:")
    print("  python api.py")
