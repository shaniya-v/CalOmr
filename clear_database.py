#!/usr/bin/env python3
"""
Clear the database cache to remove incorrect cached answers
"""
from supabase import create_client
from config import Config

print("🗑️  Clearing database cache...")
print(f"   Supabase URL: {Config.SUPABASE_URL}")

try:
    supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
    
    # First delete query_log entries (child table)
    print("   Deleting query logs...")
    supabase.table('query_log').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
    
    # Then delete all questions from the cache (parent table)
    print("   Deleting cached questions...")
    result = supabase.table('questions').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
    
    print(f"\n✅ Database cleared successfully!")
    print(f"   All cached questions and logs removed")
    print(f"\n💡 Now click 'Solve ALL Questions' again - it will:")
    print(f"   • Skip Tier 1 (database cache is empty)")
    print(f"   • Skip Tier 2 (web search disabled)")
    print(f"   • Use Tier 3 (AI with improved prompts)")
    print(f"   • Cache the NEW correct answers")
    
except Exception as e:
    print(f"❌ Error clearing database: {e}")
    print(f"\n📝 Alternative: Go to Supabase dashboard and run:")
    print(f"   DELETE FROM questions;")
