const usd = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });

/** Money is handled in integer cents on the client, never floats. */
export const money = (cents: number) => usd.format(cents / 100);

export const dateTime = (iso: string) =>
  new Date(iso).toLocaleString("en-US", { dateStyle: "medium", timeStyle: "short" });

export const STATUS_LABELS = { active: "Active", on_hold: "On hold", inactive: "Inactive" };
