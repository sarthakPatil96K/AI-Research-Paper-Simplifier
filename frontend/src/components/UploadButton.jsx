import { useRef, useState } from "react";
import { api } from "../services/api";
import styles from "./UploadButton.module.css";

export default function UploadButton({ onUploaded }) {
  const inputRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);

  async function handleFile(file) {
    if (!file) return;
    setBusy(true);
    setError(null);
    setProgress(0);
    try {
      await api.uploadPaper(file, setProgress);
      onUploaded?.();
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
      setProgress(0);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        style={{ display: "none" }}
        onChange={(e) => handleFile(e.target.files?.[0])}
      />
      <button
        className={styles.btn}
        disabled={busy}
        onClick={() => inputRef.current?.click()}
      >
        {busy ? (
          <>
            <span className={styles.spinner} /> Uploading {progress}%
          </>
        ) : (
          <>+ Upload paper</>
        )}
      </button>

      {busy && (
        <div className={styles.progressTrack}>
          <div className={styles.progressFill} style={{ width: `${progress}%` }} />
        </div>
      )}

      {error && <div className={styles.error}>{error}</div>}
    </div>
  );
}