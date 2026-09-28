"""Flask extensions and logger setup to avoid circular dependencies."""
import logging
from pathlib import Path
from flask_socketio import SocketIO
from flask_cors import CORS

socketio = SocketIO(cors_allowed_origins="*", async_mode='threading')
cors = CORS()
logger = logging.getLogger('YouTubeUploaderApp')


def init_logging(logs_dir: str):
    """Initialize file and stream logging for the application."""
    log_path = Path(logs_dir) / 'server.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(str(log_path)),
            logging.StreamHandler()
        ]
    )
