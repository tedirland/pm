import clsx from "clsx";
import { LABEL_COLORS } from "@/components/LabelPicker";

type CardLabelsProps = {
  labels: string;
};

export const CardLabels = ({ labels }: CardLabelsProps) => {
  const items = labels.split(",").map((s) => s.trim()).filter(Boolean);
  if (items.length === 0) return null;

  return (
    <div className="mb-2 flex flex-wrap gap-1">
      {items.map((label) => {
        const colors = LABEL_COLORS[label];
        return (
          <span
            key={label}
            className={clsx(
              "rounded-full px-2 py-0.5 text-[9px] font-bold uppercase tracking-wide",
              colors ? `${colors.bg} ${colors.text}` : "bg-gray-100 text-gray-500"
            )}
          >
            {label}
          </span>
        );
      })}
    </div>
  );
};
