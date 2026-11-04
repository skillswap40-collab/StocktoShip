import { money } from "../format";
import type { ReceiptRow } from "../mock";

export default function ReceiptTable({
  rows, selected, onSelect,
}: {
  rows: ReceiptRow[];
  selected: number | null;
  onSelect: (id: number) => void;
}) {
  return (
    <>
      <div className="grid-wrap" style={{ flex: 1 }}>
        <table className="grid">
          <thead>
            <tr>
              <th>Date</th><th>Time</th><th>Status</th><th>Type</th><th className="num">Register</th>
              <th>Cashier</th><th>Customer</th><th className="num">Total</th><th className="num">Qty</th>
              <th>Payment</th><th className="num">Items</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className={selected === r.id ? "selected" : ""} onClick={() => onSelect(r.id)}>
                <td>{r.date}</td>
                <td>{r.time}</td>
                <td>{r.status}</td>
                <td>{r.type}</td>
                <td className="num">{r.workstation}</td>
                <td>{r.cashier}</td>
                <td><strong>{r.customer}</strong></td>
                <td className="num" style={{ color: r.totalCents < 0 ? "var(--danger)" : undefined }}>
                  <strong>{money(r.totalCents)}</strong>
                </td>
                <td className="num">{r.qty}</td>
                <td><span className="tag">{r.payment}</span></td>
                <td className="num">{r.items}</td>
              </tr>
            ))}
            {rows.length === 0 && <tr className="empty"><td colSpan={11}>No receipts</td></tr>}
          </tbody>
        </table>
      </div>
      <div className="grid-foot">
        {rows.length} record(s){selected !== null && " · 1 selected"}
        <span className="grow" />
        Total {money(rows.reduce((s, r) => s + r.totalCents, 0))}
      </div>
    </>
  );
}
