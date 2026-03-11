import { useState } from "react";
import type { HistoryEntry } from "../../types/history";

type HomeScreenProps = {
  onOpenUpload: (mode?: "file" | "text") => void;
  history: HistoryEntry[];
};

export function HomeScreen({ onOpenUpload, history }: HomeScreenProps) {
  const [section, setSection] = useState<"upload" | "uploaded" | "processed">("upload");
  const uploadedItems = history.filter((item) => item.status === "uploaded");
  const processedItems = history.filter((item) => item.status === "processed" || item.status === "text");
  const recentItems = history.slice(0, 2);

  return (
    <main className="home-screen">
      <aside className="home-sidebar">
        <div className="home-sidebar__brand">
          <span className="home-sidebar__burger" aria-hidden="true">
            <span />
            <span />
            <span />
          </span>
          <span>Обезличиватель текста</span>
        </div>

        <nav className="home-sidebar__nav">
          <button
            type="button"
            className={`home-sidebar__nav-item${section === "upload" ? " is-active" : ""}`}
            onClick={() => setSection("upload")}
          >
            <span className="home-sidebar__icon home-sidebar__icon--home" />
            <span>Главная</span>
          </button>
          <button
            type="button"
            className={`home-sidebar__nav-item${section === "uploaded" ? " is-active" : ""}`}
            onClick={() => setSection("uploaded")}
          >
            <span className="home-sidebar__icon home-sidebar__icon--download" />
            <span>Загруженные файлы</span>
          </button>
          <button
            type="button"
            className={`home-sidebar__nav-item${section === "processed" ? " is-active" : ""}`}
            onClick={() => setSection("processed")}
          >
            <span className="home-sidebar__icon home-sidebar__icon--folder" />
            <span>Обработанные</span>
          </button>
        </nav>

        <div className="home-sidebar__recent">
          <p className="home-sidebar__recent-title">НЕДАВНОЕ ДОКУМЕНТЫ</p>
          {recentItems.length ? (
            recentItems.map((item) => (
              <button key={item.id} type="button" className="home-sidebar__recent-item" onClick={() => onOpenUpload(item.mode)}>
                <span className="home-sidebar__icon home-sidebar__icon--file" />
                <span className="home-sidebar__recent-text">{item.title}</span>
              </button>
            ))
          ) : (
            <p className="home-sidebar__empty">История появится после первой обработки</p>
          )}
        </div>
      </aside>

      <section className="home-main">
        <header className="home-topbar">
          <div className="home-topbar__tabs">
            <button
              type="button"
              className={`home-topbar__tab${section === "upload" ? " is-active" : ""}`}
              onClick={() => setSection("upload")}
            >
              Новая загрузка
            </button>
            <button
              type="button"
              className={`home-topbar__tab${section === "uploaded" ? " is-active" : ""}`}
              onClick={() => setSection("uploaded")}
            >
              Загруженные
            </button>
            <button
              type="button"
              className={`home-topbar__tab${section === "processed" ? " is-active" : ""}`}
              onClick={() => setSection("processed")}
            >
              Готовые документы
            </button>
          </div>
          <button type="button" className="home-topbar__settings" aria-label="Настройки" />
        </header>

        <div className="home-dropzone-layout">
          {section === "upload" ? (
            <div className="home-dropzone-layout__content">
              <h1 className="home-dropzone-layout__title">Обезличиватель документов</h1>
              <p className="home-dropzone-layout__subtitle">ФИО • Телефоны • Email • Реквизиты • PDF</p>

              <button type="button" className="home-dropzone" onClick={() => onOpenUpload("file")}>
                <span className="home-dropzone__icon" aria-hidden="true" />
                <span className="home-dropzone__title">Перетащите файл сюда</span>
                <span className="home-dropzone__action">или нажмите для выбора</span>
                <span className="home-dropzone__formats">TXT • DOCX • PDF</span>
              </button>
            </div>
          ) : (
            <div className="home-library">
              <div className="home-library__header">
                <h1 className="home-library__title">
                  {section === "uploaded" ? "Загруженные файлы" : "Готовые документы"}
                </h1>
                <button type="button" className="home-library__action" onClick={() => onOpenUpload("file")}>
                  Открыть обработку
                </button>
              </div>
              <div className="home-library__list">
                {(section === "uploaded" ? uploadedItems : processedItems).length ? (
                  (section === "uploaded" ? uploadedItems : processedItems).map((item) => (
                    <button key={item.id} type="button" className="home-library__item" onClick={() => onOpenUpload(item.mode)}>
                      <span className="home-sidebar__icon home-sidebar__icon--file" />
                      <span className="home-library__item-name">{item.title}</span>
                      <span className="home-library__item-meta">
                        {section === "uploaded"
                          ? "Ожидает обработки"
                          : item.resultPath || item.outputFilename || "Готово к скачиванию"}
                      </span>
                    </button>
                  ))
                ) : (
                  <div className="home-library__empty">
                    {section === "uploaded" ? "Пока нет загруженных файлов" : "Пока нет обработанных документов"}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </section>
    </main>
  );
}
