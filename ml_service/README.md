# Bitcoin Price Prediction ML Service

This microservice system predicts Bitcoin (BTC/USDT) closing prices using machine learning models that automatically retrain daily. It provides FastAPI endpoints for predictions and model management.

## Features

- 🤖 **Multiple ML Models**: RandomForest, XGBoost, LightGBM, and Prophet models for BTC price prediction
- 🔄 **Daily Retraining**: Automatically fetches new data and retrains models daily
- 🔥 **Hot Model Swapping**: Updates models without service restart
- 🔌 **REST API**: Simple interface for predictions and model management
- 📊 **Model Versioning**: Maintains model history with timestamps
- 🐳 **Docker-based**: Fully containerized setup with Docker Compose

## Architecture

```
[FastAPI ML Service] <-- Models/Data --> [Airflow DAG Service]
       |
       v
Predictions & Management
```

### Components

- **ML Service**: FastAPI application serving models for predictions
- **Airflow Service**: Handles scheduled daily retraining
- **Shared Volumes**: For models and data persistence

## API Endpoints

- **GET /health**: Check service health status
- **GET /model-info**: Get information about available models
- **POST /predict**: Get BTC price prediction for the next day
- **POST /retrain**: Manually trigger model retraining

## Setup and Deployment

### Prerequisites

- Docker and Docker Compose installed
- At least 4GB of RAM for running all services

### Running the Service

```bash
# Clone the repository
git clone <repository-url>
cd ml-service

# Start all services
docker-compose up -d

# Access FastAPI service
open http://localhost:8000/docs

# Access Airflow UI
open http://localhost:8080
```

### Making a Prediction

```bash
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{}'
```

Or with custom features:

```bash
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '
{
    "model_type": "xgboost",
    "features": {
        "open": 70000.0,
        "high": 72000.0,
        "low": 69000.0,
        "close": 71000.0,
        "volume": 100000.0,
        "turnover": 7000000000.0
    }
}'
```

## Development

### Project Structure

```
ml_service/
├── app/                # FastAPI application
│   ├── main.py         # Main API endpoints
│   └── services/       # Model handling services
├── airflow/            # Airflow configuration
│   └── dags/           # DAG definition for retraining
├── models/             # Saved ML models
├── data/               # Historical BTC data
└── docker/             # Docker configurations
```

### Adding New Models

To add a new model type:

1. Implement the training function in the Airflow DAG
2. Update the `ModelType` enum in the FastAPI app
3. Add model loading logic in the `load_models()` function

## License

MIT

## Contributors

- Your Name
