import { useEffect, useMemo, useRef, useState } from "react";
import {
  anonymizeFile,
  anonymizeText,
  getBatchStatus,
  resolveApiUrl,
  startBatch,
  type AnonymizeOptions,
  type BatchItem,
} from "../lib/api";
import { defaultOptions } from "../constants/anonymize";
import type { HistoryEntry } from "../types/history";

export type AppMode = "text" | "file";

type UseAnonymizerOptions = {
  onHistoryEntry?: (entry: HistoryEntry) => void;
};

export function useAnonymizer({ onHistoryEntry }: UseAnonymizerOptions = {}) {
  const [mode, setMode] = useState<AppMode>("text");
  const [options, setOptions] = useState<AnonymizeOptions>(defaultOptions);
  const [inputText, setInputText] = useState("");
  const [outputText, setOutputText] = useState("");
  const [highlightHtml, setHighlightHtml] = useState("");
  const [resultPath, setResultPath] = useState("");
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("Режим: обработка текста");
  const [warning, setWarning] = useState("");
  const [resultItems, setResultItems] = useState<BatchItem[]>([]);
  const [activeItemId, setActiveItemId] = useState<string | null>(null);
  const [isHighlightOpen, setIsHighlightOpen] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [fileInputKey, setFileInputKey] = useState(0);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        window.clearInterval(timerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    setStatus(mode === "text" ? "Режим: обработка текста" : "Режим: обработка документов");
  }, [mode]);

  useEffect(() => {
    if (!activeItemId) return;
    const item = resultItems.find((entry) => entry.filename === activeItemId);
    if (!item?.result) return;
    setOutputText(item.result.preview_text || "");
    setHighlightHtml(item.result.preview_html || "");
    setResultPath(item.result.result_path || "");
  }, [activeItemId, resultItems]);

  const currentFileName = useMemo(() => {
    if (!selectedFiles.length) return "Файл не выбран";
    if (selectedFiles.length === 1) {
      const file = selectedFiles[0];
      return `${getFileDisplayPath(file)} • ${formatSize(file.size)}`;
    }
    return `Выбрано файлов: ${selectedFiles.length}`;
  }, [selectedFiles]);

  const resultItemLabels = useMemo(() => {
    if (!resultItems.length) return [];
    const selectedLabels = selectedFiles.map((file) => getFileDisplayPath(file));
    return resultItems.map((item, index) => selectedLabels[index] || item.filename);
  }, [resultItems, selectedFiles]);

  const characterCount = inputText.length;

  const updateOption = (key: keyof AnonymizeOptions) => {
    setOptions((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const clearText = () => {
    setInputText("");
    setOutputText("");
    setHighlightHtml("");
    setResultPath("");
    setResultItems([]);
    setActiveItemId(null);
    setProgress(0);
    setWarning("");
    setStatus("Режим: обработка текста");
  };

  const resetFileFlow = () => {
    if (timerRef.current) {
      window.clearInterval(timerRef.current);
    }
    setSelectedFiles([]);
    setResultItems([]);
    setActiveItemId(null);
    setOutputText("");
    setHighlightHtml("");
    setResultPath("");
    setWarning("");
    setBusy(false);
    setProgress(0);
    setStatus("Режим: обработка документа");
    setFileInputKey((prev) => prev + 1);
  };

  const onFilesSelected = (files: FileList | null) => {
    const nextFiles = files ? Array.from(files) : [];
    setSelectedFiles(nextFiles);
    setResultItems([]);
    setActiveItemId(null);
    setOutputText("");
    setHighlightHtml("");
    setResultPath("");
    setWarning("");
    nextFiles.forEach((file) => {
      const displayPath = getFileDisplayPath(file);
      onHistoryEntry?.({
        id: `upload:${file.name}:${file.size}`,
        title: displayPath,
        mode: "file",
        status: "uploaded",
        createdAt: new Date().toISOString(),
        sourceName: displayPath,
      });
    });
  };

  const runText = async () => {
    if (!inputText.trim()) {
      throw new Error("Введите текст для обработки");
    }

    setBusy(true);
    setProgress(15);
    setWarning("");
    setStatus("Обработка текста...");

    try {
      const data = await anonymizeText({ text: inputText, options });
      setOutputText(data.anonymized_text || "");
      setHighlightHtml(data.highlighted_html || "");
      setResultPath(data.result_path || "");
      setResultItems([]);
      setActiveItemId(null);
      setProgress(100);
      setStatus("Текст обработан");
      if (data.warnings?.length) setWarning(data.warnings.join(" "));
      onHistoryEntry?.({
        id: `text:${Date.now()}`,
        title: "Текстовый результат",
        mode: "text",
        status: "text",
        createdAt: new Date().toISOString(),
        resultPath: data.result_path || "",
        previewText: data.anonymized_text || "",
        warnings: data.warnings || [],
      });
    } finally {
      setBusy(false);
    }
  };

  const runFile = async () => {
    if (!selectedFiles.length) {
      throw new Error("Выберите файл");
    }

    if (timerRef.current) {
      window.clearInterval(timerRef.current);
    }

    setBusy(true);
    setProgress(12);
    setWarning("");
    setStatus("Обработка файлов...");
    setOutputText("");
    setHighlightHtml("");
    setResultPath("");
    setResultItems([]);
    setActiveItemId(null);

    try {
      if (selectedFiles.length === 1) {
        const result = await anonymizeFile(selectedFiles[0], options);
        const item = { filename: selectedFiles[0].name, result, error: null };
        const sourcePath = getFileDisplayPath(selectedFiles[0]);
        setResultItems([item]);
        setActiveItemId(item.filename);
        setOutputText(result.preview_text || "");
        setHighlightHtml(result.preview_html || "");
        setResultPath(result.result_path || "");
        setProgress(100);
        setStatus("Файл обработан");
        if (result.warnings?.length) setWarning(result.warnings.join(" "));
        onHistoryEntry?.({
          id: `processed:${selectedFiles[0].name}:${result.output_filename}`,
          title: sourcePath,
          mode: "file",
          status: "processed",
          createdAt: new Date().toISOString(),
          sourceName: sourcePath,
          resultPath: result.result_path,
          previewText: result.preview_text,
          downloadUrl: result.download_url,
          outputFilename: result.output_filename,
          warnings: result.warnings,
        });
        setBusy(false);
        return;
      }

      const batch = await startBatch(selectedFiles, options);
      setResultPath(`Задача: ${batch.job_id}`);
      setStatus("Пакетная обработка запущена");

      timerRef.current = window.setInterval(async () => {
        try {
          const statusData = await getBatchStatus(batch.job_id);
          setProgress(statusData.progress || 0);
          setStatus(`Пакет: ${statusData.processed}/${statusData.total}`);

          if (statusData.status !== "completed") return;

          if (timerRef.current) {
            window.clearInterval(timerRef.current);
          }

          const items = statusData.items || [];
          setResultItems(items);
          setActiveItemId(items[0]?.filename || null);
          setOutputText(items[0]?.result?.preview_text || "");
          setHighlightHtml(items[0]?.result?.preview_html || "");
          setResultPath(items[0]?.result?.result_path || `Задача: ${batch.job_id}`);
          setStatus("Пакет обработан");
          setProgress(100);

          const hasErrors = items.some((item) => item.error);
          const warnings = items.flatMap((item) => item.result?.warnings || []);
          items.forEach((item, index) => {
            if (!item.result) return;
            const sourcePath = getFileDisplayPath(selectedFiles[index] || null);
            onHistoryEntry?.({
              id: `processed:${item.filename}:${item.result.output_filename}`,
              title: sourcePath || item.filename,
              mode: "file",
              status: "processed",
              createdAt: new Date().toISOString(),
              sourceName: sourcePath || item.filename,
              resultPath: item.result.result_path,
              previewText: item.result.preview_text,
              downloadUrl: item.result.download_url,
              outputFilename: item.result.output_filename,
              warnings: item.result.warnings,
            });
          });
          if (hasErrors) {
            setWarning("Некоторые файлы обработались с ошибками.");
          } else if (warnings.length) {
            setWarning(warnings.join(" "));
          }
          setBusy(false);
        } catch (error) {
          if (timerRef.current) {
            window.clearInterval(timerRef.current);
          }
          setBusy(false);
          setProgress(0);
          setStatus("Ошибка пакетной обработки");
          throw error;
        }
      }, 800);
    } catch (error) {
      setBusy(false);
      throw error;
    }
  };

  const downloadActive = () => {
    const result = activeItem?.result;
    if (!result?.download_url) return;
    const link = document.createElement("a");
    link.href = resolveApiUrl(result.download_url);
    link.download = result.output_filename || activeItem?.filename || "result";
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  const copyOutput = async () => {
    if (!outputText) {
      throw new Error("Нет текста для копирования");
    }
    await navigator.clipboard.writeText(outputText);
  };

  const activeItem = useMemo(
    () => resultItems.find((item) => item.filename === activeItemId) || null,
    [activeItemId, resultItems],
  );

  const statusLabel = useMemo(() => {
    if (busy && progress > 0 && progress < 100) {
      return `Обработка... ${progress}%`;
    }
    if (mode === "file" && progress === 100 && activeItem) {
      return "Файл обработан";
    }
    return mode === "text" ? "Режим: обработка текста" : "Режим: обработка документа";
  }, [activeItem, busy, mode, progress]);

  return {
    mode,
    setMode,
    options,
    updateOption,
    inputText,
    setInputText,
    outputText,
    resultPath,
    progress,
    status: statusLabel || status,
    busy,
    warning,
    characterCount,
    currentFileName,
    fileInputKey,
    selectedFiles,
    onFilesSelected,
    runText,
    runFile,
    clearText,
    resetFileFlow,
    copyOutput,
    downloadActive,
    activeItem,
    resultItems,
    setActiveItemId,
    highlightHtml,
    isHighlightOpen,
    setIsHighlightOpen,
    resultItemLabels,
  };
}

function formatSize(size: number) {
  if (size < 1024) return `${size} Б`;
  if (size < 1024 * 1024) return `${Math.round(size / 102.4) / 10} КБ`;
  return `${Math.round(size / 1024 / 102.4) / 10} МБ`;
}

function getFileDisplayPath(file: File | null): string {
  if (!file) return "";
  const withPath = file as File & { path?: string };
  return withPath.path || file.name;
}
