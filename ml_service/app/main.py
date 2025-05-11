# ml_service/app/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field
import os
import joblib
import pickle
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import json
from enum import Enum
import time
import matplotlib.pyplot as plt
import io
import base64

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import xgboost as xgb
import lightgbm as lgb

from pybit.unified_trading import HTTP


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ml-service")


app = FastAPI(
    title="Cryptocurrency Price Prediction ML Service",
    description="API for cryptocurrency price predictions using ML models with daily retraining",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR = os.path.join(BASE_DIR, "data")
TRAINING_INFO_FILE = os.path.join(MODELS_DIR, "training_info.json")

# Make sure directories exist
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# Try to load training info
training_info = {}
if os.path.exists(TRAINING_INFO_FILE):
    try:
        with open(TRAINING_INFO_FILE, 'r') as f:
            training_info = json.load(f)
            logger.info(f"Loaded training info: {training_info}")
    except Exception as e:
        logger.error(f"Error loading training info: {e}")
        # Initialize with default values
        training_info = {}

# Enum for cryptocurrency types
class CryptoType(str, Enum):
    BTC = "btc"
    ETH = "eth"
    # Add more cryptocurrencies as they become available
    
# Enum for model types
class ModelType(str, Enum):
    RANDOM_FOREST = "random_forest"
    XGBOOST = "xgboost"
    LIGHTGBM = "lightgbm"
    PROPHET = "prophet"

# Current model state
class ModelState:
    current_model_type: ModelType = ModelType.RANDOM_FOREST
    models = {}
    model_info = {}
    retraining_in_progress = False

# Map model types to their file names
MODEL_FILE_MAPPING = {
    ModelType.RANDOM_FOREST: "random_forest_{}_model.pkl",
    ModelType.XGBOOST: "xgboost_{}.pkl",
    ModelType.LIGHTGBM: "lightgbm_{}.pkl",
    ModelType.PROPHET: "prophet_{}_model.pkl"
}

# Data fetching function from Bybit
def get_historical_data(symbol: str, days: int = 1000):
# Always convert symbol to uppercase
    symbol = symbol.upper()
    if not symbol.endswith("USDT"):
        symbol = symbol + "USDT"
    
    try:
        session = HTTP(testnet=False)
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
        
        response = session.get_kline(
            category="linear",
            symbol=symbol,
            interval="D",
            start=start_time,
            end=end_time,
            limit=days
        )
        
        if response["retCode"] != 0:
            logger.error(f"Error fetching data from Bybit: {response['retMsg']}")
            raise Exception(f"Bybit API error: {response['retMsg']}")
            
        raw = response["result"]["list"]
        df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume", "turnover"])
        df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit="ms")
        for col in ["open", "high", "low", "close", "volume", "turnover"]:
            df[col] = df[col].astype(float)
            
        # Add target column for prediction (next day's close price)
        df["target"] = df["close"].shift(-1)
        df = df.dropna()
        df = df.sort_values("timestamp")
        
        # Save the data for later use
        data_file = os.path.join(DATA_DIR, f"{symbol}_data.csv")
        df.to_csv(data_file, index=False)
        logger.info(f"Saved {symbol} data to {data_file}")
        
        return df
    except Exception as e:
        logger.error(f"Error in get_historical_data: {e}")
        raise e

# Model training function
def train_model(df: pd.DataFrame, model_name: str, crypto: str):
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.metrics import mean_absolute_error
    import xgboost as xgb
    import lightgbm as lgb
    
    try:
        crypto = crypto.lower()
        if not crypto.endswith("usdt"):
            crypto = crypto + "usdt"
            
        # Clean the data
        df = df.dropna().sort_values("timestamp").reset_index(drop=True)
        features = ["open", "high", "low", "close", "volume", "turnover"]
        
        if model_name == "prophet":
            try:
                from prophet import Prophet
                # Prophet requires specific format
                df_p = df[["timestamp", "close"]].rename(columns={"timestamp": "ds", "close": "y"})
                test_size = int(len(df_p) * 0.2)
                train_df = df_p[:-test_size]
                test_df = df_p[-test_size:]
                
                model = Prophet()
                model.fit(train_df)
                
                future = model.make_future_dataframe(periods=test_size)
                forecast = model.predict(future)
                
                y_true = test_df["y"].values
                y_pred = forecast[["ds", "yhat"]].tail(test_size)["yhat"].values
                
                mae = mean_absolute_error(y_true, y_pred)
                logger.info(f"PROPHET MAE on test set: {mae:.2f}")
                
                # Save model
                model_path = os.path.join(MODELS_DIR, MODEL_FILE_MAPPING[ModelType.PROPHET].format(crypto[:3]))
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
                
                # Update training info
                update_training_info(crypto[:3], "prophet", mae)
                    
                return {"prophet": model}
                
            except Exception as e:
                logger.error(f"Error training Prophet model: {e}")
                # Default to Random Forest if Prophet fails
                model_name = "random_forest"
                
        # Prepare models for other algorithms
        models = {}
        model_class = {
            "random_forest": RandomForestRegressor,
            "xgboost": xgb.XGBRegressor,
            "lightgbm": lgb.LGBMRegressor,
        }
        
        if model_name not in model_class:
            raise ValueError(f"Model {model_name} not supported")
            
        # Train models for features: open, high, low, volume, turnover
        for target in ["open", "high", "low", "volume", "turnover"]:
            X = df[features]
            y = df[target].shift(-1)
            X, y = X[:-1], y[:-1]
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
            
            model = model_class[model_name](n_estimators=100, random_state=42)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            logger.info(f"{model_name.upper()} → {target} MAE: {mae:.2f}")
            
            models[target] = model
            
        # Train model for close price (main target)
        X = df[features]
        y = df["close"].shift(-1)
        X, y = X[:-1], y[:-1]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
        
        close_model = model_class[model_name](n_estimators=100, random_state=42)
        close_model.fit(X_train, y_train)
        y_pred = close_model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        logger.info(f"{model_name.upper()} → close MAE: {mae:.2f}")
        
        models["close"] = close_model
        
        # Save all models
        model_path = os.path.join(MODELS_DIR, MODEL_FILE_MAPPING[model_name].format(crypto[:3]))
        with open(model_path, 'wb') as f:
            joblib.dump(models, f)
            
        # Update training info
        update_training_info(crypto[:3], model_name, mae)
        
        return models
    except Exception as e:
        logger.error(f"Error in train_model: {e}")
        raise e

# Function to update training info
def update_training_info(crypto: str, model_name: str, accuracy: float):
    global training_info
    
    crypto = crypto.lower()
    current_time = datetime.now().isoformat()
    
    if crypto not in training_info:
        training_info[crypto] = {}
        
    training_info[crypto][model_name] = {
        "last_trained": current_time,
        "accuracy": accuracy
    }
    
    # Save to file
    try:
        with open(TRAINING_INFO_FILE, 'w') as f:
            json.dump(training_info, f, indent=2)
        logger.info(f"Updated training info for {crypto} {model_name}")
    except Exception as e:
        logger.error(f"Error saving training info: {e}")

# Forecasting function
def forecast_n_days(models, df: pd.DataFrame, model_name: str, n_days: int):
    try:
        if model_name == "prophet":
            model = models["prophet"]
            future = model.make_future_dataframe(periods=n_days)
            forecast = model.predict(future)
            result = forecast[["ds", "yhat"]].tail(n_days)
            result.columns = ["timestamp", "predicted_close"]
            return result
            
        # For other model types, use recursive forecasting
        preds = []
        last_row = df.iloc[-1:].copy()
        
        for _ in range(n_days):
            # Predict features
            next_features = {}
            for feat in ["open", "high", "low", "volume", "turnover"]:
                X_feat = last_row[["open", "high", "low", "close", "volume", "turnover"]].values
                y_feat = models[feat].predict(X_feat)[0]
                next_features[feat] = y_feat
                
            # Create row with features
            feature_row = {
                "open": next_features["open"],
                "high": next_features["high"],
                "low": next_features["low"],
                "close": last_row["close"].values[0],  # previous day's close
                "volume": next_features["volume"],
                "turnover": next_features["turnover"],
            }
            
            X_close = pd.DataFrame([feature_row])[["open", "high", "low", "close", "volume", "turnover"]]
            y_close = models["close"].predict(X_close)[0]
            preds.append(y_close)
            
            # Create new row for next iteration
            new_row = pd.DataFrame([{
                "timestamp": last_row["timestamp"].values[0] + pd.Timedelta(days=1),
                "open": next_features["open"],
                "high": next_features["high"],
                "low": next_features["low"],
                "close": y_close,
                "volume": next_features["volume"],
                "turnover": next_features["turnover"],
            }])
            
            last_row = new_row
            
        future_dates = pd.date_range(start=df["timestamp"].iloc[-1] + pd.Timedelta(days=1), periods=n_days)
        return pd.DataFrame({"timestamp": future_dates, "predicted_close": preds})
    except Exception as e:
        logger.error(f"Error in forecast_n_days: {e}")
        raise e

# Main prediction function
def predict_token_price(symbol: str, model_name: str, n_days: int):
    try:
        if model_name not in [m.value for m in ModelType]:
            raise ValueError(f"Unsupported model type: {model_name}")
            
        if not 1 <= n_days <= 30:
            raise ValueError("Forecast days must be between 1 and 30")
            
        # Get historical data
        logger.info(f"Getting historical data for {symbol}...")
        df = get_historical_data(symbol, days=1000)
        
        # Check if we need to train a new model
        should_train = False
        symbol_key = symbol[:3].lower()
        
        if symbol_key not in training_info:
            logger.info(f"No training info for {symbol_key}, training new model")
            should_train = True
        elif model_name not in training_info[symbol_key]:
            logger.info(f"No training info for {symbol_key} {model_name}, training new model")
            should_train = True
        else:
            # Check if model was trained in the last 24 hours
            last_trained = datetime.fromisoformat(training_info[symbol_key][model_name]["last_trained"])
            time_diff = datetime.now() - last_trained
            if time_diff.days >= 1:
                logger.info(f"Model for {symbol_key} {model_name} is older than 24 hours, retraining")
                should_train = True
                
        # Train model if needed
        if should_train:
            logger.info(f"Training {model_name} model for {symbol}...")
            models = train_model(df, model_name, symbol)
        else:
            # Load existing model
            model_path = os.path.join(MODELS_DIR, MODEL_FILE_MAPPING[model_name].format(symbol_key))
            if not os.path.exists(model_path):
                logger.info(f"Model file {model_path} not found, training new model")
                models = train_model(df, model_name, symbol)
            else:
                logger.info(f"Loading existing model from {model_path}")
                if model_name == "prophet":
                    with open(model_path, 'rb') as f:
                        models = {"prophet": pickle.load(f)}
                else:
                    models = joblib.load(model_path)
                    
        # Make forecast
        logger.info(f"Forecasting {n_days} days ahead...")
        forecast = forecast_n_days(models, df, model_name, n_days)
        
        return forecast
    except Exception as e:
        logger.error(f"Error in predict_token_price: {e}")
        raise e

# Model loader
def load_models():
    loaded_count = 0
    
    # Debug output to check paths
    logger.info(f"MODELS_DIR: {MODELS_DIR}")
    all_files = os.listdir(MODELS_DIR)
    logger.info(f"All files in MODELS_DIR: {all_files}")
    
    for model_type in ModelType:
        for crypto in ["btc", "eth"]:  # Add more cryptos as needed
            try:
                # Use direct filename mapping from the dictionary
                model_filename = MODEL_FILE_MAPPING.get(model_type).format(crypto)
                full_path = os.path.join(MODELS_DIR, model_filename)
                logger.info(f"Attempting to load model {model_type} for {crypto} from {full_path}")
                
                if not os.path.exists(full_path):
                    logger.warning(f"Model file not found: {full_path}")
                    continue
                    
                # Load model
                if model_type == ModelType.PROPHET:
                    with open(full_path, 'rb') as f:
                        model = pickle.load(f)
                else:
                    model = joblib.load(full_path)
                
                # Save model in state
                if crypto not in ModelState.models:
                    ModelState.models[crypto] = {}
                    
                ModelState.models[crypto][model_type] = model
                
                # Save model metadata
                if crypto not in ModelState.model_info:
                    ModelState.model_info[crypto] = {}
                    
                model_stats = os.stat(full_path)
                ModelState.model_info[crypto][model_type] = {
                    "file": full_path,
                    "size_mb": round(model_stats.st_size / (1024 * 1024), 2),
                    "last_modified": datetime.fromtimestamp(model_stats.st_mtime).isoformat(),
                }
                
                loaded_count += 1
                logger.info(f"Successfully loaded model {model_type} for {crypto} from {full_path}")
                
            except Exception as e:
                logger.error(f"Error loading model {model_type} for {crypto}: {str(e)}")
    
    logger.info(f"Loaded {loaded_count} models successfully")
    return loaded_count

# Функция для обучения всех типов моделей для одной криптовалюты
def train_all_models_for_crypto(crypto: str):
    try:
        logger.info(f"Starting training all models for {crypto}...")
        # Получение исторических данных для заданной криптовалюты
        symbol = f"{crypto}usdt"
        df = get_historical_data(symbol, days=200)
        
        # Обучение всех типов моделей
        for model_type in ModelType:
            logger.info(f"Training {model_type} model for {crypto}...")
            try:
                train_model(df, model_type, crypto)
                logger.info(f"Successfully trained {model_type} model for {crypto}")
            except Exception as e:
                logger.error(f"Error training {model_type} model for {crypto}: {e}")
        
        logger.info(f"Completed training all models for {crypto}")
        return True
    except Exception as e:
        logger.error(f"Error in train_all_models_for_crypto: {e}")
        return False

# Функция инициализации моделей - проверяет наличие моделей и обучает их при необходимости
def initialize_models():
    # Сначала загрузим существующие модели
    loaded_count = load_models()
    logger.info(f"Loaded {loaded_count} models from disk")
    
    # Проверим, есть ли хотя бы одна модель для каждой криптовалюты
    cryptos = [crypto.value for crypto in CryptoType]
    models_needed = False
    
    # Проверяем, существуют ли модели для каждой криптовалюты и типа модели
    for crypto in cryptos:
        crypto_models_exist = False
        
        # Проверяем каждый тип модели
        for model_type in ModelType:
            model_filename = MODEL_FILE_MAPPING.get(model_type).format(crypto)
            full_path = os.path.join(MODELS_DIR, model_filename)
            
            if os.path.exists(full_path):
                crypto_models_exist = True
                break
        
        # Если нет моделей для этой криптовалюты, обучаем их
        if not crypto_models_exist:
            logger.info(f"No models found for {crypto}, will train new models")
            models_needed = True
            train_all_models_for_crypto(crypto)
    
    # Если были обучены новые модели, загружаем их
    if models_needed:
        logger.info("New models were trained, reloading models...")
        load_models()
    
    return True

# Try to load models on startup
# load_models()
# Используем новую функцию для инициализации моделей
initialize_models()
load_models()

# Prediction request model - updated to include crypto and days parameters
class PredictionRequest(BaseModel):
    crypto: CryptoType = Field(CryptoType.BTC, description="Cryptocurrency to predict")
    days: int = Field(1, description="Number of days to predict", ge=1, le=30)
    model_type: Optional[ModelType] = Field(ModelState.current_model_type, description="Model type to use for prediction")

# Daily prediction model for the response
class DailyPrediction(BaseModel):
    date: str = Field(..., description="Date of the prediction")
    price: float = Field(..., description="Predicted closing price")

# Prediction response model - updated to handle multiple days
class PredictionResponse(BaseModel):
    crypto: str = Field(..., description="Cryptocurrency that was predicted")
    predictions: List[DailyPrediction] = Field(..., description="List of daily predictions")
    model_type: str = Field(..., description="Model type used for the prediction")
    timestamp: str = Field(..., description="Timestamp of the prediction")
    chart: Optional[str] = Field(None, description="Base64 encoded chart image")

# Model info response model
class ModelInfoResponse(BaseModel):
    available_models: Dict[str, List[str]] = Field(..., description="Available models by cryptocurrency")
    model_details: Dict[str, Dict[str, Any]] = Field(..., description="Details of loaded models")
    training_info: Dict[str, Dict[str, Any]] = Field(..., description="Training information for models")

# Health check response model
class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Current timestamp")
    models_loaded: int = Field(..., description="Number of loaded models")

# Generate chart function
def generate_prediction_chart(historical_data, forecast_data, symbol):
    plt.figure(figsize=(12, 5))
    
    # Plot historical data
    plt.plot(historical_data["timestamp"], historical_data["close"], label="Historical Price")
    
    # Plot forecast data
    plt.plot(forecast_data["timestamp"], forecast_data["predicted_close"], label="Forecast", color="red")
    
    plt.xlabel("Date")
    plt.ylabel(f"Price {symbol.upper()}/USDT")
    plt.title(f"Price Forecast for {symbol.upper()}/USDT")
    plt.legend()
    plt.grid(True)
    
    # Save plot to bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    
    # Convert to base64
    img_str = base64.b64encode(buf.read()).decode("utf-8")
    plt.close()
    
    return img_str

# Updated prediction endpoint
@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    try:
        model_type = request.model_type
        crypto = request.crypto
        days = request.days
        
        # Get crypto symbol
        symbol = f"{crypto}usdt"
        
        # Make prediction
        forecast = predict_token_price(symbol, model_type, days)
        
        # Get historical data for chart
        historical_data = get_historical_data(symbol, days=30)
        
        # Generate chart
        chart_img = generate_prediction_chart(historical_data, forecast, crypto)
        
        # Format predictions
        daily_predictions = []
        for _, row in forecast.iterrows():
            daily_predictions.append(
                DailyPrediction(
                    date=row["timestamp"].strftime("%Y-%m-%d"),
                    price=round(float(row["predicted_close"]), 2)
                )
            )
        
        # Return prediction response
        return PredictionResponse(
            crypto=crypto,
            predictions=daily_predictions,
            model_type=model_type,
            timestamp=datetime.now().isoformat(),
            chart=chart_img
        )
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

# Model retraining function
async def retrain_models_task(crypto: CryptoType = CryptoType.BTC):
    try:
        ModelState.retraining_in_progress = True
        symbol = f"{crypto}usdt"
        logger.info(f"Starting model retraining process for {symbol}")
        
        # Get historical data
        df = get_historical_data(symbol, days=1000)
        
        # Train all model types
        for model_type in ModelType:
            logger.info(f"Training {model_type} model for {symbol}")
            train_model(df, model_type, symbol)
        
        # Reload models
        load_models()
        
        logger.info("Model retraining completed successfully")
    except Exception as e:
        logger.error(f"Error during model retraining: {str(e)}")
    finally:
        ModelState.retraining_in_progress = False

# Retrain endpoint
@app.post("/retrain")
async def retrain_models(background_tasks: BackgroundTasks, crypto: CryptoType = CryptoType.BTC):
    if ModelState.retraining_in_progress:
        raise HTTPException(status_code=409, detail="Retraining already in progress")
    
    # Add retraining task to background tasks
    try:
        background_tasks.add_task(retrain_models_task, crypto)
        return {"message": f"Retraining process started for {crypto}"}
    except Exception as e:
        logger.error(f"Failed to start retraining: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start retraining: {str(e)}")

# Model info endpoint
@app.get("/model-info", response_model=ModelInfoResponse)
async def get_model_info():
    available_models = {}
    for crypto, models in ModelState.model_info.items():
        available_models[crypto] = list(models.keys())
        
    return ModelInfoResponse(
        available_models=available_models,
        model_details=ModelState.model_info,
        training_info=training_info
    )

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    # Count total loaded models
    model_count = sum(len(models) for models in ModelState.models.values())
    
    return HealthResponse(
        status="ok",
        timestamp=datetime.now().isoformat(),
        models_loaded=model_count
    )

@app.get("/current-price/{crypto}")
async def get_current_price(crypto: CryptoType):
    try:
        symbol = f"{crypto}usdt"
        session = HTTP(testnet=False)
        
        ticker_data = session.get_tickers(category="linear", symbol=symbol.upper())
        
        if ticker_data["retCode"] != 0:
            raise HTTPException(status_code=500, detail=f"Error getting ticker data: {ticker_data['retMsg']}")
            
        last_price = float(ticker_data["result"]["list"][0]["lastPrice"])
        
        return {
            "crypto": crypto,
            "price": last_price,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting current price: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting current price: {str(e)}")
