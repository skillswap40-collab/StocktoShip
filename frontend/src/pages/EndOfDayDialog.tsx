import { useState } from "react";
import { Modal, useToast } from "../components/ui";

export default function EndOfDayDialog({ onClose }: { onClose: () => void }) {
  const toast = useToast();
  const [runReport, setRunReport] = useState(true);
  const [report, setReport] = useState("z-out");
  const [period, setPeriod] = useState("today");
  const [printNow, setPrintNow] = useState(false);

  return (
    <Modal
      title="End of Day"
      onClose={onClose}
      footer={
        <>
          <button className="btn" onClick={onClose}>Cancel</button>
          <button
            className="btn primary"
            disabled={!runReport}
            onClick={() => {
              toast("End of Day reports arrive with payments in Step 8.");
              onClose();
            }}
          >
            Start
          </button>
        </>
      }
    >
      <p className="muted" style={{ margin: 0 }}>
        Run the closing procedures for this register. Checked options run together.
      </p>
      <label className="check">
        <input type="checkbox" checked={runReport} onChange={(e) => setRunReport(e.target.checked)} />
        <strong>Run End of Day report</strong>
      </label>
      <div className="form-grid" style={{ paddingLeft: 24, opacity: runReport ? 1 : 0.5 }}>
        <div className="field span-4">
          <label htmlFor="eod-report">Report</label>
          <select id="eod-report" className="select input" value={report} disabled={!runReport}
            onChange={(e) => setReport(e.target.value)}>
            <option value="z-out">Z-Out: drawer count and close</option>
            <option value="x-out">X-Out: mid-day snapshot</option>
          </select>
        </div>
        <div className="field span-2">
          <label htmlFor="eod-period">For</label>
          <select id="eod-period" className="select input" value={period} disabled={!runReport}
            onChange={(e) => setPeriod(e.target.value)}>
            <option value="today">Today</option>
            <option value="yesterday">Yesterday</option>
          </select>
        </div>
        <label className="check span-6">
          <input type="checkbox" checked={printNow} disabled={!runReport}
            onChange={(e) => setPrintNow(e.target.checked)} />
          Print immediately (skip preview)
        </label>
      </div>
      <div className="notice info">
        Backups are no longer a register task: the server database is backed up centrally.
      </div>
    </Modal>
  );
}
