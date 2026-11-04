import { LogOut, Package, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { can, ROLE_LABELS } from "../permissions";

function Clock() {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const t = window.setInterval(() => setNow(new Date()), 30_000);
    return () => window.clearInterval(t);
  }, []);
  return (
    <span className="clock">
      {now.toLocaleString("en-US", { weekday: "short", month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}
    </span>
  );
}

export default function Shell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  if (!user) return null;

  const initials = user.full_name.split(/\s+/).map((p) => p[0]).slice(0, 2).join("").toUpperCase();

  return (
    <div className="shell">
      <header className="topbar">
        <NavLink to="/" className="brand">
          <span className="brand-mark"><Package size={18} /></span>
          StocktoShip
        </NavLink>
        <nav className="topnav">
          <NavLink to="/" end>Home</NavLink>
          <NavLink to="/sale">Point of Sale</NavLink>
          <NavLink to="/customers">Customers</NavLink>
          <NavLink to="/sales">Sales History</NavLink>
          {can(user.role, "viewStaff") && <NavLink to="/staff">Employees</NavLink>}
        </nav>
        <form
          className="topsearch"
          role="search"
          onSubmit={(e) => {
            e.preventDefault();
            navigate(`/customers?q=${encodeURIComponent(q.trim())}`);
            setQ("");
          }}
        >
          <Search size={16} />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Quick find customer, account # or phone"
            aria-label="Quick find customer"
          />
        </form>
        <Clock />
        <div className="userchip">
          <span className="avatar">{initials}</span>
          <div>
            {user.full_name}
            <small>{ROLE_LABELS[user.role]}</small>
          </div>
          <button className="iconbtn" onClick={logout} title="Sign out" aria-label="Sign out">
            <LogOut size={18} />
          </button>
        </div>
      </header>
      <Outlet />
    </div>
  );
}
