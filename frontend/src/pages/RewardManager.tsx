// Shown because the old POS has it, but customer rewards are not in the build plan.
// Read-only until the client confirms they want it.
import { Gift, ListChecks, ScrollText } from "lucide-react";
import { Page } from "../components/ui";

export default function RewardManager() {
  return (
    <Page
      title="Reward Manager"
      sub={<span className="tag">Not in current plan</span>}
      actions={[
        { label: "Member List", icon: ListChecks, later: "TBD" },
        { label: "Redemption History", icon: ScrollText, later: "TBD" },
      ]}
    >
      <div className="notice info">
        The current POS has rewards switched off. Confirm with the client whether wholesale
        customers need a rewards program before this is built.
      </div>
      <div className="cards-2" style={{ maxWidth: 900 }}>
        <fieldset className="card" disabled style={{ padding: 0, margin: 0 }}>
          <div className="card-head"><Gift size={16} />Reward setup</div>
          <div className="card-body form-grid">
            <div className="field span-3"><label>Purchase threshold</label><input className="input" value="$0.00" readOnly /></div>
            <div className="field span-3"><label>Reward amount</label><input className="input" value="$0.00" readOnly /></div>
            <div className="field span-3"><label>Reward expires after</label><select className="input select"><option>30 days</option></select></div>
            <div className="field span-3"><label>Tracking period</label><input className="input" value="No end date" readOnly /></div>
          </div>
        </fieldset>
        <fieldset className="card" disabled style={{ padding: 0, margin: 0 }}>
          <div className="card-head">Program status</div>
          <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            <div><span className="tag on_hold">Tracking off</span></div>
            <label className="check"><input type="checkbox" />Automatically enroll new customers</label>
            <label className="check"><input type="checkbox" />Prompt to enroll non-members at sale</label>
            <label className="check"><input type="checkbox" defaultChecked />Tell the cashier when a reward is earned</label>
          </div>
        </fieldset>
      </div>
    </Page>
  );
}
