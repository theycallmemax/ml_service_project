import os
import sys
import logging
import joblib
import pickle
from datetime import datetime
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("debug-models")

# Define paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")

logger.info(f"BASE_DIR: {BASE_DIR}")
logger.info(f"MODELS_DIR: {MODELS_DIR}")

# Define model types enum
class ModelType(str, Enum):
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    PROPHET = "prophet"

# Try to load models
def debug_load_models():
    logger.info("Starting debug load_models")
    try:
        # Load the latest version of each model type
        models = {}
        model_info = {}
        
        # Find latest version of each model type
        for model_type in ModelType:
            logger.info(f"Checking for model type: {model_type}")
            try:
                model_files = [f for f in os.listdir(MODELS_DIR) if f.startswith(f"{model_type}_btc") and f.endswith(".pkl")]
                logger.info(f"Found files for {model_type}: {model_files}")
                
                if not model_files:
                    logger.info(f"No files found for {model_type}, continuing to next model type")
                    continue
                    
                # Sort by timestamp (if versioned) or just take the base model
                if any("_20" in f for f in model_files):  # Check if any versioned models exist
                    latest_model = sorted([f for f in model_files if "_20" in f], reverse=True)[0]
                    logger.info(f"Using versioned model: {latest_model}")
                else:
                    model_base_names = {
                        ModelType.RANDOM_FOREST: "random_forest_btc_model.pkl",
                        ModelType.XGBOOST: "xgboost_btc.pkl",
                        ModelType.LIGHTGBM: "lightgbm_btc.pkl",
                        ModelType.PROPHET: "prophet_btc_model.pkl"
                    }
                    latest_model = model_base_names.get(model_type)
                    logger.info(f"Using base model: {latest_model}")
                    
                    if not latest_model or not os.path.exists(os.path.join(MODELS_DIR, latest_model)):
                        logger.info(f"Base model {latest_model} does not exist, continuing to next model type")
                        continue
                
                model_path = os.path.join(MODELS_DIR, latest_model)
                logger.info(f"Loading model from path: {model_path}")
                
                # Load the model based on its type
                if model_type == ModelType.PROPHET:
                    logger.info("Loading Prophet model...")
                    with open(model_path, "rb") as f:
                        try:
                            model = pickle.load(f)
                            logger.info("Prophet model loaded successfully")
                        except Exception as e:
                            logger.error(f"Error loading Prophet model: {e}")
                            raise
                else:
                    logger.info(f"Loading {model_type} model with joblib...")
                    try:
                        model = joblib.load(model_path)
                        logger.info(f"{model_type} model loaded successfully")
                    except Exception as e:
                        logger.error(f"Error loading {model_type} model: {e}")
                        raise
                
                models[model_type] = model
                logger.info(f"Added {model_type} to models dictionary")
                
                # Store model information
                model_info[model_type] = {
                    "filename": latest_model,
                    "path": model_path,
                    "last_modified": datetime.fromtimestamp(os.path.getmtime(model_path)).isoformat(),
                    "size_bytes": os.path.getsize(model_path)
                }
                logger.info(f"Added {model_type} info to model_info dictionary")
            except Exception as e:
                logger.error(f"Error processing {model_type}: {e}")
        
        logger.info(f"Loaded {len(models)} models successfully")
        logger.info(f"Models loaded: {list(models.keys())}")
        return True, models, model_info
    except Exception as e:
        logger.error(f"Error loading models: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False, {}, {}

if __name__ == "__main__":
    success, models, model_info = debug_load_models()
    logger.info(f"Load models {'succeeded' if success else 'failed'}")
    logger.info(f"Loaded models: {list(models.keys())}")
    logger.info(f"Model info: {model_info}")
