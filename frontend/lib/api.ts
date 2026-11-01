/**
 * Typed client for the jintru FastAPI gateway.
 *
 * Types mirror backend/app/api/schemas.py field-for-field. This module is the only
 * place the UI is allowed to talk to /api/v1.
 */

export type PublicVerdict =
  | 'supported'
  | 'contradicted'
  | 'mixed'
  | 'insufficient_evidence'
  | 'not_verifiable'

export type SourceStance = 'supports' | 'refutes' | 'neutral'

export type Relevance = 'direct' | 'indirect' | 'contextual' | 'irrelevant'

export interface SourceItem {
  source_id: string
  url: string
  domain: string
  title: string
  snippet: string
  stance: SourceStance
  source_family_id: string
  retrieved_at: string
  published_at: string | null
  source_type: 'search_snippet' | 'llm_context'
  content_hash: string
  extraction_status: 'ok' | 'truncated' | 'empty'
  is_quarantined: boolean
  relevance: Relevance | null
  exact_quote: string | null
}

export interface ReasoningStatement {
  statement: string
  citation_ids: string[]
  quoted_excerpt: string | null
}

export interface VerificationResponse {
  id: string
  claim: string
  public_verdict: PublicVerdict
  summary: string
  limitations: string[]
  sources: SourceItem[]
  reasoning: ReasoningStatement[]
  created_at: string
}

export interface VerificationListItem {
  id: string
  claim: string
  public_verdict: PublicVerdict
  created_at: string
}

export interface PaginatedVerificationResponse {
  items: VerificationListItem[]
  total: number
}

export interface HealthResponse {
  status: string
  providers: Record<string, string>
}

export interface ErrorEnvelope {
  error: string
  code: string
  detail: string | null
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly detail: string | null

  constructor(status: number, code: string, message: string, detail: string | null = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.detail = detail
  }
}

export function isApiError(value: unknown): value is ApiError {
  return value instanceof ApiError
}

/**
 * Same-origin by default so the Next.js rewrite (next.config.mjs) proxies to the
 * backend; set NEXT_PUBLIC_API_BASE_URL to an absolute origin only when the browser
 * must reach the API directly.
 */
const API_BASE = (process.env.NEXT_PUBLIC_API_BASE_URL ?? '/api/v1').replace(/\/$/, '')

/**
 * Backstop against a hung socket. The backend's own budget is 8.0s, so this must
 * stay comfortably above it and never substitute for the server-side SLA.
 */
const CLIENT_TIMEOUT_MS = 12_000

type RequestOptions = {
  method?: string
  body?: string
}

function toQuery(params: Record<string, string | number | undefined>): string {
  const pairs = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== '')
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
  return pairs.length ? `?${pairs.join('&')}` : ''
}

async function toApiError(response: Response): Promise<ApiError> {
  let envelope: Partial<ErrorEnvelope> | null = null
  try {
    envelope = (await response.json()) as Partial<ErrorEnvelope>
  } catch {
    envelope = null
  }
  const code = envelope?.code ?? `HTTP_${response.status}`
  const message = envelope?.error ?? (response.statusText || 'The request failed.')
  return new ApiError(response.status, code, message, envelope?.detail ?? null)
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), CLIENT_TIMEOUT_MS)
  let response: Response

  try {
    response = await fetch(`${API_BASE}${path}`, {
      method: options.method ?? 'GET',
      body: options.body,
      headers: {
        Accept: 'application/json',
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      },
      signal: controller.signal,
      cache: 'no-store',
    })
  } catch {
    if (controller.signal.aborted) {
      throw new ApiError(
        0,
        'CLIENT_TIMEOUT',
        'The request exceeded the client timeout before the backend responded.',
      )
    }
    throw new ApiError(0, 'NETWORK_ERROR', 'The verification backend could not be reached.')
  } finally {
    clearTimeout(timer)
  }

  if (response.status === 204) {
    return undefined as unknown as T
  }
  if (!response.ok) {
    throw await toApiError(response)
  }
  return (await response.json()) as T
}

export function createVerification(claim: string): Promise<VerificationResponse> {
  return request<VerificationResponse>('/verifications', {
    method: 'POST',
    body: JSON.stringify({ claim }),
  })
}

export function listVerifications(params: {
  limit?: number
  offset?: number
  verdict?: PublicVerdict
} = {}): Promise<PaginatedVerificationResponse> {
  return request<PaginatedVerificationResponse>(`/verifications${toQuery(params)}`)
}

export function getVerification(id: string): Promise<VerificationResponse> {
  return request<VerificationResponse>(`/verifications/${encodeURIComponent(id)}`)
}

export function deleteVerification(id: string): Promise<void> {
  return request<void>(`/verifications/${encodeURIComponent(id)}`, { method: 'DELETE' })
}

export function purgeVerifications(): Promise<void> {
  return request<void>('/verifications', { method: 'DELETE' })
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health')
}
