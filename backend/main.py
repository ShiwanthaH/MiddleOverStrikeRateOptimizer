from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import joblib
import numpy as np

app = FastAPI()

# Crucial: Enable CORS so your React app running on a different port can communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the model and columns on startup
model = joblib.load('./model/xgb_strike_optimizer.joblib')
training_columns = joblib.load('./model/training_columns.joblib')

# Define the expected JSON payload from React
class MatchScenario(BaseModel):
    Over: int
    Cumulative_Wickets: int
    Current_Run_Rate: float
    Inning: int
    Venue_Type: str
    Bowler_Group: str
    available_batters: list[str]

@app.post("/api/optimize")
def optimize_order(scenario: MatchScenario):
    # Convert Pydantic model to dictionary, separating batters from match context
    scenario_dict = scenario.model_dump()
    batters = scenario_dict.pop('available_batters')
    
    simulations = []
    
    # Create a simulation row for each available batter
    for batter in batters:
        sim_data = scenario_dict.copy()
        sim_data['Batter'] = batter
        simulations.append(sim_data)
        
    sim_df = pd.DataFrame(simulations)
    
    # One-Hot Encode and align columns to match the training data
    sim_encoded = pd.get_dummies(sim_df, columns=['Batter', 'Bowler_Group', 'Venue_Type'])
    sim_encoded = sim_encoded.reindex(columns=training_columns, fill_value=0)
    
    # Predict probabilities
    probs = model.predict_proba(sim_encoded)
    
    results = []
    for i, batter in enumerate(batters):
        boundary_prob = float(round(float(probs[i][2]) * 100, 2))
        strike_rotation = float(round(float(probs[i][1]) * 100, 2))
        pressure_prob = float(round(float(probs[i][0]) * 100, 2))
        
        # Calculate Middle Over Score (prioritizes strike rotation and low pressure)
        # Weights: Strike_Rotation (+1.0),  Pressure (-1.0), Boundaries (+1.5)
        middle_over_score = (strike_rotation * 1.0) + (pressure_prob * (-1.0)) + (boundary_prob * 1.5)
        middle_over_score = float(round(middle_over_score, 2))
        
        results.append({
            "Batter": batter,
            "Boundary_Prob": boundary_prob,
            "Strike_Rotation": strike_rotation,
            "Pressure_Prob": pressure_prob,
            "Middle_Over_Score": middle_over_score
        })
        
    # Sort results by Middle Over Score (highest to lowest)
    results.sort(key=lambda x: x["Middle_Over_Score"], reverse=True)
    
    return {"optimized_order": results}