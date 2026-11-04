import { X, type LucideIcon } from "lucide-react";
import {
  createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode,
} from "react";
import { STATUS_LABELS } from "../format";
import type { CustomerStatus } from "../types";

/* ---------- Page: left action rail + main content (mirrors the POS layout) ---------- */

export interface RailAction {
  label: string;
  icon: LucideIcon;
  onClick?: () => void;
  primary?: boolean;
  /** Shown as a tag when the action exists in the old POS but is not built yet. */
  later?: string;
  hidden?: boolean;
}

export function Page({
  title, sub, actions, headExtra, children,
}: {
  title: string;
  sub?: ReactNode;
  actions: RailAction[];
  headExtra?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="page">
      <aside className="rail" aria-label={`${title} actions`}>
        <div className="rail-label">Actions</div>
        {actions.filter((a) => !a.hidden).map((a) => (
          <button
            key={a.label}
            className={`rail-btn${a.primary ? " primary" : ""}`}
            onClick={a.onClick}
            disabled={!!a.later || !a.onClick}
          >
            <a.icon size={18} />
            {a.label}
            {a.later && <span className="tag">{a.later}</span>}
          </button>
        ))}
      </aside>
      <main className="content">
        <div className="page-head">
          <h1>{title}</h1>
          {sub && <span className="sub">{sub}</span>}
          <span className="grow" />
          {headExtra}
        </div>
        {children}
      </main>
    </div>
  );
}

/* ---------- Modal ---------- */

export function Modal({
  title, onClose, children, footer, wide,
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
  wide?: boolean;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className={`modal${wide ? " wide" : ""}`} role="dialog" aria-modal="true" aria-label={title}>
        <div className="modal-head">
          <h2>{title}</h2>
          <span className="grow" />
          <button className="iconbtn" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-foot">{footer}</div>}
      </div>
    </div>
  );
}

/* ---------- Toast ---------- */

const ToastContext = createContext<(msg: string) => void>(() => {});

export function ToastProvider({ children }: { children: ReactNode }) {
  const [msg, setMsg] = useState<string | null>(null);
  const timer = useRef<number>();
  const show = useCallback((m: string) => {
    setMsg(m);
    window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setMsg(null), 3500);
  }, []);
  return (
    <ToastContext.Provider value={show}>
      {children}
      {msg && <div className="toast" role="status">{msg}</div>}
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);

/* ---------- Small bits ---------- */

export const StatusTag = ({ status }: { status: CustomerStatus }) => (
  <span className={`tag ${status}`}>{STATUS_LABELS[status]}</span>
);

export const SampleDataNotice = ({ step }: { step: string }) => (
  <div className="notice">
    Sample data. This screen connects to the backend in {step}.
  </div>
);

export function useDebounced<T>(value: T, ms = 250): T {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = window.setTimeout(() => setV(value), ms);
    return () => window.clearTimeout(t);
  }, [value, ms]);
  return v;
}
