import { useState, useEffect } from "react";
import { settings } from "../api/client";

const FIELDS = {
  subscriber: {
    label: "Subscriber Details",
    sub: "Used in the PDF complaint report",
    fields: [
      { key: "subscriber_name",           label: "Full Name",       type: "text" },
      { key: "subscriber_address",        label: "Address",         type: "text" },
      { key: "subscriber_account_number", label: "Account Number",  type: "text" },
      { key: "subscriber_email",          label: "Email",           type: "email" },
      { key: "subscriber_phone",          label: "Phone",           type: "text" },
      { key: "subscriber_provider",       label: "Provider",        type: "text" },
      { key: "subscriber_plan",           label: "Plan Name",       type: "text" },
    ],
  },
  thresholds: {
    label: "Service Thresholds",
    sub: "Used to classify speedtest results",
    fields: [
      { key: "contracted_download_mbps", label: "Contracted Download (Mbps)", type: "number", hint: "Your plan's advertised speed" },
      { key: "contracted_upload_mbps",   label: "Contracted Upload (Mbps)",   type: "number", hint: "0 if unknown" },
      { key: "download_degraded_mbps",   label: "Degraded Download (Mbps)",   type: "number", hint: "Auto-derived as 50% of contracted" },
      { key: "download_critical_mbps",   label: "Critical Download (Mbps)",   type: "number", hint: "Auto-derived as 20% of contracted" },
      { key: "upload_degraded_mbps",     label: "Degraded Upload (Mbps)",     type: "number", hint: "Below this = degraded" },
      { key: "upload_critical_mbps",     label: "Critical Upload (Mbps)",     type: "number", hint: "Below this = critical" },
    ],
  },
};

export default function SettingsModal({ onClose }) {
  const [values, setValues]   = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving]   = useState(false);
  const [saved, setSaved]     = useState(false);
  const [error, setError]     = useState(null);

  useEffect(() => {
    settings.get().then((data) => {
      setValues(data);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  function handleChange(key, val) {
    setValues((prev) => ({ ...prev, [key]: val }));
    setSaved(false);
  }

  function deriveThresholds(contractedDownload) {
    const dl = parseFloat(contractedDownload) || 0;
    setValues((prev) => ({
      ...prev,
      download_degraded_mbps: (dl * 0.5).toFixed(1),
      download_critical_mbps: (dl * 0.2).toFixed(1),
    }));
    setSaved(false);
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      await settings.save(values);
      setSaved(true);
      setTimeout(onClose, 600);
    } catch (e) {
      setError("Failed to save settings.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">Settings</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        {loading ? (
          <div className="loading-state">Loading settings…</div>
        ) : (
          <div className="modal-body">
            {Object.entries(FIELDS).map(([sectionKey, section]) => (
              <div key={sectionKey} className="settings-section">
                <div className="settings-section-header">
                  <h3 className="settings-section-title">{section.label}</h3>
                  <span className="settings-section-sub">{section.sub}</span>
                </div>

                {sectionKey === "thresholds" && (
                  <button
                    className="derive-btn"
                    onClick={() => deriveThresholds(values["contracted_download_mbps"])}
                  >
                    Auto-derive from contracted speed
                  </button>
                )}

                <div className="settings-fields">
                  {section.fields.map((f) => (
                    <div key={f.key} className="settings-field">
                      <label className="settings-label">
                        {f.label}
                        {f.hint && <span className="settings-hint"> — {f.hint}</span>}
                      </label>
                      <input
                        className="settings-input"
                        type={f.type}
                        value={values[f.key] ?? ""}
                        onChange={(e) => handleChange(f.key, e.target.value)}
                        step={f.type === "number" ? "0.1" : undefined}
                      />
                    </div>
                  ))}
                </div>
              </div>
            ))}

            {error && <p className="settings-error">{error}</p>}
          </div>
        )}

        <div className="modal-footer">
          {saved && <span className="settings-saved">Settings saved ✓</span>}
          <button className="preset-btn" onClick={onClose}>Cancel</button>
          <button
            className={`ingest-btn ${saving ? "loading" : ""}`}
            onClick={handleSave}
            disabled={saving || loading}
          >
            {saving ? "Saving…" : "Save Settings"}
          </button>
        </div>
      </div>
    </div>
  );
}