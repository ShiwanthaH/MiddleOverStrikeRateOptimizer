# Middle Over Strike Rate Optimizer - Backend

## Overview

The backend is a **FastAPI-based REST API** that uses a pre-trained **CatBoost machine learning model** to optimize cricket batting order during middle overs. It analyzes match scenarios and player statistics (including recent strike rates) to recommend the best batting sequence for maximizing strike rotation while minimizing pressure risk.

## Technology Stack

- **Framework**: FastAPI 0.115.6
- **Server**: Uvicorn 0.34.0
- **ML Library**: CatBoost (Gradient Boosting)
- **Data Processing**: Pandas
- **Model Serialization**: Joblib
- **Validation**: Pydantic

## Project Structure

```
backend/
├── main.py                              # FastAPI application and API endpoints
├── requirements.txt                     # Python dependencies
└── model/
    ├── catboost_strike_optimizer.joblib # Pre-trained CatBoost model
    └── training_columns.joblib         # Feature column names from training
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
  "Bowler_Group": "Pacer",
  "available_batters": [
    { "name": "KIC Asalanka", "sr": 120.5 },
    { "name": "MD Shanaka", "sr": 115.3 },
    { "name": "BKG Mendis", "sr": 105.0 }
  ]
}
```

**Parameters**:

- `Over` (int): Current over number (1-20)
- `Cumulative_Wickets` (int): Number of wickets lost (0-10)
- `Current_Run_Rate` (float): Current run rate per over
- `Inning` (int): Inning number (1 or 2)
- `Venue_Type` (str): Type of venue (e.g., "Neutral", "Home", "Away")
- `Bowler_Group` (str): Category of bowlers ("Pacer", "Spinner", "All-Rounder")
- `available_batters` (array of objects): List of batters with their recent form
  - `name` (str): Player's unique identifier/name
  - `sr` (float): Batter's recent strike rate (last 5 innings)

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
      "Strike_Rotation": 65.3,
      "Pressure_Prob": 8.42,
      "Middle_Over_Score": 138.22
    }
  ]
}
```

**Response Fields**:

- `Rank`: Recommendation rank (1 = best choice)
- `Batter`: Player name
- `Boundary_Prob`: Probability of hitting a boundary (%) - Class 2
- `Strike_Rotation`: Probability of rotating the strike (%) - Class 1
- `Pressure_Prob`: Probability of getting pressured (%) - Class 0
- `Middle_Over_Score`: Tactical utility score (higher is better)

## How It Works

### 1. Model Loading

The XGBoost model and training column mappings are loaded at application startup for quick inference.

### 2. Scenario Processing

- Takes the match scenario and available batters (with strike rate data)
- Creates a base scenario dictionary with match context and defaults
- For each batter, creates a simulation row with:
  - Match context (Over, Wickets, Run Rate, Inning, Venue, Bowler)
  - Player-specific data (Batter name, Batter_Last5_SR from the request)
- Ensures all necessary training columns are present with proper defaults

### 3. Prediction

- CatBoost model predicts probabilities for three outcome classes:
  - **Class 0**: Pressure (risky delivery faced)
  - **Class 1**: Strike Rotation (successful single/safe rotation)
  - **Class 2**: Boundary (aggressive boundary hit)

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

### catboost_strike_optimizer.joblib

- **Type**: CatBoost Classifier
- **Classes**: 3 (Pressure, Strike_Rotation, Boundary)
- **Features**: Match context (Over, Wickets, Run Rate, Inning, Venue, Bowler) + Player data (Batter, Recent SR)
- **Training Data**: Historical T20 cricket match data from `Dataset/` directory

### training_columns.joblib

- Stores the list of feature column names from model training
- Defines the expected feature structure for inference
- Used to ensure all features are present in the correct order

## Development

### Data Processing Pipeline

The training data comes from the `Dataset/` directory:

- `T20_ball_by_ball.csv`: Ball-by-ball match data
- `T20_matches.csv`: Match metadata
- Various preprocessing scripts for data cleaning and feature engineering

### Adding New Models

To replace or update the model:

1. Train your CatBoost model with the same feature structure (match context + player data)
2. Save using: `joblib.dump(model, './model/catboost_strike_optimizer.joblib')`
3. Save training columns: `joblib.dump(model_feature_names_list, './model/training_columns.joblib')`
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

| Issue                                            | Solution                                            |
| ------------------------------------------------ | --------------------------------------------------- |
| `FileNotFoundError: xgb_strike_optimizer.joblib` | Ensure model files are in `./model/` directory      |
| `CORS error in browser`                          | Update `allow_origins` in main.py with frontend URL |
| `Slow predictions`                               | Increase number of Uvicorn workers for concurrency  |
| `ModuleNotFoundError`                            | Run `pip install -r requirements.txt` again         |

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
