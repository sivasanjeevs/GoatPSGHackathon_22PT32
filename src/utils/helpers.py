import os
import logging
from datetime import datetime
from typing import List, Tuple

def setup_logging(log_file: str) -> logging.Logger:
    """Set up logging configuration"""
    logger = logging.getLogger('fleet_management')
    logger.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def log_robot_action(logger: logging.Logger, robot_id: int, action: str,
                    details: str = "") -> None:
    """Log a robot action with timestamp"""
    message = f"Robot {robot_id}: {action}"
    if details:
        message += f" - {details}"
    logger.info(message)
    
def calculate_path_length(coordinates: List[Tuple[float, float]]) -> float:
    """Calculate total length of a path given list of coordinates"""
    if len(coordinates) < 2:
        return 0.0
        
    total_length = 0.0
    for i in range(len(coordinates) - 1):
        x1, y1 = coordinates[i]
        x2, y2 = coordinates[i + 1]
        segment_length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        total_length += segment_length
        
    return total_length
    
def format_time(seconds: float) -> str:
    """Format time in seconds to human-readable string"""
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"
        
def create_log_directory(base_path: str) -> str:
    """Create log directory with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = os.path.join(base_path, f"run_{timestamp}")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir 