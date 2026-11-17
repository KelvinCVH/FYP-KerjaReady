import { useEffect, useEffectEvent, useRef, useState } from "react";
import { ApiError, getApiErrorMessage } from "@/lib/apiClient";
import {
  getResumeStatus,
  isFinalStatus,
  retryResumeAssessment,
  type AssessmentState,
  type AssessmentStatus,
} from "@/lib/resumeApi";

const POLL_MS = 3000;

// A 4xx (403, 404) won't fix itself, so checking stops. Network errors (0) and 5xx are retried on the next check.
function isPermanent(error: unknown) {
  return error instanceof ApiError && error.status >= 400 && error.status < 500;
}

// Checks one resume's assessment every 3 seconds until it is done, failed or timed out.
// onDone runs once when the status becomes done. onStatusChange runs each time the status moves on, including
// after Try Again. The caller remounts the hook (key) for another resume.
export function useAssessmentStatus(
  resumeId: number,
  initial: AssessmentState,
  onDone: () => void,
  onStatusChange?: (status: AssessmentStatus) => void,
) {
  const [state, setState] = useState(initial);
  // The status onStatusChange last saw. A ref, so StrictMode's second effect run doesn't report it twice.
  const reportedRef = useRef(initial.status);
  const [polling, setPolling] = useState(!isFinalStatus(initial.status));
  // Bumped to restart checking after Retry. Checking then starts straight away, not after 3 seconds.
  const [round, setRound] = useState(0);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);
  const [retryError, setRetryError] = useState<string | null>(null);
  // Set while Retry runs, so a double click can't send two requests
  const retryingRef = useRef(false);

  const notifyDone = useEffectEvent(onDone);
  const notifyChange = useEffectEvent((status: AssessmentStatus) => onStatusChange?.(status));

  useEffect(() => {
    if (reportedRef.current === state.status) return;
    reportedRef.current = state.status;
    notifyChange(state.status);
  }, [state.status]);

  useEffect(() => {
    if (!polling) return;
    let active = true;
    let timer: number | undefined;

    async function check() {
      try {
        const next = await getResumeStatus(resumeId);
        if (!active) return;
        setState(next);
        if (isFinalStatus(next.status)) {
          setPolling(false);
          if (next.status === "done") notifyDone();
          return;
        }
      } catch (error) {
        if (!active) return;
        if (isPermanent(error)) {
          setLoadError(getApiErrorMessage(error));
          setPolling(false);
          return;
        }
      }
      timer = window.setTimeout(check, POLL_MS);
    }

    timer = window.setTimeout(check, round === 0 ? POLL_MS : 0);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [resumeId, polling, round]);

  function restartPolling() {
    setPolling(true);
    setRound((count) => count + 1);
  }

  async function retry() {
    if (retryingRef.current) return;
    retryingRef.current = true;
    setRetrying(true);
    setRetryError(null);
    try {
      setState(await retryResumeAssessment(resumeId));
      restartPolling();
    } catch (error) {
      // 409: another tab or click already restarted it, so check where it is now
      if (error instanceof ApiError && error.status === 409) restartPolling();
      else setRetryError(getApiErrorMessage(error));
    } finally {
      retryingRef.current = false;
      setRetrying(false);
    }
  }

  return { status: state.status, failureReason: state.failure_reason, loadError, retry, retrying, retryError };
}
