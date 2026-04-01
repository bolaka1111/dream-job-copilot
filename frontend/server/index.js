/**
 * Express.js API Server — Dream Job Copilot
 *
 * Routes:
 *   POST /api/pipeline/start         — upload resume, start stages 1-3
 *   GET  /api/pipeline/status/:id    — SSE stream of pipeline progress
 *   GET  /api/pipeline/result/:id    — get current pipeline state
 *   POST /api/feedback/:id           — submit feedback, trigger stages 5-7
 *   POST /api/apply/:id              — trigger stages 8-9
 *   POST /api/cover-letter/:id/:idx/regenerate — regenerate a cover letter
 *   GET  /api/download/:id/resume/:idx
 *   GET  /api/download/:id/cover-letter/:idx
 *   GET  /api/download/:id/resumes/all
 *   GET  /api/download/:id/cover-letters/all
 *   POST /api/checklist/:id/:idx     — toggle application checklist
 */

import express from "express";
import cors from "cors";
import path from "path";
import { fileURLToPath } from "url";

import pipelineRoutes from "./routes/pipeline.js";
import feedbackRoutes from "./routes/feedback.js";
import downloadRoutes from "./routes/download.js";
import coverLetterRoutes from "./routes/cover-letter.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors({ origin: true, credentials: true }));
app.use(express.json());

// Static uploads directory
const uploadsDir = path.resolve(__dirname, "..", "..", "uploads");
import fs from "fs";
fs.mkdirSync(uploadsDir, { recursive: true });

// Routes
app.use("/api/pipeline", pipelineRoutes);
app.use("/api/feedback", feedbackRoutes);
app.use("/api/download", downloadRoutes);
app.use("/api/cover-letter", coverLetterRoutes);

// Health check
app.get("/api/health", (_req, res) => {
  res.json({ status: "ok", timestamp: new Date().toISOString() });
});

app.listen(PORT, () => {
  console.log(`\n  🚀 Dream Job Copilot API running at http://localhost:${PORT}\n`);
});

export default app;
