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
model = joblib.load('./model/catboost_strike_optimizer.joblib')
training_columns = joblib.load('./model/training_columns.joblib')

# Define batter info model
class BatterInfo(BaseModel):
    name: str
    sr: float

# Define the expected JSON payload from React
class MatchScenario(BaseModel):
    Over: int
    Cumulative_Wickets: int
    Current_Run_Rate: float
    Inning: int
    Venue_Type: str
    Bowler_Group: str
    available_batters: list[BatterInfo]

def optimize_batting_order(scenario, available_batters, pipeline_model, training_columns):
    """
    Optimize batting order based on match scenario and available batters.
    
    Args:
        scenario (dict): Match context (Over, Cumulative_Wickets, Current_Run_Rate, Inning, Venue_Type, Bowler_Group)
        available_batters (list): List of dicts with 'name' and 'sr' keys
        pipeline_model: Trained ML model for predictions
        training_columns (list): Feature column names from training data
    
    Returns:
        pd.DataFrame: Ranked batters with tactical scores and probabilities
    """
    simulations = []

    # Prepare a base dictionary for scenario features, including defaults for missing ones
    base_scenario = {
        'Over': None, 'Cumulative_Wickets': None, 'Current_Run_Rate': None,
        'Inning': None, 'Venue_Type': None, 'Bowler_Group': None,
        'Batter_Last5_SR': 100.0, # Default if not provided in scenario, otherwise overridden
        'Batter_vs_BowlerType_SR': 100.0 # Default if not provided in scenario, otherwise overridden
    }
    base_scenario.update(scenario) # Override with provided scenario values

    for batter_info in available_batters:
        # Create a dictionary for this specific batter
        sim_data = base_scenario.copy()
        sim_data['Batter'] = batter_info['name']
        sim_data['Batter_Last5_SR'] = batter_info['sr'] # Use the provided SR
        simulations.append(sim_data)

    # Create DataFrame from simulations
    sim_df = pd.DataFrame(simulations)
    # Reorder columns to match training data, and ensure all training columns are present.
    # Missing columns (like Batter_Last5_SR, Batter_vs_BowlerType_SR if not in scenario) will use defaults from base_scenario.
    sim_df = sim_df[training_columns]

    # Predict probabilities using the model
    probs = pipeline_model.predict_proba(sim_df)

    results = []
    for i, batter_info in enumerate(available_batters):
        p_pressure = probs[i][0] * 100
        p_rotation = probs[i][1] * 100
        p_boundary = probs[i][2] * 100

        # Calculate the Unified Tactical Score
        # Formula: (Boundary * 1.5) + (Rotation * 1.0) - (Pressure * 1.0)
        tactical_score = (p_boundary * 1.5) + (p_rotation * 1.0) - (p_pressure * 1.0)

        results.append({
            'Batter': batter_info['name'],
            'Tactical_Score': round(tactical_score, 2),
            'Boundary_Prob': round(p_boundary, 2),
            'Strike_Rotation': round(p_rotation, 2),
            'Pressure_Prob': round(p_pressure, 2)
        })

    results_df = pd.DataFrame(results)
    # Sort by the new Tactical Score
    results_df = results_df.sort_values(by='Tactical_Score', ascending=False).reset_index(drop=True)

    return results_df

@app.post("/api/optimize")
def optimize_order(scenario: MatchScenario):
    # Convert Pydantic model to dictionaries
    scenario_dict = scenario.model_dump()
    available_batters = scenario_dict.pop('available_batters')
    
    # Use the optimize_batting_order function
    results_df = optimize_batting_order(scenario_dict, available_batters, model, training_columns)
    
    # Convert DataFrame to list of dictionaries for JSON response
    results_list = results_df.to_dict('records')
    
    # Format response data to match frontend expectations
    optimized_order = []
    for idx, row in enumerate(results_list, 1):
        optimized_order.append({
            "Rank": idx,
            "Batter": row['Batter'],
            "Boundary_Prob": round(row['Boundary_Prob'], 2),
            "Strike_Rotation": round(row['Strike_Rotation'], 2),
            "Pressure_Prob": round(row['Pressure_Prob'], 2),
            "Middle_Over_Score": round(row['Tactical_Score'], 2)
        })
    
    return {"optimized_order": optimized_order}