import React, { useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { venueData, bowlerGroups, batterData } from "../data";

interface BatterSelection {
  name: string;
  sr: number;
}

interface PredictionResult {
  Batter: string;
  Boundary_Prob: number;
  Strike_Rotation: number;
  Pressure_Prob: number;
  Middle_Over_Score: number;
}

export default function TacticalDashboard() {
  // --- State Management ---
  const [over, setOver] = useState<number>(10);
  const [wickets, setWickets] = useState<number>(3);
  const [score, setScore] = useState<number>(75);
  const [inning, setInning] = useState<number>(1);
  const [selectedVenueName, setSelectedVenueName] = useState<string>(
    venueData[0].name,
  );
  const [bowlerGroup, setBowlerGroup] = useState<string>(bowlerGroups[1].type);
  const [selectedBatters, setSelectedBatters] = useState<BatterSelection[]>([
    { name: "KIC Asalanka", sr: 120.0 },
    { name: "MD Shanaka", sr: 115.5 },
    { name: "BKG Mendis", sr: 105.3 },
  ]);

  const [results, setResults] = useState<PredictionResult[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Auto-calculate run rate based on score and over
  const currentRunRate = useMemo(() => {
    return over > 0 ? Number((score / over).toFixed(2)) : 0;
  }, [score, over]);

  // Lookup venue type from venue name
  const currentVenueType = useMemo(() => {
    const v = venueData.find((v) => v.name === selectedVenueName);
    return v ? v.venueType : "Neutral";
  }, [selectedVenueName]);

  // Render content based on loading and results state
  const renderResultsContent = useMemo(() => {
    if (results.length === 0 && !isLoading) {
      return (
        <div className="h-full flex items-center justify-center text-slate-500 italic mt-10">
          Configure the scenario and click "Optimize" to view tactical
          recommendations.
        </div>
      );
    } else if (isLoading) {
      return (
        <div className="h-full flex items-center justify-center mt-10">
          <div className="animate-pulse flex flex-col items-center">
            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            <span className="mt-4 text-slate-400">
              Processing XGBoost Tree Inferencing...
            </span>
          </div>
        </div>
      );
    } else {
      return (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="text-xs text-slate-400 uppercase bg-slate-900">
              <tr>
                <th className="px-6 py-3 rounded-tl-lg">Rank</th>
                <th className="px-6 py-3">Batter</th>
                <th className="px-6 py-3 text-center">
                  Tactical Utility Score
                </th>
                <th className="px-6 py-3 text-center">
                  Boundary Prob (Class 2)
                </th>
                <th className="px-6 py-3 text-center">
                  Strike Rotation (Class 1)
                </th>
                <th className="px-6 py-3 text-center rounded-tr-lg">
                  Pressure Risk (Class 0)
                </th>
              </tr>
            </thead>
            <tbody>
              {results.map((res, index) => {
                const playerInfo = batterData.find(
                  (b) => b.unique_name === res.Batter,
                );
                const isTopPick = index === 0;

                return (
                  <tr
                    key={res.Batter}
                    className={`border-b border-slate-700 last:border-0 ${isTopPick ? "bg-blue-900 bg-opacity-20" : ""}`}
                  >
                    <td className="px-6 py-4 font-bold text-lg text-slate-400">
                      #{index + 1}
                    </td>
                    <td className="px-6 py-4 flex items-center gap-3">
                      <img
                        src={playerInfo?.img_url}
                        alt=""
                        className="w-10 h-10 rounded-full bg-slate-200"
                      />
                      <div>
                        <div className="font-semibold text-slate-100">
                          {playerInfo?.common_name || res.Batter}
                        </div>
                        {isTopPick && (
                          <span className="text-[10px] text-emerald-400 uppercase font-bold tracking-wider">
                            Optimal Matchup
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span
                        className={`px-3 py-1 rounded font-bold ${isTopPick ? "bg-blue-500 bg-opacity-30 text-blue-300" : "bg-slate-700 bg-opacity-40 text-slate-200"}`}
                      >
                        {res.Middle_Over_Score}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span
                        className={`px-3 py-1 rounded font-bold ${isTopPick ? "bg-emerald-500 bg-opacity-20 text-emerald-400" : "text-slate-200"}`}
                      >
                        {res.Boundary_Prob}%
                      </span>
                    </td>
                    <td className="px-6 py-4 text-center text-slate-300">
                      {res.Strike_Rotation}%
                    </td>
                    <td className="px-6 py-4 text-center">
                      <span
                        className={`${res.Pressure_Prob > 30 ? "text-red-400" : "text-slate-400"}`}
                      >
                        {res.Pressure_Prob}%
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      );
    }
  }, [results, isLoading]);

  // Toggle a batter in/out of the dugout selection
  const toggleBatter = (unique_name: string) => {
    const isBatterSelected = selectedBatters.some(
      (b) => b.name === unique_name,
    );
    if (isBatterSelected) {
      setSelectedBatters(selectedBatters.filter((b) => b.name !== unique_name));
    } else {
      // Find batter data to get strike rate (default to 100.0 if not found)
      const batterInfo = batterData.find((b) => b.unique_name === unique_name);
      const strikeRate = batterInfo?.sr || 100.0;
      setSelectedBatters([
        ...selectedBatters,
        { name: unique_name, sr: strikeRate },
      ]);
    }
  };

  // Run the Optimization API Call
  const handleOptimize = async () => {
    if (selectedBatters.length === 0) {
      alert("Please select at least one batter from the dugout.");
      return;
    }

    setIsLoading(true);

    const payload = {
      Over: over,
      Cumulative_Wickets: wickets,
      Current_Run_Rate: currentRunRate,
      Inning: inning,
      Venue_Type: currentVenueType,
      Bowler_Group: bowlerGroup,
      available_batters: selectedBatters,
    };

    try {
      const response = await fetch("http://localhost:8000/api/optimize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        const data = await response.json();
        setResults(data.optimized_order);
      } else {
        throw new Error("Backend not connected");
      }
    } catch (error) {
      console.warn(
        "API failed, using simulated response for demo purposes.",
        error,
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen min-w-[100vw] bg-slate-900 text-slate-100 p-6 py-12 font-sans">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <header className="border-b border-slate-700 pb-4 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-blue-400">
              SLC Tactical Optimizer
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Middle-Overs Matchup Analysis (Powered by CatBoost)
            </p>
          </div>
          <Link
            to="/model-dashboard"
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg transition-colors text-sm font-medium"
          >
            ML Model Dashboard →
          </Link>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* LEFT PANEL: Match Context Configuration */}
          <div className="lg:col-span-4 space-y-6 bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
            <h2 className="text-xl font-semibold text-slate-200 border-b border-slate-700 pb-2">
              Match Scenario
            </h2>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label
                  htmlFor="over-input"
                  className="block text-xs text-slate-400 mb-1"
                >
                  Over (7-15)
                </label>
                <input
                  id="over-input"
                  type="number"
                  min="7"
                  max="15"
                  value={over}
                  onChange={(e) => setOver(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-600 rounded p-2 text-white focus:border-blue-500 outline-none"
                />
              </div>
              <div>
                <label
                  htmlFor="wickets-input"
                  className="block text-xs text-slate-400 mb-1"
                >
                  Wickets Down
                </label>
                <input
                  id="wickets-input"
                  type="number"
                  min="0"
                  max="9"
                  value={wickets}
                  onChange={(e) => setWickets(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-600 rounded p-2 text-white focus:border-blue-500 outline-none"
                />
              </div>
              <div>
                <label
                  htmlFor="score-input"
                  className="block text-xs text-slate-400 mb-1"
                >
                  Current Score
                </label>
                <input
                  id="score-input"
                  type="number"
                  min="0"
                  value={score}
                  onChange={(e) => setScore(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-600 rounded p-2 text-white focus:border-blue-500 outline-none"
                />
              </div>
              <div>
                <div className="block text-xs text-slate-400 mb-1">
                  Run Rate
                </div>
                <div className="w-full bg-slate-900 border border-slate-600 rounded p-2 text-blue-400 font-bold bg-opacity-50">
                  {currentRunRate}
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label
                  htmlFor="inning-select"
                  className="block text-xs text-slate-400 mb-1"
                >
                  Inning
                </label>
                <select
                  id="inning-select"
                  value={inning}
                  onChange={(e) => setInning(Number(e.target.value))}
                  className="w-full bg-slate-900 border border-slate-600 rounded p-2 text-white"
                >
                  <option value={1}>1st Inning (Setting Target)</option>
                  <option value={2}>2nd Inning (Chasing)</option>
                </select>
              </div>
              <div>
                <label
                  htmlFor="venue-select"
                  className="block text-xs text-slate-400 mb-1"
                >
                  Venue
                </label>
                <select
                  id="venue-select"
                  value={selectedVenueName}
                  onChange={(e) => setSelectedVenueName(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-600 rounded p-2 text-white"
                >
                  {venueData.map((v) => (
                    <option key={v.name} value={v.name}>
                      {v.name} ({v.venueType})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label
                  htmlFor="bowler-select"
                  className="block text-xs text-slate-400 mb-1"
                >
                  Upcoming Bowler Group
                </label>
                <select
                  id="bowler-select"
                  value={bowlerGroup}
                  onChange={(e) => setBowlerGroup(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-600 rounded p-2 text-white border-l-4 border-l-orange-500"
                >
                  {bowlerGroups.map((b) => (
                    <option key={b.type} value={b.type}>
                      {b.type}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <button
              onClick={handleOptimize}
              disabled={isLoading}
              className="w-full mt-4 bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 px-4 rounded transition-all shadow-lg flex justify-center items-center"
            >
              {isLoading ? "Analyzing Matchups..." : "Optimize Batting Order"}
            </button>
          </div>

          {/* MIDDLE & RIGHT PANELS */}
          <div className="lg:col-span-8 space-y-6">
            {/* Dugout Selection */}
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
              <div className="flex justify-between items-center mb-4 border-b border-slate-700 pb-2">
                <h2 className="text-xl font-semibold text-slate-200">
                  Dugout Availability
                </h2>
                <span className="text-xs bg-slate-700 px-2 py-1 rounded-full">
                  {selectedBatters.length} Selected
                </span>
              </div>

              <div className="flex gap-4 overflow-x-auto pb-4 scrollbar-thin scrollbar-thumb-slate-600">
                {batterData.map((batter) => {
                  const isSelected = selectedBatters.some(
                    (b) => b.name === batter.unique_name,
                  );
                  return (
                    <button
                      key={batter.unique_name}
                      onClick={() => toggleBatter(batter.unique_name)}
                      className={`min-w-[100px] flex flex-col items-center p-3 rounded-lg cursor-pointer transition-all border ${
                        isSelected
                          ? "bg-blue-900 bg-opacity-40 border-blue-500"
                          : "bg-slate-900 border-slate-700 hover:border-slate-500"
                      }`}
                    >
                      <img
                        src={batter.img_url}
                        alt={batter.common_name}
                        className="w-16 h-16 rounded-full object-cover mb-2 border-2 border-slate-800 bg-slate-200"
                      />
                      <span className="text-xs text-center font-medium leading-tight">
                        {batter.common_name}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* AI Output / Results Panel */}
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg min-h-[300px]">
              <h2 className="text-xl font-semibold text-slate-200 border-b border-slate-700 pb-2 mb-4">
                Model Recommendations
              </h2>

              {renderResultsContent}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
