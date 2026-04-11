/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  /** Set to `session` to store JWT in sessionStorage (sign-in again after closing the browser). */
  readonly VITE_AUTH_STORAGE?: string
  /** Injected by deploy scripts; shown in sidebar to confirm which build is live. */
  readonly VITE_APP_BUILD?: string
  readonly VITE_OIDC_ISSUER: string
  readonly VITE_OIDC_CLIENT_ID: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

