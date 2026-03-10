export type AnonymizeOptions = {
  fio: boolean;
  passport: boolean;
  birthdate: boolean;
  snils_inn: boolean;
  phone: boolean;
  banking: boolean;
};

export type FileResult = {
  result_path: string;
  download_url: string;
  output_filename: string;
  preview_html: string;
  preview_text: string;
  warnings: string[];
};

export type BatchJobCreate = {
  job_id: string;
  status: string;
  total: number;
};

export type BatchItem = {
  filename: string;
  result: FileResult | null;
  error: string | null;
};

export type BatchStatus = {
  job_id: string;
  status: string;
  total: number;
  processed: number;
  progress: number;
  items: BatchItem[];
};

export type TextResponse = {
  anonymized_text: string;
  highlighted_html: string;
  result_path: string;
  warnings?: string[];
};

const API_BASE = (import.meta as any).env?.VITE_API_BASE_URL || "";
const DESKTOP_TOKEN = (import.meta as any).env?.VITE_DESKTOP_TOKEN || "";

function apiUrl(path: string) {
  if (!API_BASE) return path;
  return `${API_BASE.replace(/\/$/, "")}${path}`;
}

async function handleJson(res: Response) {
  const contentType = res.headers.get("content-type") || "";
  if (contentType.includes("application/json")) return res.json();
  const text = await res.text();
  return { detail: text };
}

function buildHeaders(extra: Record<string, string> = {}) {
  const headers: Record<string, string> = { ...extra };
  if (DESKTOP_TOKEN) headers["X-Desktop-Token"] = DESKTOP_TOKEN;
  return headers;
}

export async function anonymizeText(payload: {
  text: string;
  options: AnonymizeOptions;
}): Promise<TextResponse> {
  const res = await fetch(apiUrl("/api/anonymize"), {
    method: "POST",
    headers: buildHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  const data = await handleJson(res);
  if (!res.ok) {
    const msg = data?.detail || `Ошибка сервера (${res.status})`;
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return data as TextResponse;
}

export async function anonymizeFile(file: File, options: AnonymizeOptions): Promise<FileResult> {
  const form = new FormData();
  form.append("file", file);
  form.append("options", JSON.stringify(options));

  const res = await fetch(apiUrl("/api/anonymize-file"), {
    method: "POST",
    body: form,
    headers: buildHeaders(),
  });
  const data = await handleJson(res);
  if (!res.ok) {
    const msg = data?.detail || `Ошибка сервера (${res.status})`;
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return data as FileResult;
}

export async function startBatch(files: File[], options: AnonymizeOptions): Promise<BatchJobCreate> {
  const form = new FormData();
  files.forEach((file) => form.append("files", file));
  form.append("options", JSON.stringify(options));

  const res = await fetch(apiUrl("/api/anonymize-files-async"), {
    method: "POST",
    body: form,
    headers: buildHeaders(),
  });
  const data = await handleJson(res);
  if (!res.ok) {
    const msg = data?.detail || `Ошибка сервера (${res.status})`;
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return data as BatchJobCreate;
}

export async function getBatchStatus(jobId: string): Promise<BatchStatus> {
  const res = await fetch(apiUrl(`/api/batch/${jobId}`), {
    headers: buildHeaders(),
  });
  const data = await handleJson(res);
  if (!res.ok) {
    const msg = data?.detail || `Ошибка сервера (${res.status})`;
    throw new Error(typeof msg === "string" ? msg : JSON.stringify(msg));
  }
  return data as BatchStatus;
}
