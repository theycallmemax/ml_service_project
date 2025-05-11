import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("debug")

# Получаем текущий путь
current_file = __file__
logger.info(f"Current file: {current_file}")

# Получаем BASE_DIR
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
logger.info(f"BASE_DIR: {BASE_DIR}")

# Проверяем директории моделей и данных
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR = os.path.join(BASE_DIR, "data")

logger.info(f"MODELS_DIR: {MODELS_DIR}")
logger.info(f"DATA_DIR: {DATA_DIR}")

# Проверяем существование директорий
logger.info(f"MODELS_DIR exists: {os.path.exists(MODELS_DIR)}")
logger.info(f"DATA_DIR exists: {os.path.exists(DATA_DIR)}")

# Если директория моделей существует, проверяем файлы в ней
if os.path.exists(MODELS_DIR):
    model_files = os.listdir(MODELS_DIR)
    logger.info(f"Files in MODELS_DIR: {model_files}")
    
    # Проверяем существование конкретных моделей
    model_paths = [
        os.path.join(MODELS_DIR, "random_forest_btc_model.pkl"),
        os.path.join(MODELS_DIR, "xgboost_btc.pkl"),
        os.path.join(MODELS_DIR, "lightgbm_btc.pkl"),
        os.path.join(MODELS_DIR, "prophet_btc_model.pkl")
    ]
    
    for path in model_paths:
        logger.info(f"File exists: {path} = {os.path.exists(path)}")
else:
    logger.info("MODELS_DIR does not exist")

# Проверка на существование данных
if os.path.exists(DATA_DIR):
    data_files = os.listdir(DATA_DIR)
    logger.info(f"Files in DATA_DIR: {data_files}")
else:
    logger.info("DATA_DIR does not exist")

logger.info("Debug complete")
