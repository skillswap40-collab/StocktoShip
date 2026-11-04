// Register (POST /customers) or edit (PATCH /customers/{id}) a customer.
import { useState, type FormEvent } from "react";
import { api, ApiError } from "../api";
import { useAuth } from "../auth";
import { Modal } from "../components/ui";
import { can } from "../permissions";
import type { Customer, CustomerStatus } from "../types";

type Fields = {
  business_name: string; owner_name: string; tax_id: string; address_line1: string;
  address_line2: string; city: string; state: string; postal_code: string;
  phone: string; email: string; notes: string; status: CustomerStatus;
};

const empty: Fields = {
  business_name: "", owner_name: "", tax_id: "", address_line1: "", address_line2: "",
  city: "", state: "MA", postal_code: "", phone: "", email: "", notes: "", status: "active",
};

export default function CustomerForm({
  customer, onClose, onSaved,
}: {
  customer?: Customer;
  onClose: () => void;
  onSaved: (c: Customer) => void;
}) {
  const { user } = useAuth();
  const editing = !!customer;
  const taxEditable = !editing || can(user?.role, "changeTaxId");
  const [f, setF] = useState<Fields>(
    customer
      ? {
          ...empty,
          ...Object.fromEntries(
            Object.entries(customer).filter(([k]) => k in empty).map(([k, v]) => [k, v ?? ""]),
          ),
          tax_id: "",
        }
      : empty,
  );
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const set = (k: keyof Fields) => (e: { target: { value: string } }) =>
    setF((prev) => ({ ...prev, [k]: e.target.value }));

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    setErrors({});
    setFormError(null);
    // Edit: send only what changed; never send an empty tax ID (it means "keep the current one").
    const body: Record<string, string> = {};
    for (const [k, v] of Object.entries(f) as [keyof Fields, string][]) {
      if (k === "status" && !editing) continue;
      if (k === "tax_id" && (!v || !taxEditable)) continue;
      if (editing && k !== "tax_id" && (customer![k] ?? "") === v) continue;
      body[k] = v;
    }
    try {
      const saved = editing
        ? await api<Customer>(`/customers/${customer!.id}`, { method: "PATCH", body })
        : await api<Customer>("/customers", { method: "POST", body });
      onSaved(saved);
    } catch (err) {
      if (err instanceof ApiError) {
        setErrors(err.fieldErrors);
        setFormError(err.message);
      } else setFormError("Could not save the customer");
    } finally {
      setBusy(false);
    }
  };

  const input = (k: keyof Fields, label: string, span: string, opts: {
    required?: boolean; type?: string; placeholder?: string; hint?: string; disabled?: boolean;
  } = {}) => (
    <div className={`field ${span}`}>
      <label htmlFor={`cf-${k}`}>{label}{opts.required && " *"}</label>
      <input
        id={`cf-${k}`} className={`input${errors[k] ? " invalid" : ""}`} type={opts.type ?? "text"}
        value={f[k]} onChange={set(k)} required={opts.required} placeholder={opts.placeholder}
        disabled={opts.disabled}
      />
      {errors[k] ? <span className="err">{errors[k]}</span> : opts.hint && <span className="hint">{opts.hint}</span>}
    </div>
  );

  return (
    <Modal
      wide
      title={editing ? `Edit ${customer!.business_name}` : "Register customer"}
      onClose={onClose}
      footer={
        <>
          <button className="btn" type="button" onClick={onClose}>Cancel</button>
          <button className="btn primary" form="customer-form" disabled={busy}>
            {busy ? "Saving…" : editing ? "Save changes" : "Register customer"}
          </button>
        </>
      }
    >
      <form id="customer-form" onSubmit={submit} className="form-grid">
        {formError && <div className="error span-6">{formError}</div>}
        {input("business_name", "Business / store name", "span-4", { required: true })}
        {input("owner_name", "Owner name", "span-2", { required: true })}
        {taxEditable
          ? input("tax_id", editing ? "New tax ID (EIN)" : "Tax ID (EIN)", "span-2", {
              required: !editing,
              placeholder: editing ? customer!.tax_id_masked : "12-3456789",
              hint: editing ? "Leave blank to keep the current one" : "9 digits",
            })
          : (
            <div className="field span-2">
              <label>Tax ID (EIN)</label>
              <input className="input" value={customer!.tax_id_masked} disabled />
              <span className="hint">Only admins can change it</span>
            </div>
          )}
        {input("phone", "Phone", "span-2", { type: "tel" })}
        {input("email", "Email", "span-2", { type: "email" })}
        {input("address_line1", "Street address", "span-4", { required: true })}
        {input("address_line2", "Suite / unit", "span-2")}
        {input("city", "City", "span-3", { required: true })}
        {input("state", "State", "span-1", { required: true })}
        {input("postal_code", "ZIP", "span-2", { required: true, placeholder: "02108" })}
        {editing && (
          <div className="field span-2">
            <label htmlFor="cf-status">Status</label>
            <select id="cf-status" className="input select" value={f.status} onChange={set("status")}>
              <option value="active">Active</option>
              <option value="on_hold">On hold</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
        )}
        <div className="field span-6">
          <label htmlFor="cf-notes">Notes</label>
          <textarea id="cf-notes" className="input" rows={3} maxLength={2000} value={f.notes}
            onChange={set("notes")} />
        </div>
      </form>
    </Modal>
  );
}
