import React, { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  LineChart,
  Line,
  Area,
  AreaChart,
} from "recharts";

const API_BASE = "http://localhost:8000";

interface FeatureImportance {
  feature: string;
  importance: number;
}

interface ClassLabel {
  id: number;
  name: string;
  description: string;
}

interface ModelInfo {
  model_type: string;
  algorithm: string;
  task: string;
  num_classes: number;
  class_labels: ClassLabel[];
  scoring_formula: {
    formula: string;
    weights: Record<string, number>;
  };
  training_features: string[];
  num_features: number;
  feature_importances: FeatureImportance[];
  model_params: Record<string, any>;
  tree_count: number | string;
  training_data: Record<string, string>;
  inference_time: string;
  categorical_handling: string;
}

interface ExploreDataPoint {
  value: number;
  Pressure: number;
  Strike_Rotation: number;
  Boundary: number;
}

interface ComparisonResult {
  label: string;
  Pressure: number;
  Strike_Rotation: number;
  Boundary: number;
  Tactical_Score: number;
}

// Color palette
const COLORS = {
  pressure: "#ef4444",
  rotation: "#3b82f6",
  boundary: "#10b981",
  accent: "#8b5cf6",
  muted: "#64748b",
  bg: "#1e293b",
  card: "#334155",
};

const CLASS_COLORS = [COLORS.pressure, COLORS.rotation, COLORS.boundary];

export default function ModelDashboard() {
  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Feature exploration state
  const [exploreFeature, setExploreFeature] = useState("Over");
  const [exploreData, setExploreData] = useState<ExploreDataPoint[]>([]);
  const [exploreLoading, setExploreLoading] = useState(false);

  // Scenario comparison state
  const [comparisons, setComparisons] = useState<ComparisonResult[]>([]);
  const [compLoading, setCompLoading] = useState(false);

  // Active tab
  const [activeTab, setActiveTab] = useState<
    "overview" | "features" | "explorer" | "compare"
  >("overview");

  // Fetch model info
  useEffect(() => {
    fetch(`${API_BASE}/api/model-info`)
      .then((res) => res.json())
      .then((data) => {
        setModelInfo(data);
        setLoading(false);
      })
      .catch((err) => {
        setError("Failed to load model info. Is the backend running?");
        setLoading(false);
      });
  }, []);

  // Fetch feature exploration data
  const fetchExploreData = useCallback(async (feature: string) => {
    setExploreLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/model-explore`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feature, steps: 20 }),
      });
      const data = await res.json();
      setExploreData(data.data);
    } catch {
      setExploreData([]);
    } finally {
      setExploreLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === "explorer") {
      fetchExploreData(exploreFeature);
    }
  }, [activeTab, exploreFeature, fetchExploreData]);

  // Run default scenario comparisons
  const runDefaultComparisons = useCallback(async () => {
    setCompLoading(true);
    try {
      const scenarios = [
        {
          label: "Early Middle Overs (Over 7)",
          Over: 7,
          Cumulative_Wickets: 1,
          Current_Run_Rate: 6.5,
          Bowler_Group: "Pace",
        },
        {
          label: "Deep Middle Overs (Over 13)",
          Over: 13,
          Cumulative_Wickets: 3,
          Current_Run_Rate: 7.5,
          Bowler_Group: "Off-Spin",
        },
        {
          label: "Under Pressure (4 wkts, low RR)",
          Over: 10,
          Cumulative_Wickets: 4,
          Current_Run_Rate: 5.0,
          Bowler_Group: "Leg-Spin",
        },
        {
          label: "Dominant Position (1 wkt, high RR)",
          Over: 10,
          Cumulative_Wickets: 1,
          Current_Run_Rate: 9.5,
          Bowler_Group: "Pace",
        },
        {
          label: "Chase Scenario (2nd Inning)",
          Over: 12,
          Cumulative_Wickets: 2,
          Current_Run_Rate: 8.0,
          Inning: 2,
          Bowler_Group: "Left-Arm Orthodox",
        },
      ];
      const res = await fetch(`${API_BASE}/api/model-compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenarios }),
      });
      const data = await res.json();
      setComparisons(data.comparisons);
    } catch {
      setComparisons([]);
    } finally {
      setCompLoading(false);
    }
  }, []);

  useEffect(() => {
    if (activeTab === "compare") {
      runDefaultComparisons();
    }
  }, [activeTab, runDefaultComparisons]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="animate-pulse flex flex-col items-center">
          <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
          <span className="mt-4 text-slate-400 text-lg">
            Loading Model Dashboard...
          </span>
        </div>
      </div>
    );
  }

  if (error || !modelInfo) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="bg-slate-800 p-8 rounded-xl border border-red-500/30 text-center max-w-md">
          <div className="text-red-400 text-5xl mb-4">⚠</div>
          <h2 className="text-xl font-bold text-slate-100 mb-2">
            Connection Error
          </h2>
          <p className="text-slate-400 mb-4">
            {error || "Could not load model information."}
          </p>
          <p className="text-slate-500 text-sm">
            Make sure the FastAPI backend is running on port 8000.
          </p>
        </div>
      </div>
    );
  }

  // Prepare data for charts
  const topFeatures = modelInfo.feature_importances.slice(0, 10);
  const classDistData = modelInfo.class_labels.map((c) => ({
    name: c.name,
    weight: Math.abs(
      modelInfo.scoring_formula.weights[c.name] ||
        modelInfo.scoring_formula.weights[c.name.replace(" ", "_")] ||
        1,
    ),
  }));

  const scoringWeights = [
    { name: "Boundary", weight: 1.5, color: COLORS.boundary },
    { name: "Strike Rotation", weight: 1.0, color: COLORS.rotation },
    { name: "Pressure", weight: -1.0, color: COLORS.pressure },
  ];

  const tabs = [
    { key: "overview" as const, label: "Overview" },
    { key: "features" as const, label: "Feature Importance" },
    { key: "explorer" as const, label: "Feature Explorer" },
    { key: "compare" as const, label: "Scenario Comparison" },
  ];

  const explorableFeatures = [
    "Over",
    "Cumulative_Wickets",
    "Current_Run_Rate",
    "Batter_Last5_SR",
    "Batter_vs_BowlerType_SR",
  ];

  return (
    <div className="min-h-screen min-w-[100vw] bg-slate-900 text-slate-100 p-6 py-12 font-sans">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <header className="border-b border-slate-700 pb-4 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-blue-400">
              ML Model Dashboard
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              CatBoost Classifier — Middle-Overs Strike Rate Optimization
            </p>
          </div>
          <Link
            to="/"
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-200 rounded-lg transition-colors text-sm font-medium"
          >
            ← Back to Optimizer
          </Link>
        </header>

        {/* Tab Navigation */}
        <div className="flex gap-1 bg-slate-800 p-1 rounded-lg border border-slate-700 w-fit">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                activeTab === tab.key
                  ? "bg-blue-600 text-white shadow-lg"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-700"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* ───────────── OVERVIEW TAB ───────────── */}
        {activeTab === "overview" && (
          <div className="space-y-6">
            {/* Model Identity Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                title="Algorithm"
                value={modelInfo.model_type}
                subtitle={modelInfo.algorithm}
                icon="🌲"
              />
              <StatCard
                title="Task Type"
                value={modelInfo.task}
                subtitle={`${modelInfo.num_classes} output classes`}
                icon="🎯"
              />
              <StatCard
                title="Features"
                value={String(modelInfo.num_features)}
                subtitle="Input dimensions"
                icon="📊"
              />
              <StatCard
                title="Trees"
                value={String(modelInfo.tree_count)}
                subtitle="Ensemble size"
                icon="🌳"
              />
            </div>

            {/* Architecture Diagram & Class Labels */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Pipeline Architecture */}
              <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                <h3 className="text-lg font-semibold text-slate-200 mb-4">
                  Model Pipeline Architecture
                </h3>
                <div className="space-y-3">
                  {[
                    {
                      step: "1",
                      title: "Input Features",
                      desc: "Match context (Over, Wickets, Run Rate, Inning, Venue, Bowler) + Batter stats",
                      color: "blue",
                    },
                    {
                      step: "2",
                      title: "CatBoost Encoding",
                      desc: "Native categorical feature handling — no manual one-hot encoding needed",
                      color: "purple",
                    },
                    {
                      step: "3",
                      title: "Gradient Boosted Trees",
                      desc: `Ensemble of ${modelInfo.tree_count} decision trees with ordered boosting`,
                      color: "emerald",
                    },
                    {
                      step: "4",
                      title: "Softmax Output",
                      desc: "3-class probability distribution per delivery",
                      color: "orange",
                    },
                    {
                      step: "5",
                      title: "Tactical Scoring",
                      desc: modelInfo.scoring_formula.formula,
                      color: "red",
                    },
                  ].map((item) => (
                    <div
                      key={item.step}
                      className="flex items-start gap-3 p-3 bg-slate-900 rounded-lg"
                    >
                      <div
                        className={`w-8 h-8 rounded-full bg-${item.color}-500/20 text-${item.color}-400 flex items-center justify-center font-bold text-sm flex-shrink-0`}
                      >
                        {item.step}
                      </div>
                      <div>
                        <div className="font-medium text-slate-200 text-sm">
                          {item.title}
                        </div>
                        <div className="text-xs text-slate-400 mt-0.5">
                          {item.desc}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Output Classes */}
              <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                <h3 className="text-lg font-semibold text-slate-200 mb-4">
                  Prediction Classes & Scoring
                </h3>
                <div className="space-y-4 mb-6">
                  {modelInfo.class_labels.map((cls, i) => (
                    <div
                      key={cls.id}
                      className="flex items-start gap-3 p-3 bg-slate-900 rounded-lg"
                    >
                      <div
                        className="w-4 h-4 rounded-full mt-0.5 flex-shrink-0"
                        style={{ backgroundColor: CLASS_COLORS[i] }}
                      />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-slate-200">
                            Class {cls.id}: {cls.name}
                          </span>
                          <span
                            className="text-xs px-2 py-0.5 rounded-full font-mono"
                            style={{
                              color: CLASS_COLORS[i],
                              backgroundColor: `${CLASS_COLORS[i]}20`,
                            }}
                          >
                            weight:{" "}
                            {scoringWeights.find((w) => w.name === cls.name)
                              ?.weight ?? "N/A"}
                          </span>
                        </div>
                        <div className="text-xs text-slate-400 mt-0.5">
                          {cls.description}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Scoring Formula Visual */}
                <div className="bg-slate-900 p-4 rounded-lg">
                  <div className="text-xs text-slate-400 mb-2 uppercase tracking-wider">
                    Tactical Utility Score Formula
                  </div>
                  <div className="font-mono text-sm text-slate-200 leading-relaxed">
                    <span className="text-emerald-400">Boundary × 1.5</span>
                    {" + "}
                    <span className="text-blue-400">Strike Rotation × 1.0</span>
                    {" − "}
                    <span className="text-red-400">Pressure × 1.0</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Model Hyperparameters */}
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
              <h3 className="text-lg font-semibold text-slate-200 mb-4">
                Model Hyperparameters
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                {Object.entries(modelInfo.model_params).map(([key, val]) => (
                  <div key={key} className="bg-slate-900 p-3 rounded-lg">
                    <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                      {key.replace(/_/g, " ")}
                    </div>
                    <div className="text-lg font-bold text-blue-400">
                      {String(val)}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Training Data Info */}
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
              <h3 className="text-lg font-semibold text-slate-200 mb-4">
                Training Data
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {Object.entries(modelInfo.training_data).map(([key, val]) => (
                  <div key={key} className="bg-slate-900 p-4 rounded-lg">
                    <div className="text-xs text-slate-400 uppercase tracking-wider mb-1">
                      {key.replace(/_/g, " ")}
                    </div>
                    <div className="text-sm text-slate-200">{val}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ───────────── FEATURE IMPORTANCE TAB ───────────── */}
        {activeTab === "features" && (
          <div className="space-y-6">
            {/* Horizontal Bar Chart */}
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
              <h3 className="text-lg font-semibold text-slate-200 mb-1">
                Feature Importance Ranking
              </h3>
              <p className="text-sm text-slate-400 mb-4">
                How much each feature contributes to the model's predictions
                (CatBoost built-in importance)
              </p>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart
                  data={topFeatures}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 140, bottom: 5 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#374151"
                    horizontal={false}
                  />
                  <XAxis type="number" stroke="#94a3b8" fontSize={12} />
                  <YAxis
                    dataKey="feature"
                    type="category"
                    stroke="#94a3b8"
                    fontSize={12}
                    width={130}
                    tick={{ fill: "#cbd5e1" }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1e293b",
                      border: "1px solid #475569",
                      borderRadius: "8px",
                      color: "#e2e8f0",
                    }}
                    formatter={(value: any) => [
                      Number(value).toFixed(4),
                      "Importance",
                    ]}
                  />
                  <Bar
                    dataKey="importance"
                    fill="#3b82f6"
                    radius={[0, 6, 6, 0]}
                    barSize={24}
                  >
                    {topFeatures.map((_, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={
                          index === 0
                            ? "#10b981"
                            : index < 3
                              ? "#3b82f6"
                              : "#6366f1"
                        }
                        opacity={1 - index * 0.06}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Feature Importance Pie Chart + Radar */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Pie Chart */}
              <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                <h3 className="text-lg font-semibold text-slate-200 mb-4">
                  Importance Distribution (Top 6)
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={topFeatures.slice(0, 6)}
                      dataKey="importance"
                      nameKey="feature"
                      cx="50%"
                      cy="50%"
                      outerRadius={110}
                      label={({ name, percent }: any) =>
                        `${name} (${((percent || 0) * 100).toFixed(1)}%)`
                      }
                      labelLine={{ stroke: "#64748b" }}
                      fontSize={11}
                    >
                      {topFeatures.slice(0, 6).map((_, i) => (
                        <Cell
                          key={`pie-${i}`}
                          fill={
                            [
                              "#10b981",
                              "#3b82f6",
                              "#8b5cf6",
                              "#f59e0b",
                              "#ef4444",
                              "#06b6d4",
                            ][i]
                          }
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1e293b",
                        border: "1px solid #475569",
                        borderRadius: "8px",
                        color: "#e2e8f0",
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Radar Chart */}
              <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
                <h3 className="text-lg font-semibold text-slate-200 mb-4">
                  Feature Radar Profile (Top 6)
                </h3>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart
                    data={topFeatures.slice(0, 6).map((f) => ({
                      ...f,
                      importance:
                        (f.importance /
                          Math.max(...topFeatures.map((x) => x.importance))) *
                        100,
                    }))}
                  >
                    <PolarGrid stroke="#374151" />
                    <PolarAngleAxis
                      dataKey="feature"
                      stroke="#94a3b8"
                      fontSize={11}
                      tick={{ fill: "#cbd5e1" }}
                    />
                    <PolarRadiusAxis
                      angle={30}
                      domain={[0, 100]}
                      stroke="#475569"
                      fontSize={10}
                    />
                    <Radar
                      name="Importance"
                      dataKey="importance"
                      stroke="#3b82f6"
                      fill="#3b82f6"
                      fillOpacity={0.3}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1e293b",
                        border: "1px solid #475569",
                        borderRadius: "8px",
                        color: "#e2e8f0",
                      }}
                      formatter={(value: any) => [
                        `${Number(value).toFixed(1)}%`,
                        "Relative Importance",
                      ]}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* All Features Table */}
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
              <h3 className="text-lg font-semibold text-slate-200 mb-4">
                All Training Features
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="text-xs text-slate-400 uppercase bg-slate-900">
                    <tr>
                      <th className="px-4 py-3 rounded-tl-lg">#</th>
                      <th className="px-4 py-3">Feature Name</th>
                      <th className="px-4 py-3 text-right">Importance</th>
                      <th className="px-4 py-3 text-right rounded-tr-lg">
                        Relative %
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {modelInfo.feature_importances.map((f, i) => {
                      const maxImp =
                        modelInfo.feature_importances[0].importance;
                      const relPct =
                        maxImp > 0 ? (f.importance / maxImp) * 100 : 0;
                      return (
                        <tr
                          key={f.feature}
                          className="border-b border-slate-700 last:border-0 hover:bg-slate-700/30"
                        >
                          <td className="px-4 py-2 text-slate-500 font-mono text-xs">
                            {i + 1}
                          </td>
                          <td className="px-4 py-2 font-medium">{f.feature}</td>
                          <td className="px-4 py-2 text-right font-mono text-blue-400">
                            {f.importance.toFixed(4)}
                          </td>
                          <td className="px-4 py-2 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <div className="w-24 h-2 bg-slate-700 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-blue-500 rounded-full"
                                  style={{ width: `${relPct}%` }}
                                />
                              </div>
                              <span className="text-xs text-slate-400 w-12 text-right">
                                {relPct.toFixed(1)}%
                              </span>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* ───────────── FEATURE EXPLORER TAB ───────────── */}
        {activeTab === "explorer" && (
          <div className="space-y-6">
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-slate-200">
                    Interactive Feature Impact Explorer
                  </h3>
                  <p className="text-sm text-slate-400 mt-1">
                    See how varying a single feature changes class probabilities
                    while other features stay fixed
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <label className="text-sm text-slate-400">
                    Explore Feature:
                  </label>
                  <select
                    value={exploreFeature}
                    onChange={(e) => setExploreFeature(e.target.value)}
                    className="bg-slate-900 border border-slate-600 rounded px-3 py-2 text-white text-sm"
                  >
                    {explorableFeatures.map((f) => (
                      <option key={f} value={f}>
                        {f.replace(/_/g, " ")}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {exploreLoading ? (
                <div className="h-[400px] flex items-center justify-center">
                  <div className="animate-pulse flex flex-col items-center">
                    <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    <span className="mt-3 text-slate-400 text-sm">
                      Computing predictions...
                    </span>
                  </div>
                </div>
              ) : (
                <>
                  {/* Stacked Area Chart */}
                  <ResponsiveContainer width="100%" height={400}>
                    <AreaChart
                      data={exploreData}
                      margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis
                        dataKey="value"
                        stroke="#94a3b8"
                        fontSize={12}
                        label={{
                          value: exploreFeature.replace(/_/g, " "),
                          position: "insideBottom",
                          offset: -5,
                          fill: "#94a3b8",
                        }}
                      />
                      <YAxis
                        stroke="#94a3b8"
                        fontSize={12}
                        label={{
                          value: "Probability (%)",
                          angle: -90,
                          position: "insideLeft",
                          fill: "#94a3b8",
                        }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#1e293b",
                          border: "1px solid #475569",
                          borderRadius: "8px",
                          color: "#e2e8f0",
                        }}
                        formatter={(value: any, name: any) => [
                          `${Number(value).toFixed(2)}%`,
                          String(name).replace(/_/g, " "),
                        ]}
                      />
                      <Legend
                        wrapperStyle={{ color: "#94a3b8", fontSize: "12px" }}
                      />
                      <Area
                        type="monotone"
                        dataKey="Pressure"
                        stackId="1"
                        stroke={COLORS.pressure}
                        fill={COLORS.pressure}
                        fillOpacity={0.6}
                      />
                      <Area
                        type="monotone"
                        dataKey="Strike_Rotation"
                        stackId="1"
                        stroke={COLORS.rotation}
                        fill={COLORS.rotation}
                        fillOpacity={0.6}
                        name="Strike Rotation"
                      />
                      <Area
                        type="monotone"
                        dataKey="Boundary"
                        stackId="1"
                        stroke={COLORS.boundary}
                        fill={COLORS.boundary}
                        fillOpacity={0.6}
                      />
                    </AreaChart>
                  </ResponsiveContainer>

                  {/* Line chart overlay */}
                  <div className="mt-6">
                    <h4 className="text-sm font-medium text-slate-300 mb-3">
                      Individual Probability Trends
                    </h4>
                    <ResponsiveContainer width="100%" height={300}>
                      <LineChart
                        data={exploreData}
                        margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis dataKey="value" stroke="#94a3b8" fontSize={12} />
                        <YAxis stroke="#94a3b8" fontSize={12} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: "#1e293b",
                            border: "1px solid #475569",
                            borderRadius: "8px",
                            color: "#e2e8f0",
                          }}
                          formatter={(value: any, name: any) => [
                            `${Number(value).toFixed(2)}%`,
                            String(name).replace(/_/g, " "),
                          ]}
                        />
                        <Legend
                          wrapperStyle={{ color: "#94a3b8", fontSize: "12px" }}
                        />
                        <Line
                          type="monotone"
                          dataKey="Pressure"
                          stroke={COLORS.pressure}
                          strokeWidth={2}
                          dot={{ r: 3 }}
                          activeDot={{ r: 5 }}
                        />
                        <Line
                          type="monotone"
                          dataKey="Strike_Rotation"
                          stroke={COLORS.rotation}
                          strokeWidth={2}
                          dot={{ r: 3 }}
                          activeDot={{ r: 5 }}
                          name="Strike Rotation"
                        />
                        <Line
                          type="monotone"
                          dataKey="Boundary"
                          stroke={COLORS.boundary}
                          strokeWidth={2}
                          dot={{ r: 3 }}
                          activeDot={{ r: 5 }}
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                </>
              )}
            </div>

            {/* Explanation */}
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
              <h3 className="text-lg font-semibold text-slate-200 mb-3">
                How to Read This
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div className="bg-slate-900 p-4 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-3 h-3 rounded-full bg-red-500" />
                    <span className="font-medium text-red-400">
                      Pressure (Class 0)
                    </span>
                  </div>
                  <p className="text-slate-400">
                    Higher probability means the batter is more likely to face a
                    dot ball or risky delivery under these conditions.
                  </p>
                </div>
                <div className="bg-slate-900 p-4 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-3 h-3 rounded-full bg-blue-500" />
                    <span className="font-medium text-blue-400">
                      Strike Rotation (Class 1)
                    </span>
                  </div>
                  <p className="text-slate-400">
                    Higher probability means safe singles/doubles are likely —
                    indicating controlled, low-risk batting.
                  </p>
                </div>
                <div className="bg-slate-900 p-4 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="w-3 h-3 rounded-full bg-emerald-500" />
                    <span className="font-medium text-emerald-400">
                      Boundary (Class 2)
                    </span>
                  </div>
                  <p className="text-slate-400">
                    Higher probability means the batter is likely to hit a 4 or
                    6 — aggressive, high-reward outcome.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ───────────── SCENARIO COMPARISON TAB ───────────── */}
        {activeTab === "compare" && (
          <div className="space-y-6">
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 shadow-lg">
              <h3 className="text-lg font-semibold text-slate-200 mb-1">
                Scenario Comparison
              </h3>
              <p className="text-sm text-slate-400 mb-6">
                Compare how the model predictions change across different match
                situations
              </p>

              {compLoading ? (
                <div className="h-[400px] flex items-center justify-center">
                  <div className="animate-pulse flex flex-col items-center">
                    <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                    <span className="mt-3 text-slate-400 text-sm">
                      Running scenario comparisons...
                    </span>
                  </div>
                </div>
              ) : (
                <>
                  {/* Grouped Bar Chart */}
                  <ResponsiveContainer width="100%" height={400}>
                    <BarChart
                      data={comparisons}
                      margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                      <XAxis
                        dataKey="label"
                        stroke="#94a3b8"
                        fontSize={11}
                        angle={-20}
                        textAnchor="end"
                        interval={0}
                        height={80}
                        tick={{ fill: "#cbd5e1" }}
                      />
                      <YAxis
                        stroke="#94a3b8"
                        fontSize={12}
                        label={{
                          value: "Probability (%)",
                          angle: -90,
                          position: "insideLeft",
                          fill: "#94a3b8",
                        }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: "#1e293b",
                          border: "1px solid #475569",
                          borderRadius: "8px",
                          color: "#e2e8f0",
                        }}
                        formatter={(value: any, name: any) => [
                          `${Number(value).toFixed(2)}%`,
                          String(name).replace(/_/g, " "),
                        ]}
                      />
                      <Legend
                        wrapperStyle={{ color: "#94a3b8", fontSize: "12px" }}
                      />
                      <Bar
                        dataKey="Pressure"
                        fill={COLORS.pressure}
                        radius={[4, 4, 0, 0]}
                      />
                      <Bar
                        dataKey="Strike_Rotation"
                        fill={COLORS.rotation}
                        radius={[4, 4, 0, 0]}
                        name="Strike Rotation"
                      />
                      <Bar
                        dataKey="Boundary"
                        fill={COLORS.boundary}
                        radius={[4, 4, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>

                  {/* Tactical Score Comparison */}
                  <div className="mt-8">
                    <h4 className="text-sm font-medium text-slate-300 mb-4">
                      Tactical Utility Scores
                    </h4>
                    <div className="space-y-3">
                      {comparisons
                        .sort((a, b) => b.Tactical_Score - a.Tactical_Score)
                        .map((c, i) => {
                          const maxScore = Math.max(
                            ...comparisons.map((x) =>
                              Math.abs(x.Tactical_Score),
                            ),
                          );
                          const barWidth =
                            maxScore > 0
                              ? (Math.abs(c.Tactical_Score) / maxScore) * 100
                              : 0;
                          return (
                            <div
                              key={c.label}
                              className="flex items-center gap-4"
                            >
                              <div className="w-64 text-sm text-slate-300 flex-shrink-0 truncate">
                                {i === 0 && (
                                  <span className="text-xs text-emerald-400 mr-1">
                                    ★
                                  </span>
                                )}
                                {c.label}
                              </div>
                              <div className="flex-1 h-6 bg-slate-700 rounded-full overflow-hidden">
                                <div
                                  className={`h-full rounded-full ${c.Tactical_Score >= 0 ? "bg-gradient-to-r from-blue-600 to-emerald-500" : "bg-gradient-to-r from-red-600 to-red-400"}`}
                                  style={{ width: `${barWidth}%` }}
                                />
                              </div>
                              <div
                                className={`w-20 text-right font-bold font-mono text-sm ${c.Tactical_Score >= 0 ? "text-emerald-400" : "text-red-400"}`}
                              >
                                {c.Tactical_Score.toFixed(1)}
                              </div>
                            </div>
                          );
                        })}
                    </div>
                  </div>

                  {/* Detailed Table */}
                  <div className="mt-8 overflow-x-auto">
                    <table className="w-full text-left text-sm text-slate-300">
                      <thead className="text-xs text-slate-400 uppercase bg-slate-900">
                        <tr>
                          <th className="px-4 py-3 rounded-tl-lg">Scenario</th>
                          <th className="px-4 py-3 text-center">Pressure %</th>
                          <th className="px-4 py-3 text-center">
                            Strike Rotation %
                          </th>
                          <th className="px-4 py-3 text-center">Boundary %</th>
                          <th className="px-4 py-3 text-center rounded-tr-lg">
                            Tactical Score
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {comparisons.map((c) => (
                          <tr
                            key={c.label}
                            className="border-b border-slate-700 last:border-0 hover:bg-slate-700/30"
                          >
                            <td className="px-4 py-3 font-medium">{c.label}</td>
                            <td className="px-4 py-3 text-center text-red-400">
                              {c.Pressure.toFixed(2)}%
                            </td>
                            <td className="px-4 py-3 text-center text-blue-400">
                              {c.Strike_Rotation.toFixed(2)}%
                            </td>
                            <td className="px-4 py-3 text-center text-emerald-400">
                              {c.Boundary.toFixed(2)}%
                            </td>
                            <td className="px-4 py-3 text-center font-bold">
                              <span
                                className={`px-3 py-1 rounded ${c.Tactical_Score >= 0 ? "bg-emerald-500/20 text-emerald-400" : "bg-red-500/20 text-red-400"}`}
                              >
                                {c.Tactical_Score.toFixed(2)}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Stat Card Sub-Component ──────────────────────────────────────────────── */
function StatCard({
  title,
  value,
  subtitle,
  icon,
}: {
  title: string;
  value: string;
  subtitle: string;
  icon: string;
}) {
  return (
    <div className="bg-slate-800 p-5 rounded-xl border border-slate-700 shadow-lg hover:border-blue-500/40 transition-colors">
      <div className="flex items-center gap-3 mb-2">
        <span className="text-2xl">{icon}</span>
        <span className="text-xs text-slate-400 uppercase tracking-wider">
          {title}
        </span>
      </div>
      <div className="text-xl font-bold text-slate-100">{value}</div>
      <div className="text-xs text-slate-400 mt-1">{subtitle}</div>
    </div>
  );
}
