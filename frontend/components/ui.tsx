"use client";
import type { ReactNode } from "react";

export function Spinner({ className = "" }: { className?: string }) {
  return (
    <span
      className={`spinner inline-block rounded-full border-2 border-current border-t-transparent ${className}`}
      style={{ width: "1em", height: "1em" }}
      aria-label="Загрузка"
    />
  );
}

export function PageLoader({ label = "Загрузка…" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-24 muted">
      <Spinner /> {label}
    </div>
  );
}

export function EmptyState({
  title,
  hint,
  icon = "✨",
  action,
}: {
  title: string;
  hint?: string;
  icon?: string;
  action?: ReactNode;
}) {
  return (
    <div className="card flex flex-col items-center gap-2 px-6 py-12 text-center">
      <div className="text-3xl">{icon}</div>
      <div className="font-medium">{title}</div>
      {hint && <div className="muted text-sm">{hint}</div>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="muted mt-1 text-sm">{subtitle}</p>}
      </div>
      {actions}
    </div>
  );
}
