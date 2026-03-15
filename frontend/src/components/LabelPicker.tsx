import { useState } from "react";
import clsx from "clsx";

export const LABEL_COLORS: Record<string, { bg: string; text: string }> = {
  bug: { bg: "bg-red-100", text: "text-red-700" },
  feature: { bg: "bg-blue-100", text: "text-blue-700" },
  improvement: { bg: "bg-purple-100", text: "text-purple-700" },
  urgent: { bg: "bg-orange-100", text: "text-orange-700" },
  design: { bg: "bg-pink-100", text: "text-pink-700" },
  backend: { bg: "bg-emerald-100", text: "text-emerald-700" },
  frontend: { bg: "bg-cyan-100", text: "text-cyan-700" },
  docs: { bg: "bg-yellow-100", text: "text-yellow-700" },
};

const PRESET_LABELS = Object.keys(LABEL_COLORS);

type LabelPickerProps = {
  value: string;
  onChange: (value: string) => void;
};

export const LabelPicker = ({ value, onChange }: LabelPickerProps) => {
  const [customLabel, setCustomLabel] = useState("");
  const selected = value ? value.split(",").map((s) => s.trim()).filter(Boolean) : [];
  const customLabels = selected.filter((l) => !PRESET_LABELS.includes(l));

  const toggle = (label: string) => {
    const next = selected.includes(label)
      ? selected.filter((l) => l !== label)
      : [...selected, label];
    onChange(next.join(","));
  };

  const addCustom = () => {
    const trimmed = customLabel.trim().toLowerCase();
    if (trimmed && !selected.includes(trimmed)) {
      onChange([...selected, trimmed].join(","));
    }
    setCustomLabel("");
  };

  return (
    <div className="mt-1.5 space-y-2">
      <div className="flex flex-wrap gap-1.5">
        {PRESET_LABELS.map((label) => {
          const colors = LABEL_COLORS[label];
          const isSelected = selected.includes(label);
          return (
            <button
              key={label}
              type="button"
              onClick={() => toggle(label)}
              className={clsx(
                "rounded-full px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide transition",
                isSelected
                  ? `${colors.bg} ${colors.text} ring-2 ring-current/20`
                  : "bg-gray-50 text-gray-400 hover:bg-gray-100"
              )}
            >
              {label}
            </button>
          );
        })}
      </div>
      {customLabels.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {customLabels.map((label) => (
            <button
              key={label}
              type="button"
              onClick={() => toggle(label)}
              className="rounded-full bg-gray-100 px-2.5 py-0.5 text-[10px] font-semibold text-gray-600 ring-2 ring-gray-300/30 transition hover:bg-gray-200"
            >
              {label} &times;
            </button>
          ))}
        </div>
      )}
      <div className="flex gap-1.5">
        <input
          type="text"
          value={customLabel}
          onChange={(e) => setCustomLabel(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addCustom(); } }}
          placeholder="Custom label..."
          className="flex-1 rounded-lg border border-[var(--stroke)] bg-white px-2.5 py-1 text-xs text-[var(--navy-dark)] outline-none transition focus:border-[var(--primary-blue)]"
        />
        <button
          type="button"
          onClick={addCustom}
          disabled={!customLabel.trim()}
          className="rounded-lg bg-[var(--surface)] px-2.5 py-1 text-xs font-semibold text-[var(--primary-blue)] transition hover:bg-[var(--primary-blue)]/10 disabled:opacity-40"
        >
          Add
        </button>
      </div>
    </div>
  );
};
