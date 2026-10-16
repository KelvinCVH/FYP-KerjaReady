import { useCallback, useEffect, useState } from "react";
import { ApiError, getApiErrorMessage } from "@/lib/apiClient";

export type ApiDataState<T> =
  | { status: "loading" }
  // httpStatus is 0 when the request did not reach the API
  | { status: "error"; httpStatus: number; message: string }
  | { status: "ready"; data: T };

// Runs load once on mount. retry() shows the loading state and runs it again; setData updates loaded data
// in place, such as after a save. load must keep the same identity between renders (define it outside the component).
export function useApiData<T>(load: () => Promise<T>) {
  const [state, setState] = useState<ApiDataState<T>>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    load().then(
      (data) => {
        if (active) setState({ status: "ready", data });
      },
      (error: unknown) => {
        if (!active) return;
        const httpStatus = error instanceof ApiError ? error.status : 0;
        setState({ status: "error", httpStatus, message: getApiErrorMessage(error) });
      },
    );
    return () => {
      active = false;
    };
  }, [load, attempt]);

  const retry = useCallback(() => {
    setState({ status: "loading" });
    setAttempt((count) => count + 1);
  }, []);

  const setData = useCallback((update: (data: T) => T) => {
    setState((current) => (current.status === "ready" ? { status: "ready", data: update(current.data) } : current));
  }, []);

  return { state, retry, setData };
}
