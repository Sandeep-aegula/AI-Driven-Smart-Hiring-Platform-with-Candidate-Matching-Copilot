/**
 * Shared constants for HirePilot frontend.
 * This file contains constants that are shared between frontend and backend
 * to ensure consistency and avoid duplication.
 */

// Valid application statuses that can be shortlisted
// These are the statuses where an application is "awaiting HR review"
export const SHORTLISTABLE_APPLICATION_STATUSES = [
  "submitted",
  "parsed",
  "under_review",
  "applied",
];

// Candidate statuses that correspond to shortlistable application statuses
// These are the candidate statuses that can be shortlisted
export const SHORTLISTABLE_CANDIDATE_STATUSES = [
  "Applied",
  "Under Review",
  "submitted",
  "parsed",
  "under_review",
  "applied",
];

// Application statuses that are considered "final" (cannot be shortlisted)
export const FINAL_APPLICATION_STATUSES = [
  "shortlisted",
  "hired",
  "rejected",
  "withdrawn",
];

// Candidate statuses that are considered "final" (cannot be shortlisted)
export const FINAL_CANDIDATE_STATUSES = [
  "Shortlisted",
  "Hired",
  "Rejected",
  "Interview Scheduled",
  "Interviewed",
];

// All possible application statuses
export const ALL_APPLICATION_STATUSES = [
  "submitted",
  "parsed",
  "under_review",
  "applied",
  "shortlisted",
  "hired",
  "rejected",
  "withdrawn",
];

// All possible candidate statuses
export const ALL_CANDIDATE_STATUSES = [
  "New",
  "Applied",
  "Under Review",
  "Shortlisted",
  "Interview Scheduled",
  "Interviewed",
  "Hired",
  "Rejected",
];

// Status display names for UI
export const APPLICATION_STATUS_DISPLAY = {
  "submitted": "Submitted",
  "parsed": "Parsed",
  "under_review": "Under Review",
  "applied": "Applied",
  "shortlisted": "Shortlisted",
  "hired": "Hired",
  "rejected": "Rejected",
  "withdrawn": "Withdrawn",
};

export const CANDIDATE_STATUS_DISPLAY = {
  "New": "New",
  "Applied": "Applied",
  "Under Review": "Under Review",
  "Shortlisted": "Shortlisted",
  "Interview Scheduled": "Interview Scheduled",
  "Interviewed": "Interviewed",
  "Hired": "Hired",
  "Rejected": "Rejected",
};

// Status colors for UI
export const STATUS_COLORS = {
  "submitted": "#3B82F6",
  "parsed": "#8B5CF6",
  "under_review": "#F59E0B",
  "applied": "#3B82F6",
  "shortlisted": "#10B981",
  "hired": "#10B981",
  "rejected": "#EF4444",
  "withdrawn": "#6B7280",
  "Applied": "#3B82F6",
  "Under Review": "#F59E0B",
  "Shortlisted": "#10B981",
  "Interview Scheduled": "#8B5CF6",
  "Interviewed": "#8B5CF6",
  "Hired": "#10B981",
  "Rejected": "#EF4444",
  "New": "#6B7280",
};

export function isShortlistableApplicationStatus(status: string): boolean {
  return SHORTLISTABLE_APPLICATION_STATUSES.includes(status);
}

export function isShortlistableCandidateStatus(status: string): boolean {
  return SHORTLISTABLE_CANDIDATE_STATUSES.includes(status);
}

export function isFinalApplicationStatus(status: string): boolean {
  return FINAL_APPLICATION_STATUSES.includes(status);
}

export function isFinalCandidateStatus(status: string): boolean {
  return FINAL_CANDIDATE_STATUSES.includes(status);
}