import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

const API = "http://localhost:8000";

export default function Home() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedJd = searchParams.get("jd");

  const [cvs, setCvs] = useState([]);
  const [jds, setJds] = useState([]);

  const cvInputRef = useRef(null);
  const jdInputRef = useRef(null);

  useEffect(() => {
    fetch(`${API}/cvs`).then((r) => r.json()).then(setCvs);
    fetch(`${API}/job-descriptions`).then((r) => r.json()).then(setJds);
  }, []);

  async function handleUpload(file, endpoint, setter) {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API}/upload/${endpoint}`, { method: "POST", body: formData });
    const item = await res.json();
    if (res.ok) setter((prev) => [item, ...prev]);
  }

  return (
    <div style={{ maxWidth: 700, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h1>CV Analyzer</h1>

      <div style={{ display: "flex", gap: 8, marginBottom: 32 }}>
        <input ref={cvInputRef} type="file" accept=".pdf" style={{ display: "none" }}
          onChange={(e) => e.target.files[0] && handleUpload(e.target.files[0], "cv", setCvs)} />
        <button onClick={() => cvInputRef.current.click()}>+ Upload CV</button>

        <input ref={jdInputRef} type="file" accept=".pdf" style={{ display: "none" }}
          onChange={(e) => e.target.files[0] && handleUpload(e.target.files[0], "jd", setJds)} />
        <button onClick={() => jdInputRef.current.click()}>+ Upload Job Description</button>
      </div>

      <div style={{ marginBottom: 24 }}>
        <label htmlFor="jd-select" style={{ marginRight: 8, fontWeight: "bold" }}>
          Job Description:
        </label>
        <select
          id="jd-select"
          value={selectedJd ?? ""}
          onChange={(e) =>
            e.target.value
              ? setSearchParams({ jd: e.target.value })
              : setSearchParams({})
          }
        >
          <option value="">— select one —</option>
          {jds.map((jd) => (
            <option key={jd.id} value={jd.id}>
              {jd.name}
            </option>
          ))}
        </select>
      </div>

      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ borderBottom: "2px solid #ccc", textAlign: "left" }}>
            <th style={{ padding: "8px 0" }}>Name</th>
            <th style={{ padding: "8px 0" }}>Uploaded</th>
          </tr>
        </thead>
        <tbody>
          {cvs.length === 0 && (
            <tr>
              <td colSpan={2} style={{ padding: "16px 0", color: "#888" }}>
                No CVs uploaded yet.
              </td>
            </tr>
          )}
          {cvs.map((cv) => (
            <tr key={cv.id} style={{ borderBottom: "1px solid #eee" }}>
              <td style={{ padding: "10px 0" }}>
                <Link
                  to={`/cv/${cv.id}${selectedJd ? `?jd=${selectedJd}` : ""}`}
                  style={{ textDecoration: "none", color: "#0070f3" }}
                >
                  {cv.name}
                </Link>
              </td>
              <td style={{ padding: "10px 0", color: "#555", fontSize: 14 }}>
                {new Date(cv.upload_date).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
