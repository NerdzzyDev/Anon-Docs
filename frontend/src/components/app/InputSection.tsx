import type { AppMode } from "../../hooks/useAnonymizer";
import { AppCard } from "../ui/AppCard";

type InputSectionProps = {
  mode: AppMode;
  inputText: string;
  onInputTextChange: (value: string) => void;
  characterCount: number;
  currentFileName: string;
  busy: boolean;
  warning: string;
  onSelectFiles: (files: FileList | null) => void;
  onSubmit: () => Promise<void>;
  onClear: () => void;
  onDownload: () => void;
};

export function InputSection({
  mode,
  inputText,
  onInputTextChange,
  characterCount,
  currentFileName,
  busy,
  warning,
  onSelectFiles,
  onSubmit,
  onClear,
  onDownload,
}: InputSectionProps) {
  return (
    <AppCard
      title={mode === "text" ? "Исходный текст" : "Загрузка документов"}
      className={`panel-card ${mode === "text" ? "panel-card--text" : "panel-card--file"}`}
      actions={<span className="panel-card__meta">{characterCount}/2000 символов</span>}
    >
      {mode === "text" ? (
        <>
          <textarea
            className="app-textarea"
            placeholder="Вставьте текст документа для анонимизации"
            value={inputText}
            onChange={(event) => onInputTextChange(event.target.value)}
          />
          <div className="panel-card__actions">
            <button type="button" className="button button--primary" onClick={() => void onSubmit()} disabled={busy}>
              {busy ? "Обработка..." : "Запустить обработку текста"}
            </button>
            <button type="button" className="button button--ghost" onClick={onClear} disabled={busy}>
              Очистить
            </button>
          </div>
        </>
      ) : (
        <>
          <label className="upload-dropzone">
            <input
              type="file"
              multiple
              accept=".txt,.csv,.md,.json,.log,.docx,.xlsx,.xlsm,.pdf,.doc"
              onChange={(event) => onSelectFiles(event.target.files)}
            />
            <span className="upload-dropzone__title">Выбрать файл</span>
            <span className="upload-dropzone__description">Нажмите для выбора документа</span>
          </label>
          <p className="panel-card__filename">{currentFileName}</p>
          <div className="panel-card__actions">
            <button type="button" className="button button--primary" onClick={() => void onSubmit()} disabled={busy}>
              {busy ? "Обработка..." : "Запустить обработку файла"}
            </button>
            <button type="button" className="button button--ghost" onClick={onDownload} disabled={busy}>
              Скачать файл
            </button>
          </div>
        </>
      )}
      {warning ? <p className="panel-card__warning">{warning}</p> : null}
    </AppCard>
  );
}
