import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

const API = "http://localhost:8000";

const LEVEL_COLOR = {
  "Alta idoneidad":     "#16a34a",
  "Idoneidad moderada": "#ca8a04",
  "Idoneidad baja":     "#ea580c",
  "Muy baja idoneidad": "#dc2626",
};

function ScoreBar({ value }) {
  return (
    <div style={{ background: "#e5e7eb", borderRadius: 4, height: 8, width: "100%", marginTop: 4 }}>
      <div style={{
        background: "#0070f3",
        borderRadius: 4,
        height: 8,
        width: `${Math.round(value * 100)}%`,
        transition: "width 0.4s ease",
      }} />
    </div>
  );
}

function AnalysisResult({ analysis }) {
  const r = analysis.result_json;
  const score = r.score;
  const nivel = score.nivel;
  const color = LEVEL_COLOR[nivel] ?? "#555";

  return (
    <div style={{ marginTop: 32 }}>
      <h2 style={{ marginBottom: 16 }}>Analysis Result</h2>

      {/* Score summary */}
      <div style={{ padding: 20, background: "#f4f4f4", borderRadius: 6, marginBottom: 24 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginBottom: 4 }}>
          <span style={{ fontSize: 36, fontWeight: "bold", color }}>
            {Math.round(score.final * 100)}%
          </span>
          <span style={{ fontSize: 16, color, fontWeight: 600 }}>{nivel}</span>
        </div>

        <div style={{ marginTop: 16, display: "flex", flexDirection: "column", gap: 10 }}>
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "#555" }}>
              <span>Global similarity <small style={{ color: "#888" }}>(50%)</small></span>
              <span>{Math.round(score.global * 100)}%</span>
            </div>
            <ScoreBar value={score.global} />
          </div>
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "#555" }}>
              <span>Keyword coverage <small style={{ color: "#888" }}>(35%)</small></span>
              <span>{Math.round(score.cobertura * 100)}%</span>
            </div>
            <ScoreBar value={score.cobertura} />
          </div>
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, color: "#555" }}>
              <span>Gap penalty <small style={{ color: "#888" }}>(15%)</small></span>
              <span>{Math.round(score.gaps * 100)}%</span>
            </div>
            <ScoreBar value={score.gaps} />
          </div>
        </div>
      </div>

      {/* Explanation */}
      <div style={{ marginBottom: 24 }}>
        <h3 style={{ marginBottom: 8 }}>
          Explanation{" "}
          <small style={{ fontWeight: "normal", color: "#888", fontSize: 13 }}>
            via {r.explicacion.metodo}
          </small>
        </h3>
        <p style={{ color: "#333", lineHeight: 1.6, margin: 0 }}>{r.explicacion.texto}</p>
      </div>

      {/* Keywords */}
      <div style={{ display: "flex", gap: 16 }}>
        <div style={{ flex: 1 }}>
          <h3 style={{ marginBottom: 8, color: "#16a34a" }}>
            ✓ Covered ({r.matching.keywords_cubiertas.length})
          </h3>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {r.matching.keywords_cubiertas.length === 0
              ? <span style={{ color: "#888", fontSize: 13 }}>None</span>
              : r.matching.keywords_cubiertas.map((kw) => (
                  <span key={kw} style={{
                    background: "#dcfce7", color: "#166534",
                    padding: "2px 8px", borderRadius: 12, fontSize: 13,
                  }}>{kw}</span>
                ))
            }
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <h3 style={{ marginBottom: 8, color: "#dc2626" }}>
            ✗ Gaps ({r.matching.keywords_gaps.length})
          </h3>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {r.matching.keywords_gaps.length === 0
              ? <span style={{ color: "#888", fontSize: 13 }}>None</span>
              : r.matching.keywords_gaps.map((kw) => (
                  <span key={kw} style={{
                    background: "#fee2e2", color: "#991b1b",
                    padding: "2px 8px", borderRadius: 12, fontSize: 13,
                  }}>{kw}</span>
                ))
            }
          </div>
        </div>
      </div>

      <p style={{ marginTop: 20, fontSize: 12, color: "#aaa" }}>
        Analyzed at {new Date(analysis.analyzed_at).toLocaleString()} ·{" "}
        model: {r.metadatos.modelo_embeddings}
      </p>
    </div>
  );
}

export default function CVDetail() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const jdId = searchParams.get("jd");

  const [cv, setCv] = useState(null);
  const [jd, setJd] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [analysisChecked, setAnalysisChecked] = useState(false);
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState(null);

  useEffect(() => {
    fetch(`${API}/cvs/${id}`).then((r) => r.json()).then(setCv);
  }, [id]);

  useEffect(() => {
    if (!jdId) return;
    setAnalysis(null);
    setAnalysisChecked(false);
    setRunError(null);
    fetch(`${API}/job-descriptions/${jdId}`).then((r) => r.json()).then(setJd);
    fetch(`${API}/analyses/${id}/${jdId}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => { setAnalysis(data); setAnalysisChecked(true); });
  }, [id, jdId]);

  async function handleRunAnalysis() {
    setRunning(true);
    setRunError(null);
    try {
      const res = await fetch(`${API}/analyses/${id}/${jdId}`, { method: "POST" });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `Server error ${res.status}`);
      }
      const data = await res.json();
      setAnalysis(data);
    } catch (e) {
      setRunError(e.message);
    } finally {
      setRunning(false);
    }
  }

  return (
    <div style={{ maxWidth: 700, margin: "40px auto", fontFamily: "sans-serif" }}>
      <Link to={`/${jdId ? `?jd=${jdId}` : ""}`} style={{ color: "#0070f3", fontSize: 14 }}>
        ← Back
      </Link>

      <div style={{ display: "flex", alignItems: "center", gap: 16, marginTop: 16 }}>
        <h1 style={{ margin: 0 }}>{cv?.name ?? "Loading..."}</h1>
        {cv && (
          <a
            href={`${API}/cvs/${id}/download`}
            download={cv.name}
            style={{ fontSize: 14, color: "#0070f3", textDecoration: "none" }}
          >
            ↓ Download
          </a>
        )}
      </div>
      {cv && (
        <p style={{ color: "#555", fontSize: 14 }}>
          Uploaded: {new Date(cv.upload_date).toLocaleString()}
        </p>
      )}

      <div style={{ marginTop: 32, padding: 16, background: "#f4f4f4", borderRadius: 6 }}>
        <p style={{ margin: 0 }}>
          <strong>CV:</strong> {cv?.name ?? "—"}
        </p>
        <p style={{ margin: "8px 0 0" }}>
          <strong>Job Description:</strong>{" "}
          {jdId ? (jd?.name ?? "Loading...") : <em style={{ color: "#888" }}>None selected</em>}
        </p>

        {jdId && analysisChecked && (
          <div style={{ marginTop: 12, display: "flex", alignItems: "center", gap: 12 }}>
            <button
              onClick={handleRunAnalysis}
              disabled={running}
              style={{
                padding: "6px 14px",
                background: running ? "#93c5fd" : "#0070f3",
                color: "#fff",
                border: "none",
                borderRadius: 4,
                cursor: running ? "not-allowed" : "pointer",
                fontSize: 14,
              }}
            >
              {running
                ? "Running… (this may take ~30s)"
                : analysis
                ? "Re-run Analysis"
                : "Run Analysis"}
            </button>
            {analysis && !running && (
              <span style={{ fontSize: 13, color: "#16a34a" }}>✓ Analysis available</span>
            )}
          </div>
        )}

        {runError && (
          <p style={{ marginTop: 8, color: "#dc2626", fontSize: 13 }}>Error: {runError}</p>
        )}
      </div>

      {!jdId && (
        <p style={{ marginTop: 24, color: "#888" }}>
          Select a job description on the home page to see analysis.
        </p>
      )}

      {analysis && <AnalysisResult analysis={analysis} />}
    </div>
  );
}
