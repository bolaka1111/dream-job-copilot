/**
 * SSE Hook — subscribes to pipeline progress events.
 * Reconnects with exponential backoff (max 3 retries) per guardrails §10.
 */
import { useEffect, useRef, useCallback } from "react";
import toast from "react-hot-toast";
import { usePipelineContext } from "../context/PipelineContext";

export function useSSE() {
  const { state, dispatch } = usePipelineContext();
  const eventSourceRef = useRef(null);
  const retriesRef = useRef(0);
  const maxRetries = 3;

  const connect = useCallback(() => {
    if (!state.sessionId) return;
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const es = new EventSource(`/api/pipeline/status/${state.sessionId}`);
    eventSourceRef.current = es;

    es.addEventListener("connected", (e) => {
      retriesRef.current = 0;
    });

    es.addEventListener("stage_update", (e) => {
      try {
        const data = JSON.parse(e.data);
        dispatch({ type: "SET_STAGE", stage: data.stage, status: data.status === "error" ? "error" : "running" });

        if (data.result) {
          // Route result data to the correct state slice
          if (data.result.resumeProfile) {
            dispatch({ type: "SET_RESUME_PROFILE", profile: data.result.resumeProfile });
          }
          if (data.result.jobResults) {
            dispatch({ type: "SET_JOB_RESULTS", jobs: data.result.jobResults });
          }
          if (data.result.recommendations) {
            dispatch({ type: "SET_RECOMMENDATIONS", recs: data.result.recommendations });
          }
          if (data.result.refinedJobs) {
            dispatch({ type: "SET_REFINED_JOBS", jobs: data.result.refinedJobs });
          }
          if (data.result.reviews) {
            dispatch({ type: "SET_REVIEWS", reviews: data.result.reviews });
          }
          if (data.result.reviewedJobs) {
            dispatch({ type: "SET_REVIEWED_JOBS", reviewedJobs: data.result.reviewedJobs });
          }
          if (data.result.bestJobs) {
            dispatch({ type: "SET_BEST_JOBS", jobs: data.result.bestJobs });
          }
          if (data.result.enhancedResumes) {
            dispatch({ type: "SET_ENHANCED_RESUMES", resumes: data.result.enhancedResumes });
          }
          if (data.result.applications) {
            dispatch({ type: "SET_APPLICATIONS", apps: data.result.applications });
          }
        }

        if (data.status === "error") {
          dispatch({ type: "SET_STATUS", status: "error" });
          toast.error(data.message || "Something went wrong in the pipeline — please retry");
        }

        if (data.status === "completed" && data.stageName === "complete") {
          dispatch({ type: "SET_STATUS", status: "completed" });
        }

        // Add as log message for the live log strip
        if (data.message) {
          dispatch({ type: "ADD_LOG", message: data.message });
        }
      } catch {
        /* ignore parse errors */
      }
    });

    es.addEventListener("log", (e) => {
      try {
        const data = JSON.parse(e.data);
        dispatch({ type: "ADD_LOG", message: data.message });
      } catch {
        /* ignore */
      }
    });

    es.onerror = () => {
      es.close();
      if (retriesRef.current < maxRetries) {
        retriesRef.current += 1;
        const delay = Math.min(1000 * Math.pow(2, retriesRef.current), 8000);
        setTimeout(connect, delay);
      }
    };
  }, [state.sessionId, dispatch]);

  useEffect(() => {
    connect();
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [connect]);
}
