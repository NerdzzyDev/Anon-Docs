export type HistoryEntryStatus = "uploaded" | "processed" | "text";

export type HistoryEntry = {
  id: string;
  title: string;
  mode: "file" | "text";
  status: HistoryEntryStatus;
  createdAt: string;
  sourceName?: string;
  resultPath?: string;
  previewText?: string;
  downloadUrl?: string;
  outputFilename?: string;
  warnings?: string[];
};
