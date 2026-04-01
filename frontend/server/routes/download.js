/**
 * Download routes — individual and ZIP downloads for resumes and cover letters.
 */

import { Router } from "express";
import path from "path";
import fs from "fs";
import archiver from "archiver";
import { getSession } from "../pipeline-bridge.js";

const router = Router();

/**
 * GET /api/download/:sessionId/resume/:jobIndex
 */
router.get("/:sessionId/resume/:jobIndex", (req, res) => {
  try {
    const session = getSession(req.params.sessionId);
    if (!session) return res.status(404).json({ error: "Session not found" });

    const idx = parseInt(req.params.jobIndex, 10);
    const resumes = session.state?.enhancedResumes || [];

    if (idx < 0 || idx >= resumes.length) {
      return res.status(404).json({ error: "Resume not found" });
    }

    const resume = resumes[idx];
    const filename = `resume_${resume.jobRole?.company || "company"}_${resume.jobRole?.title || "role"}.txt`
      .replace(/[^a-zA-Z0-9._-]/g, "_");

    res.setHeader("Content-Type", "text/plain");
    res.setHeader("Content-Disposition", `attachment; filename="${filename}"`);
    res.send(resume.enhancedText || resume.enhanced_text || "");
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/**
 * GET /api/download/:sessionId/cover-letter/:jobIndex
 */
router.get("/:sessionId/cover-letter/:jobIndex", (req, res) => {
  try {
    const session = getSession(req.params.sessionId);
    if (!session) return res.status(404).json({ error: "Session not found" });

    const idx = parseInt(req.params.jobIndex, 10);
    const letters = session.coverLetters || [];

    if (idx < 0 || idx >= letters.length || !letters[idx]) {
      return res.status(404).json({ error: "Cover letter not found" });
    }

    const letter = letters[idx];
    const filename = `cover_letter_${idx + 1}.txt`;

    res.setHeader("Content-Type", "text/plain");
    res.setHeader("Content-Disposition", `attachment; filename="${filename}"`);
    res.send(letter.text || "");
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/**
 * GET /api/download/:sessionId/resumes/all
 */
router.get("/:sessionId/resumes/all", (req, res) => {
  try {
    const session = getSession(req.params.sessionId);
    if (!session) return res.status(404).json({ error: "Session not found" });

    const resumes = session.state?.enhancedResumes || [];
    if (resumes.length === 0) {
      return res.status(404).json({ error: "No resumes available" });
    }

    res.setHeader("Content-Type", "application/zip");
    res.setHeader(
      "Content-Disposition",
      'attachment; filename="tailored_resumes.zip"'
    );

    const archive = archiver("zip", { zlib: { level: 9 } });
    archive.pipe(res);

    resumes.forEach((resume, i) => {
      const filename = `resume_${resume.jobRole?.company || "company"}_${resume.jobRole?.title || "role"}.txt`
        .replace(/[^a-zA-Z0-9._-]/g, "_");
      archive.append(resume.enhancedText || resume.enhanced_text || "", {
        name: filename,
      });
    });

    archive.finalize();
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/**
 * GET /api/download/:sessionId/cover-letters/all
 */
router.get("/:sessionId/cover-letters/all", (req, res) => {
  try {
    const session = getSession(req.params.sessionId);
    if (!session) return res.status(404).json({ error: "Session not found" });

    const letters = (session.coverLetters || []).filter(Boolean);
    if (letters.length === 0) {
      return res.status(404).json({ error: "No cover letters available" });
    }

    res.setHeader("Content-Type", "application/zip");
    res.setHeader(
      "Content-Disposition",
      'attachment; filename="cover_letters.zip"'
    );

    const archive = archiver("zip", { zlib: { level: 9 } });
    archive.pipe(res);

    letters.forEach((letter, i) => {
      archive.append(letter.text || "", {
        name: `cover_letter_${i + 1}.txt`,
      });
    });

    archive.finalize();
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export default router;
