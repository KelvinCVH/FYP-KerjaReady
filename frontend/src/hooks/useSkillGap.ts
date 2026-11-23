import { useCallback, useEffect, useState } from "react";
import { ApiError, getApiErrorMessage } from "@/lib/apiClient";
import { getSkillGap, type SkillGap, type SkillGapRole } from "@/lib/skillGapApi";

// Every state names the resume it belongs to, so a result is never shown for another resume
export type SkillGapState =
  // No resume to compare yet
  | { status: "idle" }
  | { status: "loading"; resumeId: number }
  | { status: "ready"; resumeId: number; data: SkillGap }
  // httpStatus is 0 when the request did not reach the API
  | { status: "error"; resumeId: number; httpStatus: number; message: string };

// Loads the skill gap for the selected resume, again whenever the selection changes.
// state is always about resumeId: until its own answer arrives it is "loading", even if another resume's result is
// held. lastRole is the target role from the newest result for any resume, so the page can keep showing the role
// while a switch loads; nothing else from an earlier result may be shown.
export function useSkillGap(resumeId: number | null) {
  // The newest settled answer, or "loading" after Try Again, for whichever resume it was about
  const [latest, setLatest] = useState<SkillGapState>({ status: "idle" });
  const [lastRole, setLastRole] = useState<SkillGapRole | null>(null);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    if (resumeId === null) return;
    // Cleared when the selection changes, so a slower answer for the previous resume is dropped
    let active = true;
    getSkillGap(resumeId).then(
      (data) => {
        if (!active) return;
        setLatest({ status: "ready", resumeId, data });
        setLastRole(data.target_role);
      },
      (error: unknown) => {
        if (!active) return;
        const httpStatus = error instanceof ApiError ? error.status : 0;
        setLatest({ status: "error", resumeId, httpStatus, message: getApiErrorMessage(error) });
      },
    );
    return () => {
      active = false;
    };
  }, [resumeId, attempt]);

  const retry = useCallback(() => {
    if (resumeId === null) return;
    setLatest({ status: "loading", resumeId });
    setAttempt((count) => count + 1);
  }, [resumeId]);

  let state: SkillGapState;
  if (resumeId === null) state = { status: "idle" };
  else if (latest.status !== "idle" && latest.resumeId === resumeId) state = latest;
  else state = { status: "loading", resumeId };

  return { state, lastRole, retry };
}
