/**
 * Feedback routes — submit user selections + preferences, trigger stages 5-7.
 */

import { Router } from "express";
import {
  getSession,
  continuePipelineWithFeedback,
  toggleChecklist,
} from "../pipeline-bridge.js";

const router = Router();

/**
 * POST /api/feedback/:sessionId
 * Body: { selectedJobs: number[], preferences: { ... } }
 */
router.post("/:sessionId", (req, res) => {
  try {
    const { sessionId } = req.params;
    const session = getSession(sessionId);

    if (!session) {
      return res.status(404).json({ error: "Session not found" });
    }

    const { selectedJobs, preferences } = req.body;

    if (!selectedJobs || !Array.isArray(selectedJobs)) {
      return res
        .status(400)
        .json({ error: "selectedJobs must be an array of indices" });
    }

    const feedback = {
      selected_role_indices: selectedJobs,
      preferred_industries: preferences?.preferredIndustries
        ? preferences.preferredIndustries.split(",").map((s) => s.trim())
        : [],
      preferred_locations: preferences?.preferredLocations
        ? preferences.preferredLocations.split(",").map((s) => s.trim())
        : [],
      remote_preference: preferences?.remotePreference || null,
      salary_expectation: preferences?.salaryExpectation || null,
      additional_notes: preferences?.additionalNotes || "",
      search_scope: preferences?.searchScope || "global",
      selected_regions: preferences?.selectedRegions || [],
      company_preferences: preferences?.companyPreferences || "",
    };

    continuePipelineWithFeedback(sessionId, feedback);

    res.json({
      status: "running",
      message: "Feedback received — refining search...",
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

/**
 * POST /api/feedback/:sessionId/checklist/:jobIndex
 * Toggle the application checklist for a specific job.
 */
router.post("/:sessionId/checklist/:jobIndex", (req, res) => {
  try {
    const { sessionId, jobIndex } = req.params;
    const checklist = toggleChecklist(sessionId, parseInt(jobIndex, 10));
    res.json({ checklist });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

export default router;
