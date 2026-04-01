/**
 * Pipeline Bridge — spawns the Python pipeline as a child process,
 * captures JSON output from each stage, and emits SSE events.
 *
 * Sessions are stored in-memory (Map<sessionId, SessionData>).
 */

import { spawn } from "child_process";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";
import { v4 as uuidv4 } from "uuid";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(__dirname, "..", "..");

// Use the project's venv Python; fall back to system python3
const PYTHON_BIN = fs.existsSync(path.join(PROJECT_ROOT, ".venv", "bin", "python3"))
  ? path.join(PROJECT_ROOT, ".venv", "bin", "python3")
  : "python3";

/** @typedef {{ id: string, status: string, stage: number, stageName: string, state: object, sseClients: Set<import('express').Response>, outputDir: string }} Session */

/** @type {Map<string, Session>} */
const sessions = new Map();

const STAGE_NAMES = [
  "upload",
  "parse_resume",
  "search_jobs",
  "recommend_roles",
  "collect_feedback",
  "refine_search",
  "fetch_reviews",
  "select_best_jobs",
  "enhance_resumes",
  "apply_to_jobs",
];

/**
 * Broadcast an SSE event to all clients listening on a session.
 */
function broadcast(sessionId, event, data) {
  const session = sessions.get(sessionId);
  if (!session) return;
  const payload = `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
  for (const res of session.sseClients) {
    res.write(payload);
  }
}

/**
 * Create a new pipeline session and start stages 1-3.
 * Returns the session ID immediately; progress is streamed via SSE.
 */
export function startPipeline(resumePath, options = {}) {
  const sessionId = uuidv4();
  const outputDir = path.join(PROJECT_ROOT, "output", sessionId);

  const session = {
    id: sessionId,
    status: "running",
    stage: 1,
    stageName: "parse_resume",
    state: {},
    sseClients: new Set(),
    outputDir,
    resumePath,
    options,
    coverLetters: [],
    applicationChecklist: [],
  };
  sessions.set(sessionId, session);

  // Spawn Python pipeline in non-interactive mode (stages 1-3)
  // We run a helper script that outputs JSON per stage
  const pythonArgs = [
    "-u",
    path.join(PROJECT_ROOT, "frontend", "server", "run_pipeline.py"),
    "--resume",
    resumePath,
    "--output-dir",
    outputDir,
    "--mode",
    "initial", // stages 1-3
  ];

  if (options.dreamRole) {
    pythonArgs.push("--dream-role", options.dreamRole);
  }
  if (options.searchScope) {
    pythonArgs.push("--search-scope", options.searchScope);
  }

  runPythonStages(sessionId, pythonArgs, 1, 3);

  return sessionId;
}

/**
 * Continue the pipeline from stages 5-7 after user feedback.
 */
export function continuePipelineWithFeedback(sessionId, feedback) {
  const session = sessions.get(sessionId);
  if (!session) throw new Error("Session not found");

  session.status = "running";
  session.state.userFeedback = feedback;

  // Write feedback to a temp file for the Python process (sync — must exist before spawn)
  const feedbackPath = path.join(session.outputDir, "feedback.json");
  fs.mkdirSync(session.outputDir, { recursive: true });
  fs.writeFileSync(feedbackPath, JSON.stringify(feedback));

  const pythonArgs = [
    "-u",
    path.join(PROJECT_ROOT, "frontend", "server", "run_pipeline.py"),
    "--resume",
    session.resumePath,
    "--output-dir",
    session.outputDir,
    "--mode",
    "refine", // stages 5-7
    "--feedback-file",
    feedbackPath,
    "--state-file",
    path.join(session.outputDir, "pipeline_state.json"),
  ];

  runPythonStages(sessionId, pythonArgs, 5, 7);
}

/**
 * Continue the pipeline for stages 8-9 (enhance resumes + apply).
 */
export function continuePipelineApply(sessionId) {
  const session = sessions.get(sessionId);
  if (!session) throw new Error("Session not found");

  session.status = "running";

  const pythonArgs = [
    "-u",
    path.join(PROJECT_ROOT, "frontend", "server", "run_pipeline.py"),
    "--resume",
    session.resumePath,
    "--output-dir",
    session.outputDir,
    "--mode",
    "apply", // stages 8-9
    "--state-file",
    path.join(session.outputDir, "pipeline_state.json"),
  ];

  runPythonStages(sessionId, pythonArgs, 8, 9);
}

/**
 * Spawn Python and process stdout for JSON stage updates.
 */
function runPythonStages(sessionId, pythonArgs, startStage, endStage) {
  const session = sessions.get(sessionId);
  if (!session) return;

  broadcast(sessionId, "stage_update", {
    stage: startStage,
    stageName: STAGE_NAMES[startStage] || `stage_${startStage}`,
    status: "running",
    progress: Math.round((startStage / 10) * 100),
    message: getStageMessage(startStage, "running"),
  });

  console.log(`[Pipeline ${sessionId.slice(0, 8)}] Spawning ${PYTHON_BIN} with args:`, pythonArgs.map(a => a.includes('/') ? '...' + a.split('/').slice(-2).join('/') : a).join(' '));

  const proc = spawn(PYTHON_BIN, pythonArgs, {
    cwd: PROJECT_ROOT,
    env: { ...process.env, PYTHONUNBUFFERED: "1" },
  });

  let buffer = "";

  proc.stdout.on("data", (chunk) => {
    buffer += chunk.toString();
    // Try to parse complete JSON lines
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      try {
        const msg = JSON.parse(trimmed);
        handlePipelineMessage(sessionId, msg);
      } catch {
        // Non-JSON output — broadcast as log
        broadcast(sessionId, "log", { message: trimmed });
      }
    }
  });

  proc.stderr.on("data", (chunk) => {
    const text = chunk.toString().trim();
    if (text) {
      console.error(`[Pipeline ${sessionId.slice(0, 8)}] stderr:`, text);
      broadcast(sessionId, "log", { message: text, level: "warn" });
    }
  });

  proc.on("error", (err) => {
    console.error(`[Pipeline ${sessionId.slice(0, 8)}] spawn error:`, err.message);
    session.status = "error";
    broadcast(sessionId, "stage_update", {
      stage: session.stage,
      stageName: STAGE_NAMES[session.stage] || "",
      status: "error",
      message: `Failed to start Python: ${err.message}`,
    });
  });

  proc.on("close", (code) => {
    console.log(`[Pipeline ${sessionId.slice(0, 8)}] Process exited with code ${code}`);
    if (buffer.trim()) {
      try {
        handlePipelineMessage(sessionId, JSON.parse(buffer.trim()));
      } catch {
        /* ignore */
      }
    }

    if (code !== 0 && session.status !== "completed") {
      session.status = "error";
      broadcast(sessionId, "stage_update", {
        stage: session.stage,
        stageName: STAGE_NAMES[session.stage] || "",
        status: "error",
        message: `Pipeline exited with code ${code}`,
      });
    }
  });
}

function handlePipelineMessage(sessionId, msg) {
  const session = sessions.get(sessionId);
  if (!session) return;

  console.log(`[Pipeline ${sessionId.slice(0, 8)}] Message:`, msg.type, msg.stage || '', msg.stageName || '', msg.message ? `| ${msg.message}` : '');

  if (msg.type === "stage_start") {
    session.stage = msg.stage;
    session.stageName = msg.stageName;
    broadcast(sessionId, "stage_update", {
      stage: msg.stage,
      stageName: msg.stageName,
      status: "running",
      progress: Math.round((msg.stage / 10) * 100),
      message: getStageMessage(msg.stage, "running"),
    });
  } else if (msg.type === "stage_complete") {
    // Merge result data into session state
    if (msg.data) {
      session.state = { ...session.state, ...msg.data };
    }
    broadcast(sessionId, "stage_update", {
      stage: msg.stage,
      stageName: msg.stageName,
      status: "completed",
      progress: Math.round(((msg.stage + 1) / 10) * 100),
      message: getStageMessage(msg.stage, "completed"),
      result: msg.data || {},
    });
  } else if (msg.type === "pipeline_complete") {
    session.status = "completed";
    if (msg.data) {
      session.state = { ...session.state, ...msg.data };
    }
    broadcast(sessionId, "stage_update", {
      stage: msg.stage || session.stage,
      stageName: "complete",
      status: "completed",
      progress: 100,
      message: "All stages complete!",
    });
  } else if (msg.type === "error") {
    session.status = "error";
    broadcast(sessionId, "stage_update", {
      stage: msg.stage || session.stage,
      stageName: STAGE_NAMES[msg.stage] || "",
      status: "error",
      message: msg.message || "An unknown error occurred",
    });
  }
}

function getStageMessage(stage, status) {
  const messages = {
    1: {
      running: "We're reading your resume and building your profile...",
      completed: "Your resume profile is ready!",
    },
    2: {
      running: "Searching across job portals for matching roles...",
      completed: "Job search complete — found matching roles!",
    },
    3: {
      running: "Our AI is ranking the best roles for you...",
      completed: "Top recommendations are ready!",
    },
    5: {
      running: "Refining search based on your preferences...",
      completed: "Refined job results are in!",
    },
    6: {
      running: "Fetching employee reviews for your top companies...",
      completed: "Employee reviews collected!",
    },
    7: {
      running: "Selecting the best job candidates for you...",
      completed: "Best jobs selected!",
    },
    8: {
      running: "Tailoring your resume for each dream role...",
      completed: "Enhanced resumes ready!",
    },
    9: {
      running: "Preparing your application materials...",
      completed: "Applications prepared — you're all set!",
    },
  };
  return messages[stage]?.[status] || `Stage ${stage} ${status}`;
}

export function getSession(sessionId) {
  return sessions.get(sessionId) || null;
}

export function addSSEClient(sessionId, res) {
  const session = sessions.get(sessionId);
  if (!session) return false;
  session.sseClients.add(res);
  return true;
}

export function removeSSEClient(sessionId, res) {
  const session = sessions.get(sessionId);
  if (session) {
    session.sseClients.delete(res);
  }
}

export function updateCoverLetter(sessionId, jobIndex, coverLetter) {
  const session = sessions.get(sessionId);
  if (!session) throw new Error("Session not found");
  if (!session.coverLetters) session.coverLetters = [];
  session.coverLetters[jobIndex] = coverLetter;
}

export function toggleChecklist(sessionId, jobIndex) {
  const session = sessions.get(sessionId);
  if (!session) throw new Error("Session not found");
  if (!session.applicationChecklist) session.applicationChecklist = [];
  session.applicationChecklist[jobIndex] =
    !session.applicationChecklist[jobIndex];
  return session.applicationChecklist;
}
