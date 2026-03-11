import { AppCard } from "../ui/AppCard";

type StatusSectionProps = {
  status: string;
  progress: number;
};

export function StatusSection({ status, progress }: StatusSectionProps) {
  return (
    <AppCard className="status-card">
      <div className="status-card__row">
        <p className="status-card__label">{status}</p>
      </div>
      <div className="status-card__progress">
        <div className="status-card__track">
          <div className="status-card__value" style={{ width: `${progress}%` }} />
        </div>
        <span className="status-card__percent">{progress}%</span>
      </div>
    </AppCard>
  );
}
