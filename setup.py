#!/usr/bin/env python3
"""
Setup script for CalOmr
"""
import subprocess
import sys
import os
from pathlib import Path


def print_step(step, message):
    """Print formatted step"""
    print(f"\n{'='*70}")
    print(f"STEP {step}: {message}")
    print('='*70)


def check_python_version():
    """Ensure Python version is 3.8+"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")


def install_dependencies():
    """Install Python dependencies"""
    print("Installing dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    print("✓ Dependencies installed")


def check_env_file():
    """Check if .env file exists and has required vars"""
    env_path = Path('.env')
    
    if not env_path.exists():
        print("❌ .env file not found")
        print("\nCreate .env with:")
        print("Groq_API=your_groq_api_key")
        print("SUPABASE_URL=your_supabase_url")
        print("SUPABASE_KEY=your_supabase_key")
        sys.exit(1)
    
    # Check required vars
    with open(env_path) as f:
        content = f.read()
    
    required = ['Groq_API', 'SUPABASE_URL', 'SUPABASE_KEY']
    missing = [var for var in required if var not in content]
    
    if missing:
        print(f"❌ Missing in .env: {', '.join(missing)}")
        sys.exit(1)
    
    print("✓ .env file configured")


def setup_database():
    """Print database setup instructions"""
    print("\n🗄️  DATABASE SETUP")
    print("\nTo set up your Supabase database:")
    print("1. Go to: https://xhfepggdpdwiaoyjlwep.supabase.co")
    print("2. Open SQL Editor")
    print("3. Run the setup SQL:")
    print("\n   python database.py")
    print("\n4. Copy and paste the output into SQL Editor")
    print("5. Execute the SQL")
    
    response = input("\n✓ Have you set up the database? (y/n): ")
    if response.lower() != 'y':
        print("\n⚠️  Database setup required before first use")
        return False
    
    return True


def download_models():
    """Download required models"""
    print("Downloading embedding model...")
    
    # Import will trigger model download
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✓ Embedding model ready")
    except Exception as e:
        print(f"⚠️  Error downloading model: {e}")
        print("Model will download on first use")


def test_connection():
    """Test Groq and Supabase connections"""
    print("Testing connections...")
    
    try:
        from config import Config
        Config.validate()
        print("✓ Configuration valid")
        
        # Test Groq
        from groq import Groq
        client = Groq(api_key=Config.GROQ_API_KEY)
        print("✓ Groq API connected")
        
        # Test Supabase
        from supabase import create_client
        supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        print("✓ Supabase connected")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


def main():
    """Run setup"""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                         CalOmr Setup                              ║
║          AI-Powered STEM Question Solver with RAG                 ║
╚═══════════════════════════════════════════════════════════════════╝
    """)
    
    try:
        print_step(1, "CHECKING PYTHON VERSION")
        check_python_version()
        
        print_step(2, "CHECKING ENVIRONMENT")
        check_env_file()
        
        print_step(3, "INSTALLING DEPENDENCIES")
        install_dependencies()
        
        print_step(4, "DATABASE SETUP")
        db_ready = setup_database()
        
        print_step(5, "DOWNLOADING MODELS")
        download_models()
        
        print_step(6, "TESTING CONNECTIONS")
        connections_ok = test_connection()
        
        # Final summary
        print("\n" + "="*70)
        print("✅ SETUP COMPLETE!")
        print("="*70)
        
        if not db_ready:
            print("\n⚠️  Remember to set up the database before first use")
        
        if connections_ok:
            print("\n🚀 Ready to use! Try:")
            print("\n   python main.py test_image.jpg")
            print("   python api.py  (for web API)")
        else:
            print("\n⚠️  Some connections failed - check your credentials")
        
        print("\n📚 Documentation: README.md")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
