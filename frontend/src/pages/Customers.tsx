// Customer list + detail, live against /customers. Tax IDs are masked for everyone; admins can
// reveal one at a time (each reveal is audit-logged by the backend).
import {
  BarChart3, Eye, EyeOff, IdCard, Pencil, Search, ShoppingCart, Undo2, UserPlus,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api, ApiError } from "../api";
import { useAuth } from "../auth";
import { Page, StatusTag, useDebounced, useToast } from "../components/ui";
import { dateTime } from "../format";
import { can } from "../permissions";
import type { Customer, CustomerPage, CustomerStatus, TaxIdReveal } from "../types";
import CustomerForm from "./CustomerForm";

const PAGE_SIZE = 50;

export default function Customers() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();
  const [params, setParams] = useSearchParams();
  const [q, setQ] = useState(params.get("q") ?? "");
  const [status, setStatus] = useState<CustomerStatus | "">("");
  const [offset, setOffset] = useState(0);
  const [page, setPage] = useState<CustomerPage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<Customer | null>(null);
  const [form, setForm] = useState<"new" | "edit" | null>(null);
  const debouncedQ = useDebounced(q);

  // Quick-find in the top bar navigates here with ?q=
  useEffect(() => setQ(params.get("q") ?? ""), [params]);
  useEffect(() => setOffset(0), [debouncedQ, status]);

  const load = useCallback(async () => {
    try {
      setError(null);
      setPage(await api<CustomerPage>("/customers", {
        params: { q: debouncedQ.trim(), status, limit: PAGE_SIZE, offset },
      }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load customers");
    }
  }, [debouncedQ, status, offset]);

  useEffect(() => { load(); }, [load]);

  const select = async (id: number) => {
    try {
      setSelected(await api<Customer>(`/customers/${id}`));
    } catch (err) {
      toast(err instanceof ApiError ? err.message : "Could not load customer");
    }
  };

  const onSaved = (c: Customer) => {
    toast(form === "new" ? `Registered ${c.business_name} as ${c.account_number}` : "Customer updated");
    setForm(null);
    setSelected(c);
    load();
  };

  const role = user?.role;
  return (
    <Page
      title="Customers"
      sub={page ? `${page.total.toLocaleString()} customer${page.total === 1 ? "" : "s"}` : undefined}
      actions={[
        { label: "Register customer", icon: UserPlus, primary: true, hidden: !can(role, "registerCustomer"), onClick: () => setForm("new") },
        { label: "Edit", icon: Pencil, hidden: !can(role, "editCustomer"), onClick: selected ? () => setForm("edit") : undefined },
        { label: "Make a Sale", icon: ShoppingCart, onClick: selected ? () => navigate(`/sale?customer=${selected.id}`) : undefined },
        { label: "Accept Return", icon: Undo2, later: "Step 7" },
        { label: "Print ID Cards", icon: IdCard, later: "Later" },
        { label: "Reports", icon: BarChart3, later: "Step 8" },
      ]}
    >
      <div className="split">
        <div className="grid-col">
          <div className="toolbar">
            <div className="search grow" style={{ minWidth: 220 }}>
              <Search size={16} />
              <input
                className="input" value={q} placeholder="Search name, owner, account # or phone"
                onChange={(e) => { setQ(e.target.value); if (params.has("q")) setParams({}, { replace: true }); }}
                aria-label="Search customers" maxLength={100}
              />
            </div>
            <select className="input select" style={{ width: 160 }} value={status}
              onChange={(e) => setStatus(e.target.value as CustomerStatus | "")} aria-label="Status">
              <option value="">All customers</option>
              <option value="active">Active</option>
              <option value="on_hold">On hold</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
          {error && <div className="error">{error}</div>}
          <div className="grid-wrap" style={{ flex: 1 }}>
            <table className="grid">
              <thead>
                <tr>
                  <th>Account #</th><th>Business</th><th>Owner</th><th>Phone</th><th>City</th>
                  <th>Status</th><th className="num" title="Balances arrive in Step 8">Balance</th>
                </tr>
              </thead>
              <tbody>
                {page?.items.map((c) => (
                  <tr key={c.id} className={selected?.id === c.id ? "selected" : ""} onClick={() => select(c.id)}>
                    <td className="mono">{c.account_number}</td>
                    <td><strong>{c.business_name}</strong></td>
                    <td>{c.owner_name}</td>
                    <td>{c.phone ?? <span className="muted">—</span>}</td>
                    <td>{c.city}, {c.state}</td>
                    <td><StatusTag status={c.status} /></td>
                    <td className="num muted">—</td>
                  </tr>
                ))}
                {page && page.items.length === 0 && (
                  <tr className="empty"><td colSpan={7}>
                    {debouncedQ || status ? "No customers match." : "No customers yet. Register the first one."}
                  </td></tr>
                )}
              </tbody>
            </table>
          </div>
          {page && (
            <div className="grid-foot">
              {page.total === 0 ? "0 records" : `${offset + 1}–${offset + page.items.length} of ${page.total}`}
              {selected && " · 1 selected"}
              <span className="grow" />
              <button className="btn" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}>Previous</button>
              <button className="btn" disabled={offset + PAGE_SIZE >= page.total} onClick={() => setOffset(offset + PAGE_SIZE)}>Next</button>
            </div>
          )}
        </div>
        {selected ? (
          <CustomerDetail key={selected.id} customer={selected} onEdit={can(role, "editCustomer") ? () => setForm("edit") : undefined} />
        ) : (
          <div className="card" style={{ display: "grid", placeItems: "center", padding: 40, color: "var(--text-3)" }}>
            Select a customer to see details
          </div>
        )}
      </div>
      {form && (
        <CustomerForm customer={form === "edit" ? selected ?? undefined : undefined} onClose={() => setForm(null)} onSaved={onSaved} />
      )}
    </Page>
  );
}

function CustomerDetail({ customer: c, onEdit }: { customer: Customer; onEdit?: () => void }) {
  const { user } = useAuth();
  const [revealed, setRevealed] = useState<string | null>(null);
  const [revealError, setRevealError] = useState<string | null>(null);

  const reveal = async () => {
    try {
      const r = await api<TaxIdReveal>(`/customers/${c.id}/tax-id`);
      setRevealed(r.tax_id);
    } catch (err) {
      setRevealError(err instanceof ApiError ? err.message : "Could not reveal");
    }
  };

  return (
    <div className="detail">
      <div className="card detail-head">
        <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
          <div className="grow">
            <h2>{c.business_name}</h2>
            <div className="muted">{c.owner_name} · <span className="mono">{c.account_number}</span></div>
          </div>
          <StatusTag status={c.status} />
          {onEdit && <button className="btn" onClick={onEdit}><Pencil size={14} />Edit</button>}
        </div>
      </div>

      <div className="cards-2">
        <div className="card">
          <div className="card-head">Contact</div>
          <dl className="card-body dl">
            <dt>Phone</dt><dd>{c.phone ?? "—"}</dd>
            <dt>Email</dt><dd>{c.email ?? "—"}</dd>
          </dl>
        </div>
        <div className="card">
          <div className="card-head">Account</div>
          <dl className="card-body dl">
            <dt>Balance due</dt><dd className="muted">Step 8</dd>
            <dt>Last sale</dt><dd className="muted">Step 7</dd>
          </dl>
        </div>
      </div>

      <div className="card">
        <div className="card-head">Address</div>
        <div className="card-body">
          {c.address_line1}{c.address_line2 && <>, {c.address_line2}</>}<br />
          {c.city}, {c.state} {c.postal_code}
        </div>
      </div>

      <div className="card">
        <div className="card-head">Tax &amp; compliance</div>
        <dl className="card-body dl">
          <dt>Tax ID (EIN)</dt>
          <dd style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span className="mono">{revealed ?? c.tax_id_masked}</span>
            {can(user?.role, "revealTaxId") && (
              revealed
                ? <button className="btn ghost" style={{ height: 28 }} onClick={() => setRevealed(null)}><EyeOff size={14} />Hide</button>
                : <button className="btn ghost" style={{ height: 28 }} onClick={reveal} title="Every reveal is recorded in the audit log"><Eye size={14} />Reveal</button>
            )}
          </dd>
          {revealError && <><dt /><dd className="err">{revealError}</dd></>}
          <dt>Tobacco license</dt><dd className="muted">Not captured yet</dd>
          <dt>ENDS license</dt><dd className="muted">Not captured yet</dd>
        </dl>
      </div>

      <div className="card">
        <div className="card-head">Recent history</div>
        <div className="card-body muted">Invoices and payments appear here from Step 7.</div>
      </div>

      <div className="card">
        <div className="card-head">Notes</div>
        <div className="card-body" style={{ whiteSpace: "pre-wrap" }}>{c.notes ?? <span className="muted">No notes</span>}</div>
      </div>

      <div className="muted" style={{ fontSize: 12 }}>
        Registered {dateTime(c.created_at)} · Updated {dateTime(c.updated_at)}
      </div>
    </div>
  );
}
