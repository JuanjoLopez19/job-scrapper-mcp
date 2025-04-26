# shared/utils.py
import logging
import json
from pathlib import Path
from typing import Any

from shared.config import LOG_LEVEL, LOG_FORMAT, OUTPUT_DIR

# Configure logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL), format=LOG_FORMAT)
logger = logging.getLogger(__name__)

def save_output(filename: str, content: Any) -> Path:
    """Save content to a file in the outputs directory"""
    try:
        filepath = OUTPUT_DIR / filename
        
        # Determine the type of content and write accordingly
        if isinstance(content, (dict, list)):
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(content))
                
        logger.info(f"Saved output to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to save output to {filename}: {e}")
        raise