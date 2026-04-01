/**
 * usePipeline — high-level hook for pipeline actions.
 */
import { useCallback } from "react";
import { usePipelineContext } from "../context/PipelineContext";
import { api } from "../api/client";
import toast from "react-hot-toast";

export function usePipeline() {
  const { state, dispatch } = usePipelineContext();

  const startPipeline = useCallback(
    async (file, options = {}) => {
      try {
        dispatch({ type: "SET_STATUS", status: "running" });
        const formData = new FormData();
        formData.append("resume", file);
        if (options.dreamRole) formData.append("dreamRole", options.dreamRole);
        if (options.searchScope) formData.append("searchScope", options.searchScope);

        // Do NOT set Content-Type manually — Axios auto-sets multipart/form-data
        // with the correct boundary when it detects a FormData body.
        const res = await api.post("/api/pipeline/start", formData);

        dispatch({ type: "SET_SESSION", sessionId: res.data.sessionId });
        toast.success("We're analysing your resume — hang tight!");
        return res.data.sessionId;
      } catch (err) {
        dispatch({ type: "ADD_ERROR", error: err.message });
        dispatch({ type: "SET_STATUS", status: "error" });
        toast.error("Something went sideways — please try again");
        throw err;
      }
    },
    [dispatch]
  );

  const submitFeedback = useCallback(
    async (preferences) => {
      try {
        dispatch({ type: "SET_STATUS", status: "running" });
        dispatch({ type: "SET_PREFERENCES", prefs: preferences });

        await api.post(`/api/feedback/${state.sessionId}`, {
          selectedJobs: state.selectedJobs,
          preferences,
        });

        toast.success("Preferences received — refining your search!");
      } catch (err) {
        dispatch({ type: "ADD_ERROR", error: err.message });
        toast.error("Something went sideways — let's retry");
        throw err;
      }
    },
    [state.sessionId, dispatch]
  );

  const triggerApply = useCallback(async () => {
    try {
      dispatch({ type: "SET_STATUS", status: "running" });
      await api.post(`/api/cover-letter/apply/${state.sessionId}`);
      toast.success("Generating your tailored materials...");
    } catch (err) {
      dispatch({ type: "ADD_ERROR", error: err.message });
      toast.error("Something went sideways — let's retry");
      throw err;
    }
  }, [state.sessionId, dispatch]);

  const regenerateCoverLetter = useCallback(
    async (jobIndex, options = {}) => {
      try {
        const res = await api.post(
          `/api/cover-letter/${state.sessionId}/${jobIndex}/regenerate`,
          { tone: options.tone, length: options.length }
        );
        dispatch({
          type: "UPDATE_COVER_LETTER",
          index: jobIndex,
          letter: res.data.coverLetter,
        });
        toast.success("Cover letter regenerated!");
        return res.data.coverLetter;
      } catch (err) {
        toast.error("Couldn't regenerate — let's try again");
        throw err;
      }
    },
    [state.sessionId, dispatch]
  );

  const toggleChecklist = useCallback(
    async (jobIndex, itemKey) => {
      dispatch({ type: "TOGGLE_CHECKLIST", index: jobIndex, key: itemKey });
      try {
        await api.post(`/api/feedback/${state.sessionId}/checklist/${jobIndex}`, { key: itemKey });
      } catch {
        /* best-effort sync */
      }
    },
    [state.sessionId, dispatch]
  );

  const fetchResult = useCallback(async () => {
    if (!state.sessionId) return;
    try {
      const res = await api.get(`/api/pipeline/result/${state.sessionId}`);
      const d = res.data;
      if (d.state?.resumeProfile) dispatch({ type: "SET_RESUME_PROFILE", profile: d.state.resumeProfile });
      if (d.state?.jobResults) dispatch({ type: "SET_JOB_RESULTS", jobs: d.state.jobResults });
      if (d.state?.recommendations) dispatch({ type: "SET_RECOMMENDATIONS", recs: d.state.recommendations });
      if (d.state?.bestJobs) dispatch({ type: "SET_BEST_JOBS", jobs: d.state.bestJobs });
      if (d.state?.enhancedResumes) dispatch({ type: "SET_ENHANCED_RESUMES", resumes: d.state.enhancedResumes });
      if (d.state?.applications) dispatch({ type: "SET_APPLICATIONS", apps: d.state.applications });
      if (d.coverLetters) dispatch({ type: "SET_COVER_LETTERS", letters: d.coverLetters });
    } catch {
      /* ignore */
    }
  }, [state.sessionId, dispatch]);

  const reset = useCallback(() => {
    dispatch({ type: "RESET" });
    sessionStorage.removeItem("pipeline_state");
    toast("Starting fresh — let's find your dream job!", { icon: "🚀" });
  }, [dispatch]);

  return {
    state,
    dispatch,
    startPipeline,
    submitFeedback,
    triggerApply,
    regenerateCoverLetter,
    toggleChecklist,
    fetchResult,
    reset,
  };
}
