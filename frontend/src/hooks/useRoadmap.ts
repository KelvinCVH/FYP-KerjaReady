import { useCallback, useEffect, useEffectEvent, useRef, useState } from "react";
import { ApiError, getApiErrorMessage } from "@/lib/apiClient";
import { getRoadmap, startRoadmap, type RoadmapResponse } from "@/lib/roadmapApi";

const POLL_MS = 3000;
// A backup for a run that never finishes. The API already reports a run that has been running for over 6 minutes as
// failed, and its POST then starts a new one.
const RUN_TIMEOUT_MS = 6 * 60 * 1000;

export type RoadmapLoad =
  | { status: "loading" }
  // httpStatus is 0 when the request did not reach the API
  | { status: "error"; httpStatus: number; message: string }
  | { status: "ready"; data: RoadmapResponse };

// What the page shows once the roadmap has loaded
export type RoadmapPhase = "no-resume" | "no-role" | "writing" | "failed" | "done";

// "start": the first run, or Try Again after a failed one. "regenerate": a new run while a roadmap is shown.
export type StartKind = "start" | "regenerate";

export type StartError = { message: string; kind: StartKind };

// A 4xx won't fix itself, so checking stops. Network errors (0) and 5xx are retried on the next check.
function isPermanent(error: unknown) {
  return error instanceof ApiError && error.status >= 400 && error.status < 500;
}

function getPhase(data: RoadmapResponse, timedOutRunId: number | null, startError: StartError | null): RoadmapPhase {
  if (!data.resume) return "no-resume";
  if (!data.target_role) return "no-role";
  const { run } = data;
  // No run yet: it is starting on its own, unless that start failed
  if (!run) return startError ? "failed" : "writing";
  if (run.status === "running") return run.run_id === timedOutRunId ? "failed" : "writing";
  if (run.status === "failed") return "failed";
  return data.roadmap ? "done" : "failed";
}

// The candidate's learning roadmap (KR-98). Loads it once, starts the first run on its own when there has never been
// one, and checks a running run every 3 seconds until it is done or failed. start() is Try Again and Regenerate.
export function useRoadmap() {
  const [load, setLoad] = useState<RoadmapLoad>({ status: "loading" });
  // Bumped by reload() to load again with the loading state
  const [attempt, setAttempt] = useState(0);
  // The running run this page gave up waiting for, so it shows as failed
  const [timedOutRunId, setTimedOutRunId] = useState<number | null>(null);
  const [startError, setStartError] = useState<StartError | null>(null);
  const [starting, setStarting] = useState(false);
  // Set while a POST runs, so a double click can't send two
  const startingRef = useRef(false);
  // Set once the first run has been started on its own. A ref, so StrictMode's second effect run doesn't send a
  // second POST.
  const autoStartedRef = useRef(false);

  useEffect(() => {
    // A newer load clears this, so a slower earlier answer can't overwrite a newer one
    let active = true;
    getRoadmap().then(
      (data) => {
        if (active) setLoad({ status: "ready", data });
      },
      (error: unknown) => {
        if (!active) return;
        const httpStatus = error instanceof ApiError ? error.status : 0;
        setLoad({ status: "error", httpStatus, message: getApiErrorMessage(error) });
      },
    );
    return () => {
      active = false;
    };
  }, [attempt]);

  const reload = useCallback(() => {
    setLoad({ status: "loading" });
    setAttempt((count) => count + 1);
  }, []);

  const data = load.status === "ready" ? load.data : null;
  const phase = data ? getPhase(data, timedOutRunId, startError) : null;

  // Quiet checks while a run is running. The effect restarts for each new run.
  const runningId =
    data?.run?.status === "running" && data.run.run_id !== timedOutRunId ? data.run.run_id : null;

  useEffect(() => {
    if (runningId === null) return;
    let active = true;
    let timer: number | undefined;

    async function check() {
      try {
        const next = await getRoadmap();
        if (!active) return;
        setLoad({ status: "ready", data: next });
        // Done, failed or another run: this effect's job is over (another running run restarts it)
        if (next.run?.status !== "running" || next.run.run_id !== runningId) return;
      } catch (error) {
        if (!active) return;
        if (isPermanent(error)) {
          const httpStatus = error instanceof ApiError ? error.status : 0;
          setLoad({ status: "error", httpStatus, message: getApiErrorMessage(error) });
          return;
        }
      }
      timer = window.setTimeout(check, POLL_MS);
    }

    timer = window.setTimeout(check, POLL_MS);
    const timeout = window.setTimeout(() => setTimedOutRunId(runningId), RUN_TIMEOUT_MS);
    return () => {
      active = false;
      window.clearTimeout(timer);
      window.clearTimeout(timeout);
    };
  }, [runningId]);

  // Starts a run. Returns true when it started, so the caller can move focus to the writing state.
  async function start(kind: StartKind) {
    if (startingRef.current) return false;
    startingRef.current = true;
    setStarting(true);
    try {
      const run = await startRoadmap();
      // Cleared only now: with no run yet, clearing it earlier would show the writing state while the POST runs
      setStartError(null);
      setTimedOutRunId(null);
      if (run.status === "running") {
        // The old roadmap goes, so the writing state shows until the new one is done
        setLoad((current) =>
          current.status === "ready" ? { status: "ready", data: { ...current.data, run, roadmap: null } } : current,
        );
      } else {
        // Not expected from the API, but load it rather than show a roadmap from another run
        reload();
      }
      return true;
    } catch (error) {
      setStartError({ message: getApiErrorMessage(error), kind });
      // 409: no assessed resume or no target role any more, so load again to show why
      if (error instanceof ApiError && error.status === 409) reload();
      return false;
    } finally {
      startingRef.current = false;
      setStarting(false);
    }
  }

  // The first visit for this resume and role: start writing straight away
  const needsFirstRun = data !== null && data.resume !== null && data.target_role !== null && data.run === null;
  const startFirstRun = useEffectEvent(() => {
    void start("start");
  });

  useEffect(() => {
    if (!needsFirstRun || autoStartedRef.current) return;
    autoStartedRef.current = true;
    startFirstRun();
  }, [needsFirstRun]);

  return { load, data, phase, start, starting, startError, reload };
}
