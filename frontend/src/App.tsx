import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth";
import Shell from "./components/Shell";
import { ToastProvider } from "./components/ui";
import Customers from "./pages/Customers";
import HeldReceipts from "./pages/HeldReceipts";
import Login from "./pages/Login";
import MakeSale from "./pages/MakeSale";
import Navigator from "./pages/Navigator";
import RewardManager from "./pages/RewardManager";
import SalesHistory from "./pages/SalesHistory";
import Staff from "./pages/Staff";

function Routed() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Login />;
  return (
    <Routes>
      <Route element={<Shell />}>
        <Route index element={<Navigator />} />
        <Route path="sale" element={<MakeSale />} />
        <Route path="sales" element={<SalesHistory />} />
        <Route path="held" element={<HeldReceipts />} />
        <Route path="customers" element={<Customers />} />
        <Route path="staff" element={<Staff />} />
        <Route path="rewards" element={<RewardManager />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <Routed />
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
