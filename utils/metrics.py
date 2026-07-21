from prometheus_client import Counter, Histogram, CollectorRegistry

class MetricsCollector:
    """Prometheus メトリクスのコレクション用クラス"""
    
    def __init__(self):
        self.registry = CollectorRegistry(auto_describe=True)
        
        # Ensure unique metric names and labels
        self.request_counter = Counter(
            'api_requests_total', 
            'Total number of API requests',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        self.response_time_histogram = Histogram(
            'response_duration_seconds', 
            'Request response duration in seconds',
            ['method', 'endpoint'],
            registry=self.registry
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