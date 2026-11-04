// Same matrix as the README "Permissions" table. The backend enforces it; the UI only hides
// what a role can't use.
import type { Role } from "./types";

const ROLES: Record<string, Role[]> = {
  registerCustomer: ["admin", "manager", "sales_rep", "cashier"],
  editCustomer: ["admin", "manager"],
  changeTaxId: ["admin"],
  revealTaxId: ["admin"],
  viewStaff: ["admin", "manager"],
  manageStaff: ["admin"],
};

export type Permission = keyof typeof ROLES;
export const can = (role: Role | undefined, p: Permission) => !!role && ROLES[p].includes(role);

export const ROLE_LABELS: Record<Role, string> = {
  admin: "Admin",
  manager: "Manager",
  sales_rep: "Sales rep",
  cashier: "Cashier",
  warehouse: "Warehouse",
};
