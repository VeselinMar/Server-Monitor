import { PRESETS, toDateTimeLocal } from "../utils/dates";

export default function TimeRangeSelector({
  preset,
  from,
  to,
  onPreset,
  onFrom,
  onTo,
}) {
  return (
    <div className="time-selector">
      <div className="preset-buttons">
        {PRESETS.map((p) => (
          <button
            key={p.label}
            className={`preset-btn ${
              preset === p.hours ? "active" : ""
            }`}
            onClick={() => onPreset(p.hours)}
          >
            {p.label}
          </button>
        ))}
      </div>

      <div className="custom-range">
        <label>From</label>

        <input
          type="datetime-local"
          value={toDateTimeLocal(from)}
          onChange={(e) => onFrom(new Date(e.target.value))}
        />

        <label>To</label>

        <input
          type="datetime-local"
          value={toDateTimeLocal(to)}
          onChange={(e) => onTo(new Date(e.target.value))}
        />
      </div>
    </div>
  );
}
