"""
Web search module for finding exact question matches
"""
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import re
import time
from duckduckgo_search import DDGS


class WebSearcher:
    """Search the web for exact question matches and answers"""
    
    def __init__(self):
        """Initialize web searcher"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_question(self, question_text: str, question_number: Optional[str] = None) -> Optional[Dict]:
        """
        Search for exact question match on the web
        
        Args:
            question_text: The question text to search
            question_number: Optional question number (e.g., "27", "Q27")
            
        Returns:
            Dictionary with answer and source if found, None otherwise
        """
        try:
            # Build search query - use more context for better matches
            # Remove special chars that break search
            clean_text = question_text.replace('\n', ' ').replace('  ', ' ').strip()
            query = f'{clean_text[:200]}'
            if question_number:
                query += f' question {question_number} physics'
            
            print(f"🔍 Searching web for: {clean_text[:80]}...")
            
            # Try DuckDuckGo search first
            results = self._search_duckduckgo(query)
            
            if results:
                # First try to extract from snippets (faster)
                for result in results[:5]:
                    snippet_answer = self._extract_answer_from_text(result.get('snippet', ''), question_text)
                    if snippet_answer:
                        print(f"✓ Found answer in search snippet!")
                        return {
                            'answer': snippet_answer['answer'],
                            'reasoning': f"Found in web results: {result.get('title', '')}\n{snippet_answer.get('reasoning', '')}",
                            'source': result['url'],
                            'confidence': snippet_answer.get('confidence', 90),
                            'method': 'web_search'
                        }
                
                # Then try full page scraping
                for result in results[:5]:  # Check top 5 results
                    answer_data = self._extract_answer_from_url(result['url'], question_text)
                    if answer_data:
                        print(f"✓ Found answer on web page!")
                        return {
                            'answer': answer_data['answer'],
                            'reasoning': answer_data.get('reasoning', 'Found on web'),
                            'source': result['url'],
                            'confidence': answer_data.get('confidence', 90),
                            'method': 'web_search'
                        }
            
            print("❌ No exact match found on web")
            return None
            
        except Exception as e:
            print(f"⚠️  Web search error: {e}")
            return None
    
    def _search_duckduckgo(self, query: str) -> List[Dict]:
        """Search using DuckDuckGo"""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=10))
                return [{'url': r['href'], 'title': r['title'], 'snippet': r['body']} for r in results]
        except Exception as e:
            print(f"DuckDuckGo search failed: {e}")
            return []
    
    def _extract_answer_from_text(self, text: str, question_text: str) -> Optional[Dict]:
        """
        Extract answer from text snippet (like search result snippet)
        
        Args:
            text: Text to search in
            question_text: Original question text
            
        Returns:
            Dictionary with answer if found
        """
        if not text:
            return None
        
        text_lower = text.lower()
        
        # Look for answer patterns
        answer_patterns = [
            r'answer\s*[:=is]\s*\(?([A-D])\)?',
            r'correct\s+(?:answer|option)\s*[:=is]\s*\(?([A-D])\)?',
            r'option\s+([A-D])\s+is\s+correct',
            r'\b([A-D])\s+is\s+(?:the\s+)?correct',
            r'(?:answer|solution)\s*[:\-]\s*\(?([A-D])\)?',
            r'the\s+answer\s+is\s+\(?([A-D])\)?'
        ]
        
        for pattern in answer_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                answer = match.group(1).upper()
                return {
                    'answer': answer,
                    'reasoning': text[:200],
                    'confidence': 90
                }
        
        return None
    
    def _extract_answer_from_url(self, url: str, question_text: str) -> Optional[Dict]:
        """
        Try to extract answer from a webpage
        
        Args:
            url: URL to scrape
            question_text: Question text to match
            
        Returns:
            Dictionary with answer and reasoning if found
        """
        try:
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            text = soup.get_text().lower()
            question_lower = question_text.lower()[:100]
            
            # Check if question appears in page
            if question_lower not in text:
                return None
            
            # Look for answer patterns (A, B, C, D)
            # Common patterns: "Answer: A", "Correct answer is A", "Option A is correct", etc.
            answer_patterns = [
                r'answer\s*[:=is]\s*([A-D])\b',
                r'correct\s+(?:answer|option)\s*[:=is]\s*([A-D])\b',
                r'option\s+([A-D])\s+is\s+correct',
                r'\b([A-D])\s+is\s+(?:the\s+)?correct',
                r'(?:answer|solution)\s*[:\-]\s*\(?([A-D])\)?'
            ]
            
            for pattern in answer_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    answer = match.group(1).upper()
                    
                    # Try to extract reasoning
                    reasoning = self._extract_reasoning_near_answer(text, match.start(), match.end())
                    
                    return {
                        'answer': answer,
                        'reasoning': reasoning or "Found exact match on web",
                        'confidence': 95
                    }
            
            return None
            
        except Exception as e:
            return None
    
    def _extract_reasoning_near_answer(self, text: str, answer_start: int, answer_end: int) -> str:
        """Extract reasoning text near where answer was found"""
        # Get 500 characters before and after answer
        context_start = max(0, answer_start - 500)
        context_end = min(len(text), answer_end + 500)
        context = text[context_start:context_end]
        
        # Clean up and return
        context = ' '.join(context.split())  # Normalize whitespace
        if len(context) > 300:
            context = context[:300] + "..."
        
        return context
    
    def search_similar_questions(self, question_text: str, subject: str) -> List[Dict]:
        """
        Search for similar questions (not exact matches)
        
        Args:
            question_text: Question text
            subject: Subject area (math/physics/chemistry)
            
        Returns:
            List of similar questions found
        """
        try:
            # Build search query with subject
            query = f'{subject} "{question_text[:80]}" answer explanation'
            
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
                return [{
                    'title': r['title'],
                    'snippet': r['body'],
                    'url': r['href']
                } for r in results]
                
        except Exception as e:
            print(f"Similar search failed: {e}")
            return []
