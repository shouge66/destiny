const KEY = "gift_tracker_auth";
const ASSESSMENT_DRAFT_KEY = "gift_tracker_assessment_draft";

export const state = {
  auth: loadAuth(),
  assessmentDraft: loadAssessmentDraft(),
  latestAssessmentId: null,
  activeProfile: null,
  flowContext: {
    scenario: null,
    dimensionScores: null,
    mysticReport: null,
  },
  correctedProfile: null,
};

export function setAuth(auth) {
  state.auth = auth;
  localStorage.setItem(KEY, JSON.stringify(auth));
}

export function clearAuth() {
  state.auth = null;
  localStorage.removeItem(KEY);
  clearAssessmentDraft();
}

export function setAssessmentDraft(draft) {
  state.assessmentDraft = draft || null;
  if (!draft) {
    localStorage.removeItem(ASSESSMENT_DRAFT_KEY);
    return;
  }
  localStorage.setItem(ASSESSMENT_DRAFT_KEY, JSON.stringify(draft));
}

export function clearAssessmentDraft() {
  state.assessmentDraft = null;
  localStorage.removeItem(ASSESSMENT_DRAFT_KEY);
}

function loadAuth() {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function loadAssessmentDraft() {
  try {
    const raw = localStorage.getItem(ASSESSMENT_DRAFT_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}
