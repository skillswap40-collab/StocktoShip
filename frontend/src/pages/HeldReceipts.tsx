import { BarChart3, PlayCircle, Printer, ShoppingCart, Trash2 } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Page, SampleDataNotice } from "../components/ui";
import { HELD_RECEIPTS } from "../mock";
import ReceiptTable from "./ReceiptTable";

export default function HeldReceipts() {
  const navigate = useNavigate();
  const [selected, setSelected] = useState<number | null>(HELD_RECEIPTS[0]?.id ?? null);
  return (
    <Page
      title="Held Receipts"
      sub="Sales parked mid-way, waiting to be finished"
      actions={[
        { label: "Make a Sale", icon: ShoppingCart, primary: true, onClick: () => navigate("/sale") },
        { label: "Unhold", icon: PlayCircle, later: "Step 7" },
        { label: "Reprint", icon: Printer, later: "Step 7" },
        { label: "Delete", icon: Trash2, later: "Step 7" },
        { label: "Reports", icon: BarChart3, later: "Step 8" },
      ]}
    >
      <SampleDataNotice step="Step 7" />
      <ReceiptTable rows={HELD_RECEIPTS} selected={selected} onSelect={setSelected} />
    </Page>
  );
}
