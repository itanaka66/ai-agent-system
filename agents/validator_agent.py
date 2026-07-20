#!/usr/bin/env python3
"""
Validator Agent - Hallucination & Logic Verification
Validates AI responses for accuracy, safety, and consistency
"""

import os
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ValidatorAgent:
    """AI 回答の正当性を検証するエージェント"""
    
    def __init__(self):
        self.ollama_url = os.getenv("OLLAMA_WORKER_URL") or os.getenv("OLLAMA_MASTER_URL")
        
        # CPU クラスターがあればそちらを使用
        cpu_nodes_str = os.getenv("OLLAMA_CPU_NODES", "")
        self.cpu_nodes = [n.strip() for n in cpu_nodes_str.split(",") if n.strip()]
        
        # 検証用モデル（軽量）
        self.model_name = os.getenv("MODEL_CPU_LIGHTER", "phi3:mini")
        
        # 評価基準
        self.hallucination_keywords = [
            "おそらく", "たぶん", "多分", "〜かもしれません", "推測ですが",
            "恐らく", "大体"
        ]
        
        self.safety_violations = [
            "暴力", "違法", "ハッキング", "攻撃", "被害"
        ]
    
    async def validate_response(self, query: str, response: str) -> Dict:
        """
        回答の正当性を検証
        
        Args:
            query (str): 元の質問
            response (str): AI の回答
        
        Returns:
            Dict: 検証結果（スコア、問題点など）
        """
        
        # 1. キーワードチェック（簡易ハルシネーション検出）
        hallucination_score = self._check_hallucination_keywords(response)
        
        # 2. セキュリティチェック
        safety_result = self._check_safety(response)
        
        # 3. 論理的一貫性チェック（LLM に委譲）
        logic_check = await self._llm_logic_validation(query, response)
        
        # 4. 総合スコア計算
        total_score = self._calculate_total_score(
            hallucination_score, 
            safety_result, 
            logic_check
        )
        
        return {
            "score": total_score,
            "hallucination_risk": hallucination_score < 0.8,
            "safety_safe": safety_result["safe"],
            "logic_consistent": logic_check.get("consistent", True),
            "issues": self._collect_issues(hallucination_score, safety_result, logic_check),
            "recommendation": self._get_recommend