import { useState } from "react";
import { api } from "../services/api";
import styles from "./SummaryPanel.module.css";

const FIELDS = [
  ["objective", "Objective"],
  ["problem", "Problem"],
  ["methodology", "Methodology"],
  ["datasets", "Datasets"],
  ["architecture", "Architecture"],
  ["results", "Results"],
  ["limitations", "Limitations"],
  ["future_work", "Future work"],
];

export default function SummaryPanel({ paperId, summary }) {
  const [busy, setBusy] = useState(false);
  const [data, setData] = useState(summary);

  async function regenerate() {
    setBusy(true);
    try {
      const res = await api.regenerateSummary(paperId);
      setData(res.summary);
    } catch (e) {
      alert(e.message);
    } finally {
      setBusy(false);
    }
  }

  if (!data) {
    return (
      <div className={styles.empty}>
        No summary available for this paper.
        <button className={styles.regen} onClick={regenerate} disabled={busy}>
          {busy ? "Generating…" : "Generate summary"}
        </button>
      </div>
    );
  }

  if (data.error) {
    return (
      <div className={styles.empty}>
        <div className={styles.errMsg}>{data.error}</div>
        <button className={styles.regen} onClick={regenerate} disabled={busy}>
          {busy ? "Retrying…" : "Retry"}
        </button>
      </div>
    );
  }

  return (
    <div className={styles.wrap}>
      <div className={styles.head}>
        <h2 className={styles.h2}>Structured Summary</h2>
        <button className={styles.regen} onClick={regenerate} disabled={busy}>
          {busy ? "Regenerating…" : "↻ Regenerate"}
        </button>
      </div>

      {data.title && (
        <div className={styles.card}>
          <div className={styles.label}>Title</div>
          <div className={styles.value}>{data.title}</div>
        </div>
      )}

      <div className={styles.grid}>
        {FIELDS.map(([key, label]) =>
          data[key] && data[key] !== "Not specified" ? (
            <div key={key} className={styles.card}>
              <div className={styles.label}>{label}</div>
              <div className={styles.value}>{data[key]}</div>
            </div>
          ) : null
        )}
      </div>

      {Array.isArray(data.keywords) && data.keywords.length > 0 && (
        <div className={styles.card}>
          <div className={styles.label}>Keywords</div>
          <div className={styles.tags}>
            {data.keywords.map((k, i) => (
              <span key={i} className={styles.tag}>{k}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}