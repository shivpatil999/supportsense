import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

function App() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API_BASE}/tickets`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch tickets");
        return res.json();
      })
      .then((data) => {
        setTickets(data.tickets || []);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  return (
    <div style={{ padding: "2rem", fontFamily: "system-ui" }}>
      <h1>SupportSense</h1>

      {loading && <p>Loading tickets…</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}

      {!loading && !error && (
        <ul>
          {tickets.map((t) => (
            <li key={t.ticket_id}>
              <strong>{t.title}</strong> — {t.status}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default App;
