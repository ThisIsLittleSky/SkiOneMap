import os
import logging
from typing import Dict, Any
from app.services.rag_engine import RAGEngine

logger = logging.getLogger(__name__)


class AppearanceAnalyzer:
    def __init__(self):
        self.rag_engine = RAGEngine()
    
    def analyze_appearance(self, image_path: str, match_info: Dict[str, Any]) -> str:
        """使用LLM分析人员穿着特征"""
        logger.info(f"Analyzing appearance for image: {image_path}")
        
        prompt = f"""请分析视频中检测到的人员穿着特征。

匹配信息：
- 置信度：{match_info.get('confidence', 0):.2f}
- 检测帧：{match_info.get('frame', 0)}

请描述该人员的：
1. 上衣颜色和款式
2. 下装颜色和款式
3. 其他显著特征（如背包、帽子等）

请用简洁的中文描述，不超过100字。"""

        try:
            response = self.rag_engine.llm_client.chat.completions.create(
                model=self.rag_engine.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            appearance = response.choices[0].message.content.strip()
            logger.info(f"Appearance analysis completed: {appearance[:50]}...")
            return appearance
            
        except Exception as e:
            logger.error(f"Failed to analyze appearance: {e}")
            return "穿着特征分析失败"
