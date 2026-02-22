import { BrowserRouter, Routes, Route } from "react-router-dom";
import TacticalDashboard from "./components/TacticalDashboard";
import ModelDashboard from "./components/ModelDashboard";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<TacticalDashboard />} />
        <Route path="/model-dashboard" element={<ModelDashboard />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
