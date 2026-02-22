from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import joblib
import numpy as np
from typing import Optional

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


# ─── Model Dashboard API Endpoints ─────────────────────────────────────────────

@app.get("/api/model-info")
def get_model_info():
    """Return comprehensive model metadata for the dashboard."""
    # Extract feature importances from the CatBoost model
    try:
        feature_importances = model.get_feature_importance().tolist()
        feature_names = model.feature_names_ if hasattr(model, 'feature_names_') else list(training_columns)
        
        # Pair and sort by importance
        importance_pairs = sorted(
            zip(feature_names, feature_importances),
            key=lambda x: x[1],
            reverse=True
        )
        feature_importance_data = [
            {"feature": name, "importance": round(imp, 4)}
            for name, imp in importance_pairs
        ]
    except Exception:
        feature_importance_data = [
            {"feature": col, "importance": round(1.0 / len(training_columns), 4)}
            for col in training_columns
        ]

    # Model parameters
    try:
        params = model.get_all_params()
        model_params = {
            "iterations": params.get("iterations", "N/A"),
            "learning_rate": round(params.get("learning_rate", 0.1), 4),
            "depth": params.get("depth", "N/A"),
            "l2_leaf_reg": params.get("l2_leaf_reg", "N/A"),
            "border_count": params.get("border_count", "N/A"),
            "loss_function": params.get("loss_function", "N/A"),
        }
    except Exception:
        model_params = {
            "iterations": "N/A",
            "learning_rate": "N/A",
            "depth": "N/A",
            "l2_leaf_reg": "N/A",
            "loss_function": "MultiClass",
        }

    # Tree count
    try:
        tree_count = model.tree_count_
    except Exception:
        tree_count = model_params.get("iterations", "N/A")

    return {
        "model_type": "CatBoost Classifier",
        "algorithm": "Gradient Boosting Decision Trees",
        "task": "Multiclass Classification",
        "num_classes": 3,
        "class_labels": [
            {"id": 0, "name": "Pressure", "description": "Dot ball / risky delivery — batter under pressure"},
            {"id": 1, "name": "Strike Rotation", "description": "Safe singles/doubles — controlled run scoring"},
            {"id": 2, "name": "Boundary", "description": "4 or 6 — aggressive scoring shot"},
        ],
        "scoring_formula": {
            "formula": "(Boundary × 1.5) + (Strike Rotation × 1.0) − (Pressure × 1.0)",
            "weights": {"Boundary": 1.5, "Strike_Rotation": 1.0, "Pressure": -1.0},
        },
        "training_features": list(training_columns),
        "num_features": len(training_columns),
        "feature_importances": feature_importance_data,
        "model_params": model_params,
        "tree_count": tree_count,
        "training_data": {
            "source": "Historical T20I Cricket Matches (ESPN Cricinfo / Cricsheet)",
            "records": "Ball-by-ball outcomes across international T20 matches",
            "label": "3-class outcome per delivery",
        },
        "inference_time": "<100ms per batch",
        "categorical_handling": "Native CatBoost categorical encoding (no manual one-hot encoding)",
    }


class ScenarioExploreRequest(BaseModel):
    feature: str  # Feature to vary
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    steps: Optional[int] = 10
    # Fixed scenario context
    Over: Optional[int] = 10
    Cumulative_Wickets: Optional[int] = 2
    Current_Run_Rate: Optional[float] = 7.0
    Inning: Optional[int] = 1
    Venue_Type: Optional[str] = "Neutral"
    Bowler_Group: Optional[str] = "Pace"
    Batter: Optional[str] = "KIC Asalanka"
    Batter_Last5_SR: Optional[float] = 120.0
    Batter_vs_BowlerType_SR: Optional[float] = 100.0


@app.post("/api/model-explore")
def explore_feature_impact(req: ScenarioExploreRequest):
    """
    Vary a single feature across a range while keeping others fixed.
    Returns class probabilities at each step for interactive visualization.
    """
    feature = req.feature

    # Define default ranges for known features
    ranges = {
        "Over": (1, 20),
        "Cumulative_Wickets": (0, 9),
        "Current_Run_Rate": (3.0, 15.0),
        "Inning": (1, 2),
        "Batter_Last5_SR": (50.0, 200.0),
        "Batter_vs_BowlerType_SR": (50.0, 200.0),
    }

    if feature in ranges:
        default_min, default_max = ranges[feature]
    else:
        default_min, default_max = 0, 10

    min_val = req.min_val if req.min_val is not None else default_min
    max_val = req.max_val if req.max_val is not None else default_max
    steps = req.steps or 10

    # Build base scenario dictionary
    base = {
        "Over": req.Over,
        "Cumulative_Wickets": req.Cumulative_Wickets,
        "Current_Run_Rate": req.Current_Run_Rate,
        "Inning": req.Inning,
        "Venue_Type": req.Venue_Type,
        "Bowler_Group": req.Bowler_Group,
        "Batter": req.Batter,
        "Batter_Last5_SR": req.Batter_Last5_SR,
        "Batter_vs_BowlerType_SR": req.Batter_vs_BowlerType_SR,
    }

    # Generate values to sweep
    if feature in ["Over", "Cumulative_Wickets", "Inning"]:
        values = list(range(int(min_val), int(max_val) + 1))
    else:
        values = np.linspace(min_val, max_val, steps).tolist()

    results = []
    for val in values:
        scenario = base.copy()
        scenario[feature] = val
        df = pd.DataFrame([scenario])
        df = df[training_columns]
        probs = model.predict_proba(df)[0]
        results.append({
            "value": round(val, 2),
            "Pressure": round(float(probs[0]) * 100, 2),
            "Strike_Rotation": round(float(probs[1]) * 100, 2),
            "Boundary": round(float(probs[2]) * 100, 2),
        })

    return {
        "feature": feature,
        "data": results,
    }


class CompareScenarioRequest(BaseModel):
    scenarios: list[dict]


@app.post("/api/model-compare")
def compare_scenarios(req: CompareScenarioRequest):
    """
    Compare multiple scenarios side by side.
    Each scenario dict should have the model features + a 'label' key.
    """
    results = []
    for scenario in req.scenarios:
        label = scenario.pop("label", "Scenario")
        # Fill defaults
        base = {
            "Over": 10,
            "Cumulative_Wickets": 2,
            "Current_Run_Rate": 7.0,
            "Inning": 1,
            "Venue_Type": "Neutral",
            "Bowler_Group": "Pace",
            "Batter": "KIC Asalanka",
            "Batter_Last5_SR": 120.0,
            "Batter_vs_BowlerType_SR": 100.0,
        }
        base.update(scenario)
        df = pd.DataFrame([base])
        df = df[training_columns]
        probs = model.predict_proba(df)[0]

        tactical_score = (float(probs[2]) * 1.5 + float(probs[1]) * 1.0 - float(probs[0]) * 1.0) * 100

        results.append({
            "label": label,
            "Pressure": round(float(probs[0]) * 100, 2),
            "Strike_Rotation": round(float(probs[1]) * 100, 2),
            "Boundary": round(float(probs[2]) * 100, 2),
            "Tactical_Score": round(tactical_score, 2),
        })

    return {"comparisons": results}