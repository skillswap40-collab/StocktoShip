// Sample data for screens whose backend arrives in later steps (products: 5, sales: 7).
// Invented names; no client data.

export interface CatalogItem {
  itemNo: string;
  barcode: string;
  name: string;
  flavor: string;
  size: string;
  priceCents: number;
  taxable: boolean;
}

export const CATALOG: CatalogItem[] = [
  { itemNo: "1001", barcode: "049000028911", name: "Cola Classic 12oz Can", flavor: "Original", size: "24/cs", priceCents: 1499, taxable: true },
  { itemNo: "1002", barcode: "611269991000", name: "Energy Drink 8.4oz", flavor: "Original", size: "24/cs", priceCents: 4299, taxable: true },
  { itemNo: "1003", barcode: "611269101713", name: "Energy Drink Sugar Free 8.4oz", flavor: "Sugar Free", size: "24/cs", priceCents: 4299, taxable: true },
  { itemNo: "2001", barcode: "034000002405", name: "Peanut Butter Cups", flavor: "Milk Chocolate", size: "36/bx", priceCents: 3150, taxable: true },
  { itemNo: "3001", barcode: "011111000001", name: "Bar Soap Original 135g", flavor: "—", size: "48/cs", priceCents: 5280, taxable: true },
  { itemNo: "4001", barcode: "012000001536", name: "Spring Water 16.9oz", flavor: "—", size: "24/cs", priceCents: 599, taxable: false },
];

export const QUICK_PICKS = CATALOG.slice(0, 4);

export type Tender = "Cash" | "Check" | "Debit Card" | "Credit Card" | "Account" | "None";

export interface ReceiptRow {
  id: number;
  date: string;
  time: string;
  status: "Regular" | "Reversed";
  type: "Sales" | "Return";
  workstation: number;
  cashier: string;
  customer: string;
  totalCents: number;
  qty: number;
  payment: Tender;
  items: number;
}

const today = new Date().toLocaleDateString("en-US");

export const SALES_HISTORY: ReceiptRow[] = [
  ["10:05 AM", 1, "Alex", "Harbor Family Market", 45489, "Check"],
  ["10:14 AM", 1, "Alex", "Elm Street Market", 248034, "Check"],
  ["10:19 AM", 1, "Alex", "Riverside Mini Mart", 71960, "Check"],
  ["10:26 AM", 1, "Alex", "Bay Bazaar", 0, "None"],
  ["10:34 AM", 1, "Alex", "Pine Hill Market", 55481, "Cash"],
  ["10:44 AM", 9, "Jordan", "Oak Corner Store", 30278, "Cash"],
  ["3:48 PM", 9, "Jordan", "Landing News & Convenience", 111905, "Debit Card"],
  ["3:59 PM", 1, "Alex", "Mini Stop", 43328, "Cash"],
  ["4:01 PM", 1, "Alex", "Summit Liquors", 122136, "Check"],
  ["4:19 PM", 1, "Alex", "Stop & Go (North)", 441694, "Cash"],
  ["4:29 PM", 9, "Jordan", "Walk-in Driver", 34381, "Debit Card"],
  ["5:00 PM", 1, "Alex", "Sam's Market (Southside)", 209354, "Check"],
].map(([time, ws, cashier, customer, total, payment], i) => ({
  id: i + 1,
  date: today,
  time: time as string,
  status: "Regular",
  type: "Sales",
  workstation: ws as number,
  cashier: cashier as string,
  customer: customer as string,
  totalCents: total as number,
  qty: total === 0 ? 0 : 1,
  payment: payment as Tender,
  items: total === 0 ? 2 : 1,
}));

export const HELD_RECEIPTS: ReceiptRow[] = [
  {
    id: 101, date: today, time: "4:15 PM", status: "Regular", type: "Return", workstation: 10,
    cashier: "Jordan", customer: "Stop & Go (North)", totalCents: -26993, qty: -7,
    payment: "Cash", items: 2,
  },
];
