// Home: the workflow map from the old POS navigator, grouped the same way.
// Tiles for features not built yet stay visible (so staff recognise the layout) but are
// disabled with the build step that delivers them.
import {
  BarChart3, Boxes, CalendarCheck, ClipboardList, Clock, FileClock, FileText, FolderTree,
  Gift, History, Inbox, LifeBuoy, Package, PackageCheck, PauseCircle, Receipt, Settings,
  ShoppingCart, Timer, Truck, UserCog, Users, type LucideIcon,
} from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { Page } from "../components/ui";
import { HELD_RECEIPTS } from "../mock";
import { can } from "../permissions";
import EndOfDayDialog from "./EndOfDayDialog";

interface Tile {
  label: string;
  icon: LucideIcon;
  to?: string;
  onClick?: () => void;
  later?: string;
  badge?: number;
  arrow?: boolean;
}

function TileButton({ t }: { t: Tile }) {
  const navigate = useNavigate();
  const off = !!t.later || (!t.to && !t.onClick);
  return (
    <button
      className={`tile${off ? " off" : ""}${t.arrow ? " arrow" : ""}`}
      onClick={off ? undefined : t.onClick ?? (() => navigate(t.to!))}
      aria-disabled={off}
    >
      <span className="ico"><t.icon size={22} /></span>
      {t.label}
      {t.badge ? <span className="badge">{t.badge}</span> : null}
      {t.later && <span className="tag">{t.later}</span>}
    </button>
  );
}

function Section({ label, tiles }: { label: string; tiles: Tile[] }) {
  return (
    <section className="card flow-section">
      <div className="flow-label">{label}</div>
      <div className="flow-grid">
        {tiles.map((t) => <TileButton key={t.label} t={t} />)}
      </div>
    </section>
  );
}

export default function Navigator() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [eod, setEod] = useState(false);
  const role = user?.role;

  const pos: Tile[] = [
    { label: "Customer Orders", icon: ClipboardList, later: "Step 7", arrow: true },
    { label: "Make a Sale", icon: ShoppingCart, to: "/sale", arrow: true },
    { label: "Sales History", icon: History, to: "/sales", arrow: true },
    { label: "Customer List", icon: Users, to: "/customers" },
    { label: "Order List", icon: FileText, later: "Step 7" },
    { label: "Held Receipts", icon: PauseCircle, to: "/held", badge: HELD_RECEIPTS.length },
    { label: "End of Day", icon: CalendarCheck, onClick: () => setEod(true) },
    { label: "Reward Manager", icon: Gift, to: "/rewards" },
  ];
  const purchasing: Tile[] = [
    { label: "Purchase Orders", icon: ClipboardList, later: "Step 6", arrow: true },
    { label: "Receiving Vouchers", icon: Truck, later: "Step 6", arrow: true },
    { label: "Receiving History", icon: FileClock, later: "Step 6", arrow: true },
    { label: "Item List", icon: Package, later: "Step 5" },
    { label: "PO List", icon: FileText, later: "Step 6" },
    { label: "Held Vouchers", icon: Inbox, later: "Step 6" },
    { label: "Vendor List", icon: Boxes, later: "Step 6" },
    { label: "Department List", icon: FolderTree, later: "Step 5" },
  ];
  const employees: Tile[] = [
    { label: "Clock In/Out", icon: Clock, later: "Not planned" },
    { label: "Manage Time Clock", icon: Timer, later: "Not planned" },
    { label: "Time Clock History", icon: History, later: "Not planned" },
    can(role, "viewStaff")
      ? { label: "Employee List", icon: UserCog, to: "/staff" }
      : { label: "Employee List", icon: UserCog, later: "Admin/manager" },
  ];
  const ops: Tile[] = [
    { label: "Reports", icon: BarChart3, later: "Step 8" },
    { label: "Preferences", icon: Settings, later: "Later" },
    { label: "Get Support", icon: LifeBuoy, later: "Later" },
  ];

  return (
    <Page
      title="Navigator"
      sub={`Welcome back, ${user?.full_name.split(" ")[0]}`}
      actions={[
        { label: "Make a Sale", icon: ShoppingCart, primary: true, onClick: () => navigate("/sale") },
        { label: "Receive Items", icon: PackageCheck, later: "Step 6" },
        { label: "Item List", icon: Package, later: "Step 5" },
        { label: "Customer List", icon: Users, onClick: () => navigate("/customers") },
        { label: "Department List", icon: FolderTree, later: "Step 5" },
        { label: "Reports", icon: BarChart3, later: "Step 8" },
        { label: "End of Day", icon: Receipt, onClick: () => setEod(true) },
      ]}
    >
      <div className="nav-layout">
        <div className="flow">
          <Section label="Point of Sale" tiles={pos} />
          <Section label="Purchasing" tiles={purchasing} />
          <Section label="Employees" tiles={employees} />
        </div>
        <aside className="card">
          <div className="card-head">Operations</div>
          <div className="ops">
            {ops.map((t) => <TileButton key={t.label} t={t} />)}
          </div>
        </aside>
      </div>
      {eod && <EndOfDayDialog onClose={() => setEod(false)} />}
    </Page>
  );
}
