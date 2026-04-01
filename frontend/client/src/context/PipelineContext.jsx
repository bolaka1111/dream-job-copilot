import React, { createContext, useContext, useReducer, useEffect } from "react";

const initialState = {
  sessionId: null,
  currentStage: 0,
  status: "idle", // idle | running | paused | completed | error
  resumeProfile: null,
  jobResults: [],
  recommendations: [],
  selectedJobs: [],
  preferences: {
    searchScope: "global",
    selectedRegions: [],
    preferredIndustries: "",
    preferredLocations: "",
    remotePreference: "",
    salaryExpectation: "",
    companyPreferences: "",
    additionalNotes: "",
  },
  refinedJobs: [],
  reviews: [],
  bestJobs: [],
  reviewedJobs: [],
  enhancedResumes: [],
  coverLetters: [],
  applications: [],
  applicationChecklist: [],
  errors: [],
  logMessages: [],
};

function reducer(state, action) {
  switch (action.type) {
    case "SET_SESSION":
      return { ...state, sessionId: action.sessionId, status: "running" };
    case "SET_STAGE":
      return { ...state, currentStage: action.stage, status: action.status || state.status };
    case "SET_STATUS":
      return { ...state, status: action.status };
    case "SET_RESUME_PROFILE":
      return { ...state, resumeProfile: action.profile };
    case "SET_JOB_RESULTS":
      return { ...state, jobResults: action.jobs };
    case "SET_RECOMMENDATIONS":
      return { ...state, recommendations: action.recs };
    case "SET_SELECTED_JOBS":
      return { ...state, selectedJobs: action.indices };
    case "SET_PREFERENCES":
      return { ...state, preferences: { ...state.preferences, ...action.prefs } };
    case "SET_REFINED_JOBS":
      return { ...state, refinedJobs: action.jobs };
    case "SET_REVIEWS":
      return { ...state, reviews: action.reviews };
    case "SET_REVIEWED_JOBS":
      return { ...state, reviewedJobs: action.reviewedJobs };
    case "SET_BEST_JOBS":
      return { ...state, bestJobs: action.jobs };
    case "SET_ENHANCED_RESUMES":
      return { ...state, enhancedResumes: action.resumes };
    case "SET_COVER_LETTERS":
      return { ...state, coverLetters: action.letters };
    case "UPDATE_COVER_LETTER":
      return {
        ...state,
        coverLetters: state.coverLetters.map((l, i) =>
          i === action.index ? action.letter : l
        ),
      };
    case "SET_APPLICATIONS":
      return { ...state, applications: action.apps };
    case "TOGGLE_CHECKLIST": {
      const apps = [...state.applications];
      const app = { ...(apps[action.index] || {}), checklist: { ...(apps[action.index]?.checklist || {}) } };
      app.checklist[action.key] = !app.checklist[action.key];
      apps[action.index] = app;
      return { ...state, applications: apps };
    }
    case "ADD_ERROR":
      return { ...state, errors: [...state.errors, action.error] };
    case "ADD_LOG":
      return {
        ...state,
        logMessages: [...state.logMessages.slice(-50), action.message],
      };
    case "RESET":
      return { ...initialState };
    default:
      return state;
  }
}

const PipelineContext = createContext(null);

export function PipelineProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState, () => {
    // Restore from sessionStorage if available
    try {
      const saved = sessionStorage.getItem("pipeline_state");
      if (saved) {
        const parsed = JSON.parse(saved);
        return { ...initialState, ...parsed };
      }
    } catch {
      /* ignore */
    }
    return initialState;
  });

  // Persist to sessionStorage on state changes
  useEffect(() => {
    try {
      const { logMessages, ...toSave } = state;
      sessionStorage.setItem("pipeline_state", JSON.stringify(toSave));
    } catch {
      /* ignore */
    }
  }, [state]);

  return (
    <PipelineContext.Provider value={{ state, dispatch }}>
      {children}
    </PipelineContext.Provider>
  );
}

export function usePipelineContext() {
  const ctx = useContext(PipelineContext);
  if (!ctx) throw new Error("usePipelineContext must be used within PipelineProvider");
  return ctx;
}
