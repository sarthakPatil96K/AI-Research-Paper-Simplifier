import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../services/api";
import SummaryPanel from "../components/SummaryPanel";
import AskPanel from "../components/AskPanel";
import styles from "./PaperPage.module.css";

export default function PaperPage() {
  const { paperId } = useParams();
  const [paper, setPaper] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState("summary"); // "summary" | "ask"

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    api
      .getPaper(paperId)
      .then((data) => { if (!cancelled) setPaper(data); })
      .catch((e) => { if (!cancelled) setError(e.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [paperId]);

  if (loading) return <div className={styles.center}>Loading…</div>;
  if (error) return <div className={styles.center + " " + styles.err}>{error}</div>;
  if (!paper) return null;

  const meta = paper.metadata || {};

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.crumb}>Paper</div>
        <h1 className={styles.title}>{meta.title || "Untitled"}</h1>
        <div className={styles.metaRow}>
          {meta.author && <span className="mono">{meta.author}</span>}
          {meta.page_count > 0 && <span className="mono">{meta.page_count} pages</span>}
          {paper.total_chunks && (
            <span className="mono">{paper.total_chunks} chunks</span>
          )}
          <span className="mono dim">{paperId.slice(0, 8)}</span>
        </div>
      </header>

      <div className={styles.tabs}>
        <button
          className={`${styles.tab} ${tab === "summary" ? styles.tabActive : ""}`}
          onClick={() => setTab("summary")}
        >
          Summary
        </button>
        <button
          className={`${styles.tab} ${tab === "ask" ? styles.tabActive : ""}`}
          onClick={() => setTab("ask")}
        >
          Ask
        </button>
      </div>

      <div className={styles.body}>
        {tab === "summary" ? (
          <SummaryPanel paperId={paperId} summary={paper.summary} />
        ) : (
          <AskPanel paperId={paperId} />
        )}
      </div>
    </div>
  );
}