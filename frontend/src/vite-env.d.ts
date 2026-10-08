/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Backend base URL (no trailing slash). Empty = same origin. */
  readonly VITE_API_BASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
