import { BarChart3, Copy, Printer, RotateCcw, Search, ShoppingCart, Undo2 } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Page, SampleDataNotice } from "../components/ui";
import { SALES_HISTORY } from "../mock";
import ReceiptTable from "./ReceiptTable";

export default function SalesHistory() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [range, setRange] = useState("today");
  const [selected, setSelected] = useState<number | null>(null);
  const rows = SALES_HISTORY.filter((r) =>
    [r.customer, r.cashier, r.payment].some((v) => v.toLowerCase().includes(q.toLowerCase())),
  );

  return (
    <Page
      title="Sales History"
      actions={[
        { label: "Make a Sale", icon: ShoppingCart, primary: true, onClick: () => navigate("/sale") },
        { label: "Accept Return", icon: Undo2, later: "Step 7" },
        { label: "Reprint", icon: Printer, later: "Step 7" },
        { label: "Copy", icon: Copy, later: "Step 7" },
        { label: "Reverse", icon: RotateCcw, later: "Step 7" },
        { label: "Reports", icon: BarChart3, later: "Step 8" },
      ]}
      headExtra={
        <div className="toolbar">
          <div className="search">
            <Search size={16} />
            <input className="input" style={{ width: 240 }} value={q} onChange={(e) => setQ(e.target.value)}
              placeholder="Customer, cashier, payment" aria-label="Search receipts" />
          </div>
          <select className="input select" style={{ width: 140 }} value={range} onChange={(e) => setRange(e.target.value)} aria-label="Date range">
            <option value="today">Today</option>
            <option value="yesterday">Yesterday</option>
            <option value="week">This week</option>
            <option value="month">This month</option>
          </select>
        </div>
      }
    >
      <SampleDataNotice step="Step 7 (POS sale → invoice)" />
      <ReceiptTable rows={rows} selected={selected} onSelect={setSelected} />
    </Page>
  );
}
