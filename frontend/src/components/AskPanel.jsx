import { useState } from "react";
import { api } from "../services/api";
import styles from "./AskPanel.module.css";

const SUGGESTIONS = [
  "What is the main objective of this paper?",
  "Summarize the methodology in 3 sentences.",
  "What limitations do the authors mention?",
  "What are the key findings?",
];

export default function AskPanel({ paperId }) {
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState(null);

  async function ask(q) {
    const text = (q ?? question).trim();
    if (!text || asking) return;
    setQuestion("");
    setAsking(true);
    setError(null);

    const entry = { id: Date.now(), question: text, answer: null, sources: [] };
    setHistory((h) => [...h, entry]);

    try {
      const data = await api.ask(paperId, text);
      setHistory((h) =>
        h.map((e) =>
          e.id === entry.id
            ? { ...e, answer: data.answer, sources: data.sources || [] }
            : e
        )
      );
    } catch (e) {
      setError(e.message);
      setHistory((h) => h.filter((x) => x.id !== entry.id));
    } finally {
      setAsking(false);
    }
  }

  return (
    <div className={styles.wrap}>
      {history.length === 0 && (
        <div className={styles.empty}>
          <div className={styles.emptyTitle}>Ask about this paper</div>
          <div className={styles.emptyHint}>
            Answers are grounded in the paper's content. Each response cites its sources.
          </div>
          <div className={styles.suggestions}>
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                className={styles.suggestion}
                onClick={() => ask(s)}
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className={styles.thread}>
        {history.map((entry) => (
          <div key={entry.id} className={styles.turn}>
            <div className={styles.question}>
              <div className={styles.qAvatar}>Q</div>
              <div className={styles.qText}>{entry.question}</div>
            </div>

            <div className={styles.answer}>
              <div className={styles.aAvatar}>A</div>
              <div className={styles.aBody}>
                {entry.answer === null ? (
                  <TypingDots />
                ) : (
                  <>
                    <div className={styles.aText}>{entry.answer}</div>
                    {entry.sources.length > 0 && (
                      <div className={styles.sources}>
                        <div className={styles.sourcesLabel}>Sources</div>
                        <div className={styles.sourceList}>
                          {entry.sources.map((s, i) => (
                            <div key={i} className={styles.source}>
                              <span className={styles.sourceDot} />
                              <span className={styles.sourceSec}>{s.section}</span>
                              <span className="dim mono">p.{s.page_number}</span>
                              <span className={styles.sourceScore}>
                                {s.score.toFixed(2)}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.composer}>
        <textarea
          rows={2}
          placeholder="Ask a question about this paper…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              ask();
            }
          }}
          className={styles.input}
        />
        <button
          className={styles.send}
          disabled={asking || !question.trim()}
          onClick={() => ask()}
        >
          {asking ? <span className={styles.miniSpinner} /> : "→"}
        </button>
      </div>
    </div>
  );
}

function TypingDots() {
  return (
    <div className={styles.typing}>
      <span /><span /><span />
    </div>
  );
}