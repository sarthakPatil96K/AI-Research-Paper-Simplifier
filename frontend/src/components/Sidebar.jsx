import { NavLink } from "react-router-dom";
import { usePapers } from "../hooks/usePapers";
import UploadButton from "./UploadButton";
import styles from "./Sidebar.module.css";

export default function Sidebar() {
  const { papers, loading, error, refresh } = usePapers();

  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <div className={styles.logo}>◇</div>
        <div>
          <div className={styles.brandName}>Paper Simplifier</div>
          <div className={styles.brandSub}>AI research assistant</div>
        </div>
      </div>

      <UploadButton onUploaded={refresh} />

      <div className={styles.section}>
        <div className={styles.sectionHeader}>
          <span>Papers</span>
          <button onClick={refresh} className={styles.refreshBtn} title="Refresh">
            ↻
          </button>
        </div>

        {loading && <div className={styles.empty}>Loading…</div>}
        {error && <div className={styles.error}>{error}</div>}
        {!loading && !error && papers.length === 0 && (
          <div className={styles.empty}>
            No papers yet. Upload a PDF to get started.
          </div>
        )}

        <nav className={styles.paperList}>
          {papers.map((p) => (
            <NavLink
              key={p.paper_id}
              to={`/paper/${p.paper_id}`}
              className={({ isActive }) =>
                `${styles.paperItem} ${isActive ? styles.active : ""}`
              }
            >
              <div className={styles.paperTitle}>{p.title || "Untitled"}</div>
              <div className={styles.paperMeta}>
                {p.author || "Unknown"} · {p.page_count || 0}p
              </div>
            </NavLink>
          ))}
        </nav>
      </div>

      <div className={styles.footer}>
        <span className="muted">Local · v0.1</span>
      </div>
    </aside>
  );
}