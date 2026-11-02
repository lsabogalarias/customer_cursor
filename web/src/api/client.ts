/** JSON client for the API gateway. */

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;

  /**
   * Build an error the screens can show.
   *
   * @param message - English explanation.
   * @param status - HTTP status.
   * @param code - Machine-readable error code.
   */
  constructor(message: string, status: number, code: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

interface ErrorBody {
  error?: string;
  message?: string;
  detail?: { error?: string; message?: string } | string;
}

/**
 * Call the gateway and parse a JSON body.
 *
 * @param path - Path beginning with /api.
 * @param init - Fetch options. JSON bodies should already be strings.
 * @param token - Bearer token, when the route is protected.
 * @returns The parsed JSON value.
 */
export async function apiRequest<T>(path: string, init: RequestInit = {}, token?: string | null): Promise<T> {
  const headers = new Headers(init.headers);
  if (init.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const response = await fetch(path, { ...init, headers });
  if (response.status === 204) {
    return undefined as T;
  }
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    throw toApiError(payload, response.status);
  }
  return payload as T;
}

/**
 * Download a document and trigger a browser save.
 *
 * @param documentId - Document identifier.
 * @param fileName - Suggested file name.
 * @param token - Bearer token.
 */
export async function downloadDocument(documentId: string, fileName: string, token: string): Promise<void> {
  const response = await fetch(`/api/documents/${documentId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    const payload: unknown = await response.json().catch(() => null);
    throw toApiError(payload, response.status);
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  anchor.click();
  URL.revokeObjectURL(url);
}

/**
 * Convert an error payload into ApiError.
 *
 * @param payload - Parsed JSON, or null.
 * @param status - HTTP status.
 * @returns An ApiError with an English message.
 */
function toApiError(payload: unknown, status: number): ApiError {
  if (payload && typeof payload === "object") {
    const body = payload as ErrorBody;
    if (typeof body.message === "string") {
      return new ApiError(body.message, status, body.error ?? "request_failed");
    }
    if (body.detail && typeof body.detail === "object" && typeof body.detail.message === "string") {
      return new ApiError(body.detail.message, status, body.detail.error ?? "request_failed");
    }
  }
  return new ApiError("The request could not be completed.", status, "request_failed");
}
