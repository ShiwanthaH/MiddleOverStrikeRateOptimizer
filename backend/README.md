# Middle Over Strike Rate Optimizer - Backend

## Overview

The backend is a **FastAPI-based REST API** that uses a pre-trained **XGBoost machine learning model** to optimize cricket batting order during middle overs. It analyzes match scenarios and player statistics to recommend the best batting sequence for maximizing strike rotation while minimizing pressure risk.

## Technology Stack

- **Framework**: FastAPI 0.115.6
- **Server**: Uvicorn 0.34.0
- **ML Library**: XGBoost
- **Data Processing**: Pandas
- **Model Serialization**: Joblib

## Project Structure

```
backend/
├── main.py                          # FastAPI application and API endpoints
├── requirements.txt                 # Python dependencies
└── model/
    ├── xgb_strike_optimizer.joblib # Pre-trained XGBoost model
    └── training_columns.joblib     # Feature column mapping for encoding
```

## Setup & Installation

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Run the Server

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

**API Documentation**: 
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### POST `/api/optimize`

Analyzes a cricket match scenario and recommends the optimized batting order based on player performance predictions.

**Request Body** (JSON):

```json
{
  "Over": 10,
  "Cumulative_Wickets": 3,
  "Current_Run_Rate": 7.5,
  "Inning": 1,
  "Venue_Type": "Neutral",
  "Bowler_Group": "All-Rounder",
  "available_batters": ["KIC Asalanka", "MD Shanaka", "BKG Mendis"]
}
```

**Parameters**:
- `Over` (int): Current over number (1-20)
- `Cumulative_Wickets` (int): Number of wickets lost (0-10)
- `Current_Run_Rate` (float): Current run rate per over
- `Inning` (int): Inning number (1 or 2)
- `Venue_Type` (str): Type of venue (e.g., "Neutral", "Home", "Away")
- `Bowler_Group` (str): Category of bowlers ("Pacer", "Spinner", "All-Rounder")
- `available_batters` (array): List of available batter names to analyze

**Response** (JSON):

```json
{
  "optimized_order": [
    {
      "Batter": "MD Shanaka",
      "Boundary_Prob": 25.43,
      "Strike_Rotation": 68.92,
      "Pressure_Prob": 5.65,
      "Middle_Over_Score": 142.54
    },
    {
      "Batter": "KIC Asalanka",
      "Boundary_Prob": 22.15,
      "Strike_Rotation": 65.30,
      "Pressure_Prob": 8.42,
      "Middle_Over_Score": 138.22
    }
  ]
}
```

**Response Fields**:
- `Batter`: Player name
- `Boundary_Prob`: Probability of hitting a boundary (%)
- `Strike_Rotation`: Probability of rotating the strike (%)
- `Pressure_Prob`: Probability of getting pressured (%)
- `Middle_Over_Score`: Tactical utility score (higher is better)

## How It Works

### 1. Model Loading
The XGBoost model and training column mappings are loaded at application startup for quick inference.

### 2. Scenario Processing
- Takes the match scenario and available batters
- Creates a simulation row for each batter with the match context
- Applies one-hot encoding to categorical features (Batter, Bowler_Group, Venue_Type)
- Aligns the encoded features to match the training data columns

### 3. Prediction
- XGBoost model predicts probabilities for three outcome classes:
  - **Class 0**: Pressure (risky delivery faced)
  - **Class 1**: Strike Rotation (successful single/safe shot)
  - **Class 2**: Boundary (aggressive shot)

### 4. Scoring Logic
The **Middle_Over_Score** is calculated using weighted probabilities:

```
Middle_Over_Score = (Strike_Rotation × 1.0) + (Pressure × -1.0) + (Boundary × 1.5)
```

This prioritizes:
- Strike rotation (weight: +1.0)
- Low pressure risk (weight: -1.0)
- Boundary potential (weight: +1.5)

### 5. Sorting
Results are sorted by Middle_Over_Score in descending order, providing the most tactically suitable batter first.

## CORS Configuration

The API has CORS middleware enabled to allow requests from the React frontend:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

⚠️ **Production Note**: The `allow_origins=["*"]` setting allows all origins. For production, restrict this to your frontend's URL:

```python
allow_origins=["http://localhost:5173", "https://yourdomain.com"]
```

## Model Information

### xgb_strike_optimizer.joblib
- **Type**: XGBoost Classifier
- **Classes**: 3 (Pressure, Strike_Rotation, Boundary)
- **Features**: One-hot encoded match scenario + batter information
- **Training Data**: Historical T20 cricket match data (available in `Dataset/` directory)

### training_columns.joblib
- Stores the list of feature column names from model training
- Used for proper alignment of input features during inference

## Development

### Data Processing Pipeline
The training data comes from the `Dataset/` directory:
- `T20_ball_by_ball.csv`: Ball-by-ball match data
- `T20_matches.csv`: Match metadata
- Various preprocessing scripts for data cleaning and feature engineering

### Adding New Models
To replace or update the model:
1. Train your XGBoost model with the same feature structure
2. Save using: `joblib.dump(model, './model/xgb_strike_optimizer.joblib')`
3. Save training columns: `joblib.dump(model.get_booster().feature_names, './model/training_columns.joblib')`
4. Restart the API server

## Error Handling

The API uses FastAPI's built-in validation:
- Invalid JSON payloads return 422 (Unprocessable Entity)
- Missing required fields return descriptive error messages
- Model prediction errors return 500 (Internal Server Error)

## Performance

- **Inference Time**: < 100ms per request (depending on number of batters)
- **Memory Usage**: ~50MB (model + dependencies)
- **Concurrent Requests**: Limited by Uvicorn workers (default: 1)

For production scaling, use:
```bash
uvicorn main:app --workers 4 --port 8000
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `FileNotFoundError: xgb_strike_optimizer.joblib` | Ensure model files are in `./model/` directory |
| `CORS error in browser` | Update `allow_origins` in main.py with frontend URL |
| `Slow predictions` | Increase number of Uvicorn workers for concurrency |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |

## Security Notes

- Model predictions are deterministic and do not contain sensitive data
- Player names are used as identifiers only
- No user authentication is currently implemented (add for production)
- All match scenarios are processed without logging

## Future Enhancements

- Add authentication and rate limiting
- Implement caching for identical scenarios
- Add endpoint for batch predictions
- Create model versioning system
- Add API logging and monitoring
