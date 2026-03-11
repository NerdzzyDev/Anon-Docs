import type { PropsWithChildren, ReactNode } from "react";

type AppCardProps = PropsWithChildren<{
  title?: string;
  actions?: ReactNode;
  className?: string;
}>;

export function AppCard({ title, actions, className = "", children }: AppCardProps) {
  return (
    <section className={`app-card ${className}`.trim()}>
      {(title || actions) && (
        <div className="app-card__header">
          {title ? <h2 className="app-card__title">{title}</h2> : <span />}
          {actions}
        </div>
      )}
      {children}
    </section>
  );
}
