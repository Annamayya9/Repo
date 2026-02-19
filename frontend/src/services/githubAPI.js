/**
 * Pipeline API Service (backend-only, no direct GitHub calls from frontend)
 */

const PIPELINE_API_BASE = import.meta.env.VITE_PIPELINE_API_BASE || "http://localhost:8000";
const PIPELINE_API_TOKEN = import.meta.env.VITE_PIPELINE_API_TOKEN;

class PipelineService {
  getHeaders() {
    const headers = {
      "Content-Type": "application/json",
      "Accept": "application/json"
    };

    if (PIPELINE_API_TOKEN) {
      headers["Authorization"] = `Bearer ${PIPELINE_API_TOKEN}`;
    }

    return headers;
  }

  async triggerPipeline(payload = {}) {
    if (!PIPELINE_API_TOKEN) {
      return { success: false, error: "Missing pipeline API token" };
    }

    try {
      const res = await fetch(`${PIPELINE_API_BASE}/pipeline/trigger`, {
        method: "POST",
        headers: this.getHeaders(),
        body: JSON.stringify(payload)
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        return { success: false, error: data.detail || data.error || `HTTP ${res.status}` };
      }

      return { success: true, ...data };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }

  async getLatestRunStatus() {
    try {
      const res = await fetch(`${PIPELINE_API_BASE}/pipeline/status`, {
        method: "GET",
        headers: this.getHeaders()
      });

      if (!res.ok) return null;
      return await res.json();
    } catch (error) {
      console.error("Error fetching latest run status:", error);
      return null;
    }
  }

  async isWorkflowRunning() {
    const status = await this.getLatestRunStatus();
    if (!status) return false;
    return status.status === "queued" || status.status === "in_progress" || status.status === "running";
  }

  async getLatestArtifactDownloadURL() {
    try {
      const res = await fetch(`${PIPELINE_API_BASE}/pipeline/latest-artifact`, {
        method: "GET",
        headers: this.getHeaders()
      });

      if (!res.ok) return null;
      const data = await res.json();

      if (!data || !data.downloadURL) return null;
      return data;
    } catch (error) {
      console.error("Error fetching latest artifact URL:", error);
      return null;
    }
  }

  // Backward compatibility if anything else still calls this
  async getWorkflowRuns() {
    return [];
  }
}

export default new PipelineService();