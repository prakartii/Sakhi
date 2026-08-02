import { supabase } from "@/lib/supabase-client";

const API_BASE_URL =
  (import.meta.env["VITE_API_BASE_URL"] as string | undefined) ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, message: string, body: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

async function authHeaders(): Promise<Record<string, string>> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

type QueryValue = string | number | boolean | undefined | null;
type QueryParams = Record<string, QueryValue>;

type RequestOptions = {
  query?: QueryParams | undefined;
  body?: unknown;
  signal?: AbortSignal | undefined;
};

function buildUrl(path: string, query: QueryParams | undefined): string {
  const url = new URL(`${API_BASE_URL}${path}`);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

async function request<T>(
  method: "GET" | "POST" | "PATCH" | "PUT" | "DELETE",
  path: string,
  options: RequestOptions,
): Promise<T> {
  const headers: Record<string, string> = {
    ...(await authHeaders()),
  };

  const init: RequestInit = { method, headers };
  if (options.body !== undefined) {
    headers["Content-Type"] = "application/json";
    init.body = JSON.stringify(options.body);
  }
  if (options.signal !== undefined) {
    init.signal = options.signal;
  }

  const response = await fetch(buildUrl(path, options.query), init);

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  const data: unknown = text ? JSON.parse(text) : undefined;

  if (!response.ok) {
    const message =
      (data && typeof data === "object" && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : undefined) ?? `Request failed with status ${response.status}`;
    throw new ApiError(response.status, message, data);
  }

  return data as T;
}

export interface VoiceMemoryOut {
  id: string;
  memory_type: string;
  title: string | null;
  content: string;
  importance_score: number;
  occurred_at: string | null;
}

export interface VoiceConverseResponse {
  voice_log_id: string;
  session_id: string;
  transcript: string;
  detected_language: string | null;
  sentiment: string;
  memories: VoiceMemoryOut[];
  answer: string;
  used_services: string[];
  sources: string[];
  audio_base64: string | null;
  audio_format: string;
}

/** Multipart upload — separate from `api.post` because that always
 * JSON-encodes the body; voice audio needs FormData instead. */
export async function postVoiceConverse(params: {
  businessProfileId: string;
  audio: Blob;
  language?: string | undefined;
  sessionId?: string | undefined;
}): Promise<VoiceConverseResponse> {
  const form = new FormData();
  form.append("business_profile_id", params.businessProfileId);
  form.append("language", params.language ?? "en-IN");
  if (params.sessionId) form.append("session_id", params.sessionId);
  form.append("audio", params.audio, "recording.webm");

  const headers = await authHeaders();
  const response = await fetch(`${API_BASE_URL}/voice/converse`, {
    method: "POST",
    headers,
    body: form,
  });

  const text = await response.text();
  const data: unknown = text ? JSON.parse(text) : undefined;
  if (!response.ok) {
    const message =
      (data && typeof data === "object" && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : undefined) ?? `Request failed with status ${response.status}`;
    throw new ApiError(response.status, message, data);
  }
  return data as VoiceConverseResponse;
}

export interface VoiceTranscribeResponse {
  transcript: string;
  detected_language: string | null;
  confidence: number | null;
}

/** STT-only upload — no business profile needed, used by Business Setup's
 * mic button to fill the story textarea before any profile exists. */
export async function postVoiceTranscribe(params: {
  audio: Blob;
  language?: string | undefined;
}): Promise<VoiceTranscribeResponse> {
  const form = new FormData();
  form.append("language", params.language ?? "en-IN");
  form.append("audio", params.audio, "recording.webm");

  const headers = await authHeaders();
  const response = await fetch(`${API_BASE_URL}/voice/transcribe`, {
    method: "POST",
    headers,
    body: form,
  });

  const text = await response.text();
  const data: unknown = text ? JSON.parse(text) : undefined;
  if (!response.ok) {
    const message =
      (data && typeof data === "object" && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : undefined) ?? `Request failed with status ${response.status}`;
    throw new ApiError(response.status, message, data);
  }
  return data as VoiceTranscribeResponse;
}

/** Multipart POST — same JSON-or-throw contract as `api.post`, but for
 * endpoints that take a FormData body (file uploads) instead of a JSON
 * one. See postVoiceConverse/postVoiceTranscribe above for the
 * hand-written version of this same shape; new multipart endpoints should
 * use this instead of duplicating it. */
async function postForm<T>(path: string, form: FormData): Promise<T> {
  const headers = await authHeaders();
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers,
    body: form,
  });

  const text = await response.text();
  const data: unknown = text ? JSON.parse(text) : undefined;
  if (!response.ok) {
    const message =
      (data && typeof data === "object" && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : undefined) ?? `Request failed with status ${response.status}`;
    throw new ApiError(response.status, message, data);
  }
  return data as T;
}

export const api = {
  get: <T>(path: string, query?: QueryParams, signal?: AbortSignal) =>
    request<T>("GET", path, { query, signal }),
  post: <T>(path: string, body?: unknown, query?: QueryParams) =>
    request<T>("POST", path, { body, query }),
  postForm: <T>(path: string, form: FormData) => postForm<T>(path, form),
  patch: <T>(path: string, body?: unknown, query?: QueryParams) =>
    request<T>("PATCH", path, { body, query }),
  put: <T>(path: string, body?: unknown, query?: QueryParams) =>
    request<T>("PUT", path, { body, query }),
  delete: <T>(path: string, query?: QueryParams) => request<T>("DELETE", path, { query }),
};
