/**
 * Cover Letter routes — regeneration with tone/length controls.
 */

import { Router } from "express";
import {
  getSession,
  continuePipelineApply,
  updateCoverLetter,
} from "../pipeline-bridge.js";

const router = Router();

/**
 * POST /api/cover-letter/:sessionId/:jobIndex/regenerate
 * Body: { tone: 'professional'|'conversational'|'concise', length: 'short'|'standard'|'long' }
 */
router.post("/:sessionId/:jobIndex/regenerate", async (req, res) => {
  try {
    const session = getSession(req.params.sessionId);
    if (!session) return res.status(404).json({ error: "Session not found" });

    const idx = parseInt(req.params.jobIndex, 10);
    const { tone = "professional", length = "standard" } = req.body;

    const bestJobs = session.state?.shortlistedJobs || session.state?.bestJobs || [];
    const job = bestJobs[idx];

    if (!job) {
      return res.status(404).json({ error: "Job not found at this index" });
    }

    // Generate cover letter using the Python bridge
    const { spawn } = await import("child_process");
    const path = await import("path");
    const { fileURLToPath } = await import("url");

    const __dirname = path.dirname(fileURLToPath(import.meta.url));
    const PROJECT_ROOT = path.resolve(__dirname, "..", "..", "..");

    // Use venv Python; fall back to system python3
    const fs = await import("fs");
    const PYTHON_BIN = fs.existsSync(path.join(PROJECT_ROOT, ".venv", "bin", "python3"))
      ? path.join(PROJECT_ROOT, ".venv", "bin", "python3")
      : "python3";

    const proc = spawn(
      PYTHON_BIN,
      [
        "-u",
        path.join(PROJECT_ROOT, "frontend", "server", "run_pipeline.py"),
        "--mode",
        "cover-letter",
        "--state-file",
        path.join(session.outputDir, "pipeline_state.json"),
        "--job-index",
        String(idx),
        "--tone",
        tone,
        "--length",
        length,
      ],
      { cwd: PROJECT_ROOT, env: { ...process.env, PYTHONUNBUFFERED: "1" } }
    );

    let output = "";
    proc.stdout.on("data", (chunk) => {
      output += chunk.toString();
    });

    proc.stderr.on("data", (chunk) => {
      console.error("Cover letter stderr:", chunk.toString());
    });

    proc.on("close", (code) => {
      try {
        const result = JSON.parse(output.trim());
        const coverLetter = {
          text: result.cover_letter || result.text || "",
          tone,
          length,
          jobRole: job,
        };
        updateCoverLetter(req.params.sessionId, idx, coverLetter);
        res.json({ coverLetter });
      } catch {
        res.status(500).json({
          error: "Failed to generate cover letter",
          raw: output,
        });
      }
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/**
 * POST /api/apply/:sessionId
 * Trigger stages 8-9 (enhance resumes + cover letters + apply).
 */
router.post("/apply/:sessionId", (req, res) => {
  try {
    const session = getSession(req.params.sessionId);
    if (!session) return res.status(404).json({ error: "Session not found" });

    continuePipelineApply(req.params.sessionId);

    res.json({
      status: "running",
      message: "Generating tailored resumes and cover letters...",
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export default router;
