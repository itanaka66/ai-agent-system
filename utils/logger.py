import os
from logging import Logger, StreamHandler, FileHandler
import logging

def setup_logger(name: str) -> Logger:
    """ロガーを設定する
    
    Args:
        name (str): ロガー名
    
    Returns:
        Logger: 設定済みのロガーインスタンス
    """
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # StreamHandler に追加
    stream_handler = StreamHandler()
    stream_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(stream_format)
    logger.addHandler(stream_handler)

    # FileHandler に追加（ログファイルへの書き込み）
    file_path = os.getenv("LOG_DIR", "logs")
    log_file = os.path.join(file_path, 'app.log')

    if not os.path.exists(file_path):
        os.makedirs(file_path)

    file_handler = FileHandler(log_file)
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    return logger