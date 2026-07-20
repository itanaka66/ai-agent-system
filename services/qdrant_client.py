import os
from qdrant_client import QdrantClient, models
from typing import List, Dict

class QdrantHandler:
    """Qdrant ベクトルデータベースとの統合ラッパークラス"""
    
    def __init__(self):
        self.client = None
        self.setup()
        
    def setup(self):
        qdrant_host = os.getenv("QDRANT_HOST")
        if not qdrant_host:
            raise ValueError("Environment variable QDRANT_HOST is missing.")
            
        self.client = QdrantClient(
            url=qdrant_host,
            api_key=os.getenv("QDRANT_API_KEY", None)
        )
    
    def search(self, query: str, limit: int = 3) -> List[Dict]:
        """クエリと類似するドキュメントを検索
        
        Args:
            query (str): ユーザーの質問または検索クエリ
            limit (int): 返される結果数（デフォルトは 3）
        
        Returns:
            List[Dict]: 検索結果の一覧
        """
        
        embedding = self._generate_embedding(query)
        search_params = models.SearchParams(hnsw_ef=10, exact=True)
        
        result = self.client.search(
            collection_name="corpus_docs",
            query_vector=embedding,
            limit=limit,
            with_payload=True,
            score_threshold=0.75,
            params=search_params
        )
        
        return [hit.payload for hit in result]
    
    def _generate_embedding(self, text: str) -> List[float]:
        """テキストから埋め込みベクトルを生成
        
        Args:
            text (str): テキスト
        """
        
        from sentence_transformers import SentenceTransformer
        
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embedding = model.encode(text).tolist()
        
        return embedding
    
    def create_index(self, collection_name: str):
        """新しいコレクションを作成または上書きする"""
        
        self.client.recreate_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=384)
        )
    
    def index_document(self, collection_name: str, payload: Dict) -> None:
        """ドキュメントをインデックスに追加
        
        Args:
            collection_name (str): コレクション名
            payload (Dict): ドキュメントのペイロード（内容）
        """
        
        embedding = self._generate_embedding(payload['content'])
        self.client.upsert(
            collection_name=collection_name,
            points=[models.PointStruct(id=payload.get('id', None), vector=embedding, payload=payload)]
        )