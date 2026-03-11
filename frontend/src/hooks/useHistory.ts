import { useEffect, useState } from "react";
import { loadHistory, saveHistory, upsertHistoryEntry } from "../lib/history";
import type { HistoryEntry } from "../types/history";

export function useHistory() {
  const [history, setHistory] = useState<HistoryEntry[]>(() => loadHistory());

  useEffect(() => {
    saveHistory(history);
  }, [history]);

  const addHistoryEntry = (entry: HistoryEntry) => {
    setHistory((prev) => upsertHistoryEntry(prev, entry));
  };

  return {
    history,
    addHistoryEntry,
  };
}
