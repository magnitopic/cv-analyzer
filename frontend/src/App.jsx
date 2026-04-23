import { useState } from "react";

const API_URL = "http://localhost:8000";

function App() {
	const [file, setFile] = useState(null);
	const [result, setResult] = useState(null);
	const [error, setError] = useState(null);
	const [loading, setLoading] = useState(false);

	async function handleSubmit(e) {
		e.preventDefault();
		if (!file) return;

		setLoading(true);
		setResult(null);
		setError(null);

		const formData = new FormData();
		formData.append("file", file);

		try {
			const res = await fetch(`${API_URL}/upload`, {
				method: "POST",
				body: formData,
			});
			const data = await res.json();
			if (!res.ok) throw new Error(data.detail ?? "Upload failed");
			setResult(data.result);
		} catch (err) {
			setError(err.message);
		} finally {
			setLoading(false);
		}
	}

	return (
		<div
			style={{
				maxWidth: 600,
				margin: "40px auto",
				fontFamily: "sans-serif",
			}}
		>
			<h1>CV Analyzer</h1>
			<form onSubmit={handleSubmit}>
				<input
					type="file"
					accept=".pdf"
					onChange={(e) => setFile(e.target.files[0])}
				/>
				<button
					type="submit"
					disabled={!file || loading}
					style={{ marginLeft: 8 }}
				>
					{loading ? "Processing..." : "Upload"}
				</button>
			</form>

			{error && <p style={{ color: "red", marginTop: 16 }}>{error}</p>}

			{result && (
				<div style={{ marginTop: 24 }}>
					<h2>Result</h2>
					<pre
						style={{
							background: "#f4f4f4",
							padding: 16,
							whiteSpace: "pre-wrap",
						}}
					>
						{result}
					</pre>
				</div>
			)}
		</div>
	);
}

export default App;
