"""
Loop Detection System
Prevents infinite conversation loops by analyzing history patterns
"""

import os
from typing import Tuple, List
from datetime import datetime, timedelta
from utils.logger import setup_logger

logger = setup_logger(__name__)


class LoopDetector:
    def __init__(self, db_logger):
        self.db_logger = db_logger
        self.threshold_similarity = 0.95
        self.max_check_depth = 7
    
    async def check_history(
        self, 
        session_id: str, 
        new_query: str
    ) -> Tuple[bool, str]:
        """
        Check if the current query matches recent conversation patterns
        
        Returns:
            Tuple of (is_loop_detected, pattern_description)
        """
        
        # Get recent messages from PostgreSQL
        history = await self.db_logger.get_session_messages(
            session_id=session_id,
            limit=self.max_check_depth,
            role="user"  # Only check user queries for loop detection
        )
        
        if len(history) < 2:
            return False, ""
        
        # Extract query content from history
        recent_queries = []
        for msg in history:
            if isinstance(msg, dict):
                recent_queries.append(msg.get("content", "").strip())
            else:
                recent_queries.append(str(msg).strip())
        
        # Check similarity with recent queries
        for i, old_query in enumerate(recent_queries):
            if self._is_similar(new_query, old_query):
                return True, f"Pattern match found at position {i+1}: '{old_query[:50]}...'"
        
        # Additional pattern: Check if similar topics are repeated 3 times
        topic_count = {}
        for query in recent_queries + [new_query]:
            topic = self._extract_topic(query)
            topic_count[topic] = topic_count.get(topic, 0) + 1
            
        max_repeats = max(topic_count.values()) if topic_count else 0
        
        if max_repeats >= 4:
            return True, f"Topic '{self._get_most_common_topic(topic_count)}' repeated {max_repeats} times"
        
        return False, ""
    
    def _is_similar(self, query1: str, query2: str) -> bool:
        """Calculate similarity between two queries"""
        
        # Normalize texts (lowercase, remove punctuation)
        import re
        
        norm1 = self._normalize_text(query1)
        norm2 = self._normalize_text(query2)
        
        if not norm1 or not norm2:
            return False
        
        # Jaccard similarity
        set1 = set(norm1.split())
        set2 = set(norm2.split())
        
        if not set1 or not set2:
            return False
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        jaccard_score = intersection / union if union > 0 else 0.0
        
        # Also check length-based similarity
        len_ratio = min(len(query1), len(query2)) / max(len(query1), len(query2)) if query1 and query2 else 0
        
        combined_score = (jaccard_score * 0.7) + (len_ratio * 0.3)
        
        return combined_score > self.threshold_similarity
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        
        import re
        
        # Remove common stopwords and special characters
        words = text.lower().split()
        
        # Simple word list (expand as needed)
        stop_words = {
            'what', 'how', 'why', 'when', 'where', 'who', 
            'the', 'is', 'are', 'was', 'were', 'be', 'been',
            'in', 'on', 'at', 'to', 'for', 'of'
        }
        
        filtered_words = [w for w in words if w not in stop_words and len(w) > 2]
        
        return " ".join(filtered_words)
    
    def _extract_topic(self, query: str) -> str:
        """Extract main topic from a query (simplified)"""
        
        import re
        
        # Remove common question words
        normalized = self._normalize_text(query)
        
        # Get most significant word(s) as topic identifier
        words = normalized.split()[-2:]  # Last meaningful words often indicate topic
        
        if len(words) >= 1:
            return " ".join(words)
        
        return query[:20]  # Fallback to first 20 chars
    
    def _get_most_common_topic(self, topic_count: dict) -> str:
        """Get most repeated topic"""
        
        if not topic_count:
            return ""
        
        return max(topic_count, key=topic_count.get)