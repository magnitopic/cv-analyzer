import json
import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import db
from pipeline import ejecutar_pipeline

UPLOADS_DIR = "/backend/uploads"

app = FastAPI(title="CV Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "*"],  # todo-> remove this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def save_file(file: UploadFile, subdir: str) -> str:
    dest_dir = os.path.join(UPLOADS_DIR, subdir)
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, file.filename)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return dest


@app.get("/health")
def health():
    return {"status": "ok"}


# --- CVs ---

@app.get("/cvs")
def list_cvs():
    return db.query("SELECT id, name, upload_date FROM cvs ORDER BY upload_date DESC")


@app.get("/cvs/{cv_id}")
def get_cv(cv_id: int):
    rows = db.query("SELECT id, name, upload_date FROM cvs WHERE id = %s", (cv_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="CV not found")
    return rows[0]


@app.post("/upload/cv")
async def upload_cv(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are supported")
    filepath = save_file(file, "cvs")
    return db.execute(
        "INSERT INTO cvs (name, filepath) VALUES (%s, %s) RETURNING id, name, upload_date",
        (file.filename, filepath),
    )


@app.get("/cvs/{cv_id}/download")
def download_cv(cv_id: int):
    rows = db.query("SELECT name FROM cvs WHERE id = %s", (cv_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="CV not found")
    path = os.path.join(UPLOADS_DIR, "cvs", rows[0]["name"])
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found on disk")
    return FileResponse(path, media_type="application/pdf", filename=rows[0]["name"])


# --- Job Descriptions ---

@app.get("/job-descriptions")
def list_job_descriptions():
    return db.query("SELECT id, name, upload_date FROM job_descriptions ORDER BY upload_date DESC")


@app.get("/job-descriptions/{jd_id}")
def get_job_description(jd_id: int):
    rows = db.query("SELECT id, name, upload_date FROM job_descriptions WHERE id = %s", (jd_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Job description not found")
    return rows[0]


@app.post("/upload/jd")
async def upload_jd(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are supported")
    filepath = save_file(file, "jds")
    return db.execute(
        "INSERT INTO job_descriptions (name, filepath) VALUES (%s, %s) RETURNING id, name, upload_date",
        (file.filename, filepath),
    )


# --- Analyses ---

@app.get("/analyses/{cv_id}/{jd_id}")
def get_analysis(cv_id: int, jd_id: int):
    rows = db.query(
        "SELECT id, cv_id, jd_id, result_json, analyzed_at FROM analyses WHERE cv_id = %s AND jd_id = %s",
        (cv_id, jd_id),
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return rows[0]


@app.post("/analyses/{cv_id}/{jd_id}")
def run_analysis(cv_id: int, jd_id: int):
    """
    Runs the full TalentMatch pipeline on the given CV and job description,
    then persists the result to the analyses table.

    If an analysis already exists for this pair it is overwritten with fresh results.
    Note: this endpoint is synchronous — the pipeline takes 20-60 s on first run
    while the embedding model loads; subsequent runs are faster.
    """
    cv_rows = db.query("SELECT filepath FROM cvs WHERE id = %s", (cv_id,))
    if not cv_rows:
        raise HTTPException(status_code=404, detail="CV not found")

    jd_rows = db.query("SELECT filepath FROM job_descriptions WHERE id = %s", (jd_id,))
    if not jd_rows:
        raise HTTPException(status_code=404, detail="Job description not found")

    ruta_cv     = cv_rows[0]["filepath"]
    ruta_puesto = jd_rows[0]["filepath"]

    if not os.path.exists(ruta_cv):
        raise HTTPException(status_code=404, detail=f"CV file not found on disk: {ruta_cv}")
    if not os.path.exists(ruta_puesto):
        raise HTTPException(status_code=404, detail=f"JD file not found on disk: {ruta_puesto}")

    result = ejecutar_pipeline(ruta_cv, ruta_puesto)

    row = db.execute(
        """
        INSERT INTO analyses (cv_id, jd_id, result_json)
        VALUES (%s, %s, %s)
        ON CONFLICT (cv_id, jd_id)
        DO UPDATE SET result_json = EXCLUDED.result_json, analyzed_at = CURRENT_TIMESTAMP
        RETURNING id, cv_id, jd_id, result_json, analyzed_at
        """,
        (cv_id, jd_id, json.dumps(result, ensure_ascii=False)),
    )
    return row
