// Placeholder page for the deployment test (backend plan, Task 1). Replaced by the web plan.
import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

function App() {
  const [health, setHealth] = useState<string>("checking the API…");
  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((h) => setHealth(`API ${h.status}: ${h.weather_packs} district weather files, Python ${h.python}`))
      .catch(() => setHealth("API not reachable"));
  }, []);
  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: "2rem" }}>
      <h1>AgriPV Lab — preview</h1>
      <p>{health}</p>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
