const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function handle(res) {
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? ` — ${text}` : ""}`);
  }
  return res.json();
}

export const api = {
  listPapers: () => fetch(`${API}/api/papers`).then(handle),

  getPaper: (id) => fetch(`${API}/api/paper/${id}`).then(handle),

  getChunks: (id) => fetch(`${API}/api/paper/${id}/chunks`).then(handle),

  uploadPaper: (file, onProgress) => {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const form = new FormData();
      form.append("file", file);

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          reject(new Error(xhr.responseText || `Upload failed (${xhr.status})`));
        }
      };
      xhr.onerror = () => reject(new Error("Network error during upload"));

      xhr.open("POST", `${API}/api/upload`);
      xhr.send(form);
    });
  },

  ask: (paperId, question, topK = 5) =>
    fetch(`${API}/api/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ paper_id: paperId, question, top_k: topK }),
    }).then(handle),

  regenerateSummary: (paperId) =>
    fetch(`${API}/api/paper/${paperId}/regenerate-summary`, {
      method: "POST",
    }).then(handle),
};