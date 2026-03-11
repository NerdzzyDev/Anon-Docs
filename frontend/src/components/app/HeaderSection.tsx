import type { AppMode } from "../../hooks/useAnonymizer";
import { SegmentedControl } from "../ui/SegmentedControl";

type HeaderSectionProps = {
  mode: AppMode;
  onModeChange: (mode: AppMode) => void;
  onBackHome: () => void;
  onResultsOpen: () => void;
};

export function HeaderSection({ mode, onModeChange, onBackHome, onResultsOpen }: HeaderSectionProps) {
  return (
    <>
      <div className="processing-toolbar">
        <button type="button" className="processing-toolbar__back" onClick={onBackHome}>
          <span className="processing-toolbar__back-icon" aria-hidden="true" />
          <span>На главную</span>
        </button>
        <div className="processing-toolbar__tabs">
          <button type="button" className="processing-toolbar__tab" onClick={onBackHome}>
            Главная
          </button>
          <button type="button" className="processing-toolbar__tab is-active">
            Новая загрузка
          </button>
          <button type="button" className="processing-toolbar__tab" onClick={onResultsOpen}>
            Результаты
          </button>
        </div>
      </div>

      <section className="app-card hero-card">
        <div className="hero-card__content">
          <h1 className="hero-card__title">Обезличиватель текста и документов</h1>
          <p className="hero-card__subtitle">
            Выберите режим, отметьте типы данных и получите результат с подсветкой замен
          </p>
        </div>
        <div className="hero-card__control">
          <SegmentedControl
            value={mode}
            onChange={onModeChange}
            options={[
              { label: "Текст", value: "text" },
              { label: "Документ", value: "file" },
            ]}
          />
        </div>
      </section>
    </>
  );
}
