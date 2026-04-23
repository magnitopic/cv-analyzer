import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";

const API = "http://localhost:8000";

export default function CVDetail() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const jdId = searchParams.get("jd");

  const [cv, setCv] = useState(null);
  const [jd, setJd] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [analysisChecked, setAnalysisChecked] = useState(false);

  useEffect(() => {
    fetch(`${API}/cvs/${id}`).then((r) => r.json()).then(setCv);
  }, [id]);

  useEffect(() => {
    if (!jdId) return;
    fetch(`${API}/job-descriptions/${jdId}`).then((r) => r.json()).then(setJd);
    fetch(`${API}/analyses/${id}/${jdId}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => { setAnalysis(data); setAnalysisChecked(true); });
  }, [id, jdId]);

  return (
    <div style={{ maxWidth: 700, margin: "40px auto", fontFamily: "sans-serif" }}>
      <Link to={`/${jdId ? `?jd=${jdId}` : ""}`} style={{ color: "#0070f3", fontSize: 14 }}>
        ← Back
      </Link>

      <h1 style={{ marginTop: 16 }}>{cv?.name ?? "Loading..."}</h1>
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
          <p style={{ margin: "8px 0 0" }}>
            <strong>Analysis:</strong>{" "}
            {analysis ? (
              <span style={{ color: "green" }}>Available</span>
            ) : (
              <span style={{ color: "#888" }}>Not yet analyzed</span>
            )}
          </p>
        )}
      </div>

      {!jdId && (
        <p style={{ marginTop: 24, color: "#888" }}>
          Select a job description on the home page to see analysis.
        </p>
      )}
    </div>
  );
}
