// Mirrors backend/app/modules/*/schemas.py

export type Role = "admin" | "manager" | "sales_rep" | "cashier" | "warehouse";
export type CustomerStatus = "active" | "on_hold" | "inactive";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface CustomerListItem {
  id: number;
  account_number: string;
  business_name: string;
  owner_name: string;
  tax_id_masked: string;
  city: string;
  state: string;
  phone: string | null;
  status: CustomerStatus;
}

export interface Customer extends CustomerListItem {
  address_line1: string;
  address_line2: string | null;
  postal_code: string;
  email: string | null;
  notes: string | null;
  registered_by_user_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface CustomerPage {
  items: CustomerListItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface TaxIdReveal {
  customer_id: number;
  account_number: string;
  tax_id: string;
}
