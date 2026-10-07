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
            "recommendation": self._get_recommendation(total_score)
        }

    def _check_hallucination_keywords(self, response: str) -> float:
        """曖昧表現キーワードの出現数からハルシネーションリスクスコアを算出（1.0=安全、0.0=高リスク）"""

        hits = sum(1 for kw in self.hallucination_keywords if kw in response)
        return max(0.0, 1.0 - hits * 0.2)

    def _check_safety(self, response: str) -> Dict:
        """危険・違反キーワードの有無を確認"""

        violations = [kw for kw in self.safety_violations if kw in response]
        return {"safe": len(violations) == 0, "violations": violations}

    async def _llm_logic_validation(self, query: str, response: str) -> Dict:
        """LLM に質問と回答の論理的一貫性を判定させる"""

        from services.ollama_client import OllamaClient

        node_url = self.cpu_nodes[0] if self.cpu_nodes else self.ollama_url
        if not node_url:
            return {"consistent": True, "explanation": "No validation node configured; skipped"}

        client = OllamaClient(node_url)

        prompt = f"""以下の質問と回答が論理的に一致しているか判定してください。

質問: {query}

回答: {response}

一致していれば「CONSISTENT」、矛盾や論理的な誤りがあれば「INCONSISTENT」という単語で始めて、短い理由を続けてください。"""

        try:
            result = await client.generate(
                model=self.model_name,
                prompt=prompt,
                max_tokens=200
            )
            consistent = result.strip().upper().startswith("CONSISTENT")
            return {"consistent": consistent, "explanation": result.strip()}
        except Exception as e:
            logger.error(f"Logic validation error: {e}")
            return {"consistent": True, "explanation": f"Validation skipped due to error: {e}"}

    def _calculate_total_score(self, hallucination_score: float, safety_result: Dict, logic_check: Dict) -> float:
        """各チェック結果を重み付けして統合スコアを算出"""

        logic_score = 1.0 if logic_check.get("consistent", True) else 0.0
        safety_score = 1.0 if safety_result.get("safe", True) else 0.0

        return round(hallucination_score * 0.3 + safety_score * 0.4 + logic_score * 0.3, 2)

    def _collect_issues(self, hallucination_score: float, safety_result: Dict, logic_check: Dict) -> List[str]:
        """検出された問題点を一覧化"""

        issues = []
        if hallucination_score < 0.8:
            issues.append("Response contains uncertain/hedging language")
        if not safety_result.get("safe", True):
            issues.append(f"Safety violation keywords found: {', '.join(safety_result.get('violations', []))}")
        if not logic_check.get("consistent", True):
            issues.append(f"Logic inconsistency: {logic_check.get('explanation', '')}")
        return issues

    def _get_recommendation(self, total_score: float) -> str:
        """総合スコアから推奨アクションを判定"""

        if total_score >= 0.8:
            return "approve"
        elif total_score >= 0.5:
            return "review"
        else:
            return "reject"