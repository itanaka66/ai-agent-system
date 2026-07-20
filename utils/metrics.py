import os
from prometheus_client import Counter, Histogram

class MetricsCollector:
    """Prometheus メトリクスのコレクション用クラス"""
    
    def __init__(self):
        self.request_counter = Counter(
            'api_requests_total', 
            'Total number of API requests',
            ['method', 'endpoint']
        )
        
        self.response_time_histogram = Histogram(
            'response_duration_seconds', 
            'Request response duration in seconds',
            ['method', 'endpoint']
        )
    
    def increment_request_count(self, method: str, endpoint: str):
        """リクエスト数をインクリメントする"""
        
        self.request_counter.labels(method=method, endpoint=endpoint).inc()
    
    def observe_response_time(self, method: str, endpoint: str, duration: float):
        """応答時間の観測値を追加する"""
        
        self.response_time_histogram.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)