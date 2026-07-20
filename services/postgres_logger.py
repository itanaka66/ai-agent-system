import os
from typing import Dict, Any
import psycopg2

class PostgreSQLLogger:
    """PostgreSQL Database のロギング用クラス"""
    
    def __init__(self):
        self.dsn = f"postgresql://{os.getenv('POSTGRES_USER')}:" \
                    f"{os.getenv('POSTGRES_PASSWORD')}@" \
                    f"{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/" \
                    f"{os.getenv('POSTGRES_DB')}"
    
    def connect(self):
        """データベースに接続"""
        
        try:
            self.conn = psycopg2.connect(self.dsn)
            self.cursor = self.conn.cursor()
            
            # テーブルが存在しない場合は作成
            self.create_tables_if_not_exists()
        except Exception as e:
            raise Exception(f"Database connection error: {e}")
    
    def close(self):
        """データベース接続を閉じる"""
        
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
            
    def save_message(self, session_id: str, role: str, content: str,
                     tokens_used: int = 0, validation_score: float = None,
                     model_used: str = "unknown", is_hallucination: bool = False):
        """メッセージをデータベースに保存
        
        Args:
            session_id (str): セッション ID
            role (str): メッセージの役割（user/assistant/system）
            content (str): 内容
            tokens_used (int, optional): 使用トークン数. Defaults to 0.
            validation_score (float, optional): 検証スコア. Defaults to None.
            model_used (str, optional): 使用モデル名. Defaults to "unknown".
            is_hallucination (bool, optional): ハルシネーションフラグ. Defaults to False.
        """
        
        try:
            if not hasattr(self, 'conn'):
                self.connect()
            
            # メッセージ保存
            self.cursor.execute(
                """INSERT INTO messages (session_id, role, content, tokens_used,
                 validation_score, model_used, is_hallucination)
                  VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (session_id, role, content, tokens_used, validation_score, model_used, is_hallucination),
            )
            
            self.conn.commit()
        except Exception as e:
            raise Exception(f"Error saving message: {e}")
    
    def create_tables_if_not_exists(self):
        """テーブルが存在しない場合は作成"""
        
        tables = [
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id SERIAL PRIMARY KEY,
                user_id VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            
            """
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES sessions(id),
                role VARCHAR(20) NOT NULL, -- user, assistant, system
                content TEXT,
                tokens_used INTEGER,
                validation_score FLOAT,
                model_used VARCHAR(50),
                is_hallucination BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        ]
        
        for table_sql in tables:
            self.cursor.execute(table_sql)
        
        self.conn.commit()