// Register screen. USB barcode scanners type the code and press Enter, so the scan box keeps
// focus and Enter adds the item. The customer picker is live (/customers); items, tax and
// saving the invoice use sample data until Steps 5 and 7.
import {
  Banknote, CreditCard, FileSignature, Landmark, Minus, PauseCircle, Percent, Plus, ScanBarcode,
  Search, Tag, Trash2, Undo2, UserRound, X, Zap,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { Page, StatusTag, useDebounced, useToast } from "../components/ui";
import { money } from "../format";
import { CATALOG, QUICK_PICKS, type CatalogItem } from "../mock";
import type { Customer, CustomerListItem, CustomerPage } from "../types";

// Placeholder rate. Real tax codes per item/customer come with products (Step 5).
const TAX_RATE = 0.0625;

interface Line { item: CatalogItem; qty: number }

function findItem(code: string): CatalogItem | undefined {
  const c = code.trim().toLowerCase();
  return (
    CATALOG.find((i) => i.barcode === c || i.itemNo === c) ??
    CATALOG.find((i) => i.name.toLowerCase().includes(c))
  );
}

export default function MakeSale() {
  const toast = useToast();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [lines, setLines] = useState<Line[]>([]);
  const [scan, setScan] = useState("");
  const [customer, setCustomer] = useState<CustomerListItem | null>(null);
  const scanRef = useRef<HTMLInputElement>(null);

  // Arriving from the customer list with ?customer=<id>
  useEffect(() => {
    const id = params.get("customer");
    if (id) api<Customer>(`/customers/${id}`).then(setCustomer).catch(() => {});
  }, [params]);

  const add = (item: CatalogItem, qty = 1) => {
    setLines((prev) => {
      const i = prev.findIndex((l) => l.item.itemNo === item.itemNo);
      if (i === -1) return [...prev, { item, qty }];
      const next = [...prev];
      next[i] = { ...next[i], qty: next[i].qty + qty };
      return next;
    });
    scanRef.current?.focus();
  };

  const onScan = (e: KeyboardEvent<HTMLInputElement>) => {
    // Read the DOM value: a scanner can send Enter before React re-renders with the last digit.
    const code = e.currentTarget.value;
    if (e.key !== "Enter" || !code.trim()) return;
    const item = findItem(code);
    if (item) add(item);
    else toast(`No item matches "${code}"`);
    setScan("");
  };

  const setQty = (itemNo: string, qty: number) =>
    setLines((prev) => prev.flatMap((l) => (l.item.itemNo !== itemNo ? [l] : qty <= 0 ? [] : [{ ...l, qty }])));

  const totals = useMemo(() => {
    let sub = 0;
    let tax = 0;
    for (const l of lines) {
      const ext = l.item.priceCents * l.qty;
      sub += ext;
      if (l.item.taxable) tax += Math.round(ext * TAX_RATE);
    }
    return { sub, tax, total: sub + tax };
  }, [lines]);

  const ready = lines.length > 0 && customer !== null;
  const tender = (name: string) =>
    toast(`${name}: ${money(totals.total)} for ${customer!.business_name}. Saving invoices arrives in Step 7.`);
  const clear = () => { setLines([]); setCustomer(null); scanRef.current?.focus(); };

  return (
    <Page
      title="Make a Sale"
      sub="Register 1"
      actions={[
        { label: "Quick Pick Items", icon: Zap, onClick: () => add(QUICK_PICKS[0]) },
        { label: "Add New Item", icon: Plus, later: "Step 5" },
        { label: "Give Discount", icon: Percent, later: "Step 7" },
        { label: "Accept Return", icon: Undo2, later: "Step 7" },
        { label: "Cashier/Associate", icon: UserRound, later: "Step 7" },
        { label: "Held Receipts", icon: PauseCircle, onClick: () => navigate("/held") },
      ]}
    >
      <div className="sale">
        <div className="sale-inputs">
          <div className="search scan">
            <ScanBarcode size={20} />
            <input
              ref={scanRef} className="input" autoFocus value={scan}
              onChange={(e) => setScan(e.target.value)} onKeyDown={onScan}
              placeholder="Scan barcode or type item # / name, then Enter"
              aria-label="Scan or enter item"
            />
          </div>
          <CustomerPicker value={customer} onChange={setCustomer} />
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 8, minHeight: 0 }}>
          <div className="toolbar">
            <span className="muted" style={{ fontSize: 12 }}>Quick picks:</span>
            {QUICK_PICKS.map((i) => (
              <button key={i.itemNo} className="btn" style={{ height: 30 }} onClick={() => add(i)}>
                <Tag size={14} />{i.name}
              </button>
            ))}
          </div>
          <div className="grid-wrap" style={{ flex: 1 }}>
            <table className="grid">
              <thead>
                <tr>
                  <th>Item #</th><th>Item name</th><th>Flavor</th><th>Size</th>
                  <th className="num">Qty</th><th className="num">Price</th><th className="num">Ext price</th>
                  <th>Tax</th><th />
                </tr>
              </thead>
              <tbody>
                {lines.map(({ item, qty }) => (
                  <tr key={item.itemNo} style={{ cursor: "default" }}>
                    <td className="mono">{item.itemNo}</td>
                    <td><strong>{item.name}</strong></td>
                    <td>{item.flavor}</td>
                    <td>{item.size}</td>
                    <td className="num">
                      <span style={{ display: "inline-flex", gap: 4, alignItems: "center" }}>
                        <button className="iconbtn" onClick={() => setQty(item.itemNo, qty - 1)} aria-label="Decrease"><Minus size={14} /></button>
                        <input className="input qty" inputMode="numeric" value={qty} aria-label={`Quantity of ${item.name}`}
                          onChange={(e) => setQty(item.itemNo, Number(e.target.value.replace(/\D/g, "")) || 0)} />
                        <button className="iconbtn" onClick={() => setQty(item.itemNo, qty + 1)} aria-label="Increase"><Plus size={14} /></button>
                      </span>
                    </td>
                    <td className="num">{money(item.priceCents)}</td>
                    <td className="num"><strong>{money(item.priceCents * qty)}</strong></td>
                    <td><span className="tag">{item.taxable ? "Tax" : "Non"}</span></td>
                    <td>
                      <button className="iconbtn" onClick={() => setQty(item.itemNo, 0)} aria-label={`Remove ${item.name}`}>
                        <Trash2 size={16} color="var(--danger)" />
                      </button>
                    </td>
                  </tr>
                ))}
                {lines.length === 0 && (
                  <tr className="empty"><td colSpan={9}>
                    Scan an item to start. Sample barcodes: {CATALOG.slice(0, 3).map((i) => i.barcode).join(", ")}
                  </td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="sale-foot">
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {!customer && lines.length > 0 && (
              <div className="notice">Select the customer account: every sale becomes an invoice under a customer.</div>
            )}
            <div className="tenders">
              <button className="tender" disabled={!ready} onClick={() => tender("Cash")}><Banknote size={20} />Cash</button>
              <button className="tender" disabled={!ready} onClick={() => tender("Credit")}><CreditCard size={20} />Credit</button>
              <button className="tender" disabled={!ready} onClick={() => tender("Debit")}><CreditCard size={20} />Debit</button>
              <button className="tender" disabled={!ready} onClick={() => tender("Check")}><FileSignature size={20} />Check</button>
              <button className="tender" disabled={!ready} onClick={() => tender("On account")}><Landmark size={20} />Account</button>
            </div>
            <div className="toolbar">
              <button className="btn" disabled={!lines.length} onClick={() => toast("Holding receipts arrives in Step 7.")}>
                <PauseCircle size={16} />Hold
              </button>
              <button className="btn danger" disabled={!lines.length && !customer} onClick={clear}>
                <X size={16} />Cancel sale
              </button>
            </div>
          </div>
          <div className="card totals">
            <div className="row"><span>Subtotal</span><span className="num">{money(totals.sub)}</span></div>
            <div className="row"><span>Tax <span className="muted">(placeholder {TAX_RATE * 100}%)</span></span><span className="num">{money(totals.tax)}</span></div>
            <div className="row total"><span>Amount due</span><span className="num">{money(totals.total)}</span></div>
          </div>
        </div>
      </div>
    </Page>
  );
}

function CustomerPicker({
  value, onChange,
}: {
  value: CustomerListItem | null;
  onChange: (c: CustomerListItem | null) => void;
}) {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [hl, setHl] = useState(0);
  const [results, setResults] = useState<CustomerListItem[]>([]);
  const dq = useDebounced(q, 200);

  useEffect(() => {
    if (!dq.trim()) { setResults([]); return; }
    let live = true;
    api<CustomerPage>("/customers", { params: { q: dq.trim(), limit: 8 } })
      .then((p) => live && (setResults(p.items), setHl(0)))
      .catch(() => live && setResults([]));
    return () => { live = false; };
  }, [dq]);

  if (value) {
    return (
      <div className={`chosen ${value.status}`}>
        <UserRound size={18} />
        <div className="grow" style={{ minWidth: 0 }}>
          <strong>{value.business_name}</strong>{" "}
          <span className="muted mono">{value.account_number}</span>
          <div className="muted" style={{ fontSize: 12 }}>
            {value.owner_name} · {value.city} · Balance: Step 8
          </div>
        </div>
        {value.status !== "active" && <StatusTag status={value.status} />}
        <button className="iconbtn" onClick={() => onChange(null)} aria-label="Change customer"><X size={16} /></button>
      </div>
    );
  }

  const pick = (c: CustomerListItem) => { onChange(c); setQ(""); setOpen(false); };
  return (
    <div className="picker">
      <div className="search scan">
        <Search size={18} />
        <input
          className="input" value={q} placeholder="Customer: name, account # or phone"
          aria-label="Customer"
          onChange={(e) => { setQ(e.target.value); setOpen(true); }}
          onFocus={() => setOpen(true)}
          onBlur={() => window.setTimeout(() => setOpen(false), 150)}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") setHl((h) => Math.min(h + 1, results.length - 1));
            if (e.key === "ArrowUp") setHl((h) => Math.max(h - 1, 0));
            if (e.key === "Enter" && results[hl]) pick(results[hl]);
          }}
        />
      </div>
      {open && q.trim() && (
        <div className="picker-list">
          {results.map((c, i) => (
            <button key={c.id} className={i === hl ? "hl" : ""} onMouseDown={() => pick(c)}>
              <span className="mono muted">{c.account_number}</span>
              <span className="grow"><strong>{c.business_name}</strong> <span className="muted">· {c.owner_name}</span></span>
              {c.status !== "active" && <StatusTag status={c.status} />}
            </button>
          ))}
          {results.length === 0 && <div className="muted" style={{ padding: 12 }}>No matching customers</div>}
        </div>
      )}
    </div>
  );
}
