// Employee list, live against /users. Admins can add staff; managers can only view.
import { Clock, UserPlus } from "lucide-react";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { api, ApiError } from "../api";
import { useAuth } from "../auth";
import { Modal, Page, useToast } from "../components/ui";
import { dateTime } from "../format";
import { can, ROLE_LABELS } from "../permissions";
import type { Role, User } from "../types";

export default function Staff() {
  const { user } = useAuth();
  const toast = useToast();
  const [users, setUsers] = useState<User[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);

  const load = useCallback(() => {
    api<User[]>("/users").then(setUsers).catch((e) => setError(e instanceof ApiError ? e.message : "Could not load staff"));
  }, []);
  useEffect(load, [load]);

  if (!can(user?.role, "viewStaff")) return <Navigate to="/" replace />;

  return (
    <Page
      title="Employees"
      sub={users ? `${users.length} staff accounts` : undefined}
      actions={[
        { label: "Add staff", icon: UserPlus, primary: true, hidden: !can(user?.role, "manageStaff"), onClick: () => setAdding(true) },
        { label: "Time Clock", icon: Clock, later: "Not planned" },
      ]}
    >
      {error && <div className="error">{error}</div>}
      <div className="grid-wrap">
        <table className="grid">
          <thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Last sign-in</th></tr></thead>
          <tbody>
            {users?.map((u) => (
              <tr key={u.id} style={{ cursor: "default" }}>
                <td><strong>{u.full_name}</strong></td>
                <td>{u.email}</td>
                <td>{ROLE_LABELS[u.role]}</td>
                <td><span className={`tag ${u.is_active ? "active" : "inactive"}`}>{u.is_active ? "Active" : "Disabled"}</span></td>
                <td className="muted">{u.last_login_at ? dateTime(u.last_login_at) : "Never"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {adding && (
        <AddStaff onClose={() => setAdding(false)} onSaved={(u) => { setAdding(false); toast(`Added ${u.full_name}`); load(); }} />
      )}
    </Page>
  );
}

function AddStaff({ onClose, onSaved }: { onClose: () => void; onSaved: (u: User) => void }) {
  const [f, setF] = useState({ full_name: "", email: "", password: "", role: "cashier" as Role });
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      onSaved(await api<User>("/users", { method: "POST", body: f }));
    } catch (err) {
      if (err instanceof ApiError) { setError(err.message); setFieldErrors(err.fieldErrors); }
    }
  };

  return (
    <Modal title="Add staff account" onClose={onClose} footer={
      <>
        <button className="btn" onClick={onClose}>Cancel</button>
        <button className="btn primary" form="staff-form">Create account</button>
      </>
    }>
      <form id="staff-form" className="form-grid" onSubmit={submit}>
        {error && <div className="error span-6">{error}</div>}
        {(["full_name", "email", "password"] as const).map((k) => (
          <div key={k} className="field span-6">
            <label htmlFor={`sf-${k}`}>{{ full_name: "Full name", email: "Email", password: "Temporary password" }[k]}</label>
            <input id={`sf-${k}`} className={`input${fieldErrors[k] ? " invalid" : ""}`} required
              type={k === "password" ? "password" : k === "email" ? "email" : "text"}
              minLength={k === "password" ? 10 : undefined} autoComplete="off"
              value={f[k]} onChange={(e) => setF({ ...f, [k]: e.target.value })} />
            {fieldErrors[k] && <span className="err">{fieldErrors[k]}</span>}
          </div>
        ))}
        <div className="field span-6">
          <label htmlFor="sf-role">Role</label>
          <select id="sf-role" className="input select" value={f.role} onChange={(e) => setF({ ...f, role: e.target.value as Role })}>
            {(Object.keys(ROLE_LABELS) as Role[]).map((r) => <option key={r} value={r}>{ROLE_LABELS[r]}</option>)}
          </select>
        </div>
      </form>
    </Modal>
  );
}
