/**
 * Pipeline routes — start, SSE status, and result retrieval.
 */

import { Router } from "express";
import multer from "multer";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";
import {
  startPipeline,
  getSession,
  addSSEClient,
  removeSSEClient,
} from "../pipeline-bridge.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const uploadsDir = path.resolve(__dirname, "..", "..", "..", "uploads");
fs.mkdirSync(uploadsDir, { recursive: true });

const upload = multer({
  storage: multer.diskStorage({
    destination: (_req, _file, cb) => cb(null, uploadsDir),
    filename: (_req, file, cb) => {
      const uniqueName = `${Date.now()}-${file.originalname}`;
      cb(null, uniqueName);
    },
  }),
  fileFilter: (_req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase();
    if ([".pdf", ".docx"].includes(ext)) {
      cb(null, true);
    } else {
      cb(new Error("Only PDF and DOCX files are supported"));
    }
  },
  limits: { fileSize: 10 * 1024 * 1024 }, // 10 MB
});

const router = Router();

/**
 * POST /api/pipeline/start
 * Upload a resume and kick off stages 1-3.
 */
router.post("/start", upload.single("resume"), (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: "No resume file uploaded" });
    }

    const resumePath = req.file.path;
    const options = {
      dreamRole: req.body.dreamRole || "",
      searchScope: req.body.searchScope || "global",
    };

    const sessionId = startPipeline(resumePath, options);

    console.log(`[API] Pipeline started: session=${sessionId.slice(0, 8)}, file=${req.file.originalname}`);

    res.json({
      sessionId,
      status: "running",
      message: "Pipeline started — connect to SSE for live updates",
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/**
 * GET /api/pipeline/status/:sessionId
 * Server-Sent Events stream for pipeline progress.
 */
router.get("/status/:sessionId", (req, res) => {
  const { sessionId } = req.params;
  const session = getSession(sessionId);

  if (!session) {
    return res.status(404).json({ error: "Session not found" });
  }

  // Set up SSE headers
  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    Connection: "keep-alive",
    "X-Accel-Buffering": "no",
  });

  // Send initial state
  res.write(
    `event: connected\ndata: ${JSON.stringify({
      sessionId,
      status: session.status,
      stage: session.stage,
    })}\n\n`
  );

  // Register this client
  addSSEClient(sessionId, res);
  console.log(`[SSE] Client connected for session ${sessionId.slice(0, 8)}, total clients: ${session.sseClients?.size || 'unknown'}`);

  // Heartbeat every 30s to keep connection alive
  const heartbeat = setInterval(() => {
    res.write(": heartbeat\n\n");
  }, 30000);

  // Cleanup on disconnect
  req.on("close", () => {
    clearInterval(heartbeat);
    removeSSEClient(sessionId, res);
  });
});

/**
 * GET /api/pipeline/result/:sessionId
 * Return the full current pipeline state.
 */
router.get("/result/:sessionId", (req, res) => {
  const session = getSession(req.params.sessionId);
  if (!session) {
    return res.status(404).json({ error: "Session not found" });
  }

  res.json({
    sessionId: session.id,
    status: session.status,
    stage: session.stage,
    stageName: session.stageName,
    state: session.state,
    coverLetters: session.coverLetters || [],
    applicationChecklist: session.applicationChecklist || [],
  });
});

export default router;
