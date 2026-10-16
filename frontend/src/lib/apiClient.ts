import { fetchAuthSession, signOut } from "aws-amplify/auth";
import { GENERIC_ERROR_MESSAGE } from "./cognitoMessages";
import { saveSignInError } from "./signInNotice";

const SESSION_ENDED_MESSAGE = "Your session has ended. Sign in again.";
// Aurora Serverless can take a few seconds to wake up and answers 503 until then
const WAKE_UP_RETRY_MS = 3_000;

// A failed API call. status is the HTTP status, or 0 when the request did not reach the API.
export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

// The message to show for a failed API call: the API's own message, or the generic one
export function getApiErrorMessage(error: unknown) {
  return error instanceof ApiError ? error.message : GENERIC_ERROR_MESSAGE;
}

type Method = "GET" | "POST" | "PUT" | "DELETE";

async function getAccessToken() {
  try {
    const { tokens } = await fetchAuthSession();
    return tokens?.accessToken?.toString();
  } catch {
    return undefined;
  }
}

// The response body, or undefined when it is empty or not JSON
async function readBody(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return undefined;
  try {
    return JSON.parse(text);
  } catch {
    return undefined;
  }
}

function getMessage(body: unknown) {
  if (typeof body === "object" && body !== null) {
    const { message } = body as Record<string, unknown>;
    if (typeof message === "string" && message.trim()) return message;
  }
  return GENERIC_ERROR_MESSAGE;
}

// The session is gone or no longer accepted: sign out and reload Sign In, which shows why
async function endSession(): Promise<never> {
  saveSignInError(SESSION_ENDED_MESSAGE);
  try {
    await signOut();
  } catch {
    // Amplify clears the local session even when revoking the token fails
  }
  window.location.replace("/sign-in");
  throw new ApiError(401, SESSION_ENDED_MESSAGE);
}

async function send(method: Method, path: string, body: unknown, token: string) {
  const headers: Record<string, string> = { Authorization: `Bearer ${token}` };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  try {
    return await fetch(`${import.meta.env.VITE_API_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, GENERIC_ERROR_MESSAGE);
  }
}

async function request<T>(method: Method, path: string, body?: unknown): Promise<T> {
  for (let attempt = 1; ; attempt++) {
    const token = await getAccessToken();
    if (!token) return endSession();

    const response = await send(method, path, body, token);
    if (response.status === 401) return endSession();
    if (response.status === 503 && attempt === 1) {
      await new Promise((resolve) => window.setTimeout(resolve, WAKE_UP_RETRY_MS));
      continue;
    }

    const data = await readBody(response);
    if (!response.ok) throw new ApiError(response.status, getMessage(data));
    return data as T;
  }
}

// GET a protected API route with the signed-in user's access token, such as apiGet("/candidate/profile")
export function apiGet<T>(path: string) {
  return request<T>("GET", path);
}

// POST, PUT or DELETE a protected API route, sending body as JSON
export function apiSend<T>(method: Exclude<Method, "GET">, path: string, body?: unknown) {
  return request<T>(method, path, body);
}
