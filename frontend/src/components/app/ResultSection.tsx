import type { RefObject } from "react";
import type { BatchItem } from "../../lib/api";
import { AppCard } from "../ui/AppCard";
import type { AppMode } from "../../hooks/useAnonymizer";

type ResultSectionProps = {
  mode: AppMode;
  outputText: string;
  busy: boolean;
  onCopy: () => Promise<void>;
  onDownload: () => void;
  items: BatchItem[];
  activeItemId?: string;
  onSelectItem: (filename: string) => void;
  sectionRef?: RefObject<HTMLDivElement | null>;
  downloadName?: string;
};

export function ResultSection({
  mode,
  outputText,
  busy,
  onCopy,
  onDownload,
  items,
  activeItemId,
  onSelectItem,
  sectionRef,
  downloadName,
}: ResultSectionProps) {
  const title = mode === "text" ? "Обезличенный текст" : "Результат";
  const canDownload = mode === "file" && Boolean(downloadName);

  return (
    <AppCard
      title={title}
      className="panel-card"
      actions={
        <button type="button" className="copy-action" onClick={() => void onCopy()} disabled={busy}>
          <span className="copy-action__icon" />
          <span>Скопировать текст</span>
        </button>
      }
    >
      <div className="result-output" ref={sectionRef}>
        <textarea
          className="app-textarea app-textarea--output"
          readOnly
          value={outputText}
          placeholder="Здесь появится обработанный текст с подсветкой замен"
        />
      </div>
      {items.length > 1 ? (
        <div className="result-list">
          {items.map((item) => (
            <button
              key={item.filename}
              type="button"
              className={`result-list__item${activeItemId === item.filename ? " is-active" : ""}`}
              onClick={() => onSelectItem(item.filename)}
            >
              <span>{item.filename}</span>
              <span>{item.error ? "Ошибка" : "Готово"}</span>
            </button>
          ))}
        </div>
      ) : null}
      {canDownload ? (
        <div className="download-panel">
          <div className="download-panel__meta">
            <p className="download-panel__label">Готовый файл</p>
            <p className="download-panel__name">{downloadName}</p>
          </div>
          <button type="button" className="download-panel__button" onClick={onDownload} disabled={busy}>
            <span className="download-panel__icon" aria-hidden="true" />
            <span>Скачать</span>
          </button>
        </div>
      ) : null}
    </AppCard>
  );
}
