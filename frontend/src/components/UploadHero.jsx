import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";
import styles from "./UploadHero.module.css";

export default function UploadHero() {
  const navigate = useNavigate();
  const inputRef = useRef(null);
  const [drag, setDrag] = useState(false);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);

  async function handleFile(file) {
    if (!file) return;
    if (file.type !== "application/pdf") {
      setError("Please upload a PDF file.");
      return;
    }
    setBusy(true);
    setError(null);
    setProgress(0);
    try {
      const data = await api.uploadPaper(file, setProgress);
      navigate(`/paper/${data.paper_id}`);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
      setProgress(0);
    }
  }

  function onDrop(e) {
    e.preventDefault();
    setDrag(false);
    handleFile(e.dataTransfer.files?.[0]);
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.hero}>
        <div className={styles.badge}>AI Research Assistant</div>
        <h1 className={styles.title}>
          Understand any paper in <span className={styles.grad}>minutes</span>
        </h1>
        <p className={styles.subtitle}>
          Upload a research paper. Get a structured summary, search across sections, and ask
          questions with grounded answers.
        </p>

        <div
          className={`${styles.dropzone} ${drag ? styles.drag : ""} ${busy ? styles.busy : ""}`}
          onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={onDrop}
          onClick={() => !busy && inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf"
            hidden
            onChange={(e) => handleFile(e.target.files?.[0])}
          />

          {busy ? (
            <>
              <div className={styles.bigSpinner} />
              <div className={styles.dropTitle}>Processing… {progress}%</div>
              <div className={styles.dropHint}>Parsing PDF, chunking, embedding</div>
            </>
          ) : (
            <>
              <div className={styles.icon}>↑</div>
              <div className={styles.dropTitle}>
                Drop your PDF here, or <span className={styles.link}>browse</span>
              </div>
              <div className={styles.dropHint}>Max 50MB · PDF only</div>
            </>
          )}
        </div>

        {error && <div className={styles.error}>{error}</div>}

        <div className={styles.features}>
          <Feature title="Structured summary" desc="Title, objective, method, results, limitations." />
          <Feature title="Grounded Q&A" desc="Answers cite the exact sections of your paper." />
          <Feature title="Semantic + lexical" desc="Hybrid retrieval finds the right passage." />
        </div>
      </div>
    </div>
  );
}

function Feature({ title, desc }) {
  return (
    <div className={styles.feature}>
      <div className={styles.featureTitle}>{title}</div>
      <div className={styles.featureDesc}>{desc}</div>
    </div>
  );
}