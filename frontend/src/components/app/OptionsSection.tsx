import type { AnonymizeOptions } from "../../lib/api";
import { optionLabels } from "../../constants/anonymize";
import { AppCard } from "../ui/AppCard";
import { CheckboxField } from "../ui/CheckboxField";

type OptionsSectionProps = {
  options: AnonymizeOptions;
  onToggle: (key: keyof AnonymizeOptions) => void;
  busy?: boolean;
};

export function OptionsSection({ options, onToggle, busy = false }: OptionsSectionProps) {
  return (
    <AppCard title="Настройки анонимизации">
      <div className="options-grid">
        {optionLabels.map((option) => (
          <CheckboxField
            key={option.key}
            checked={busy ? false : options[option.key]}
            label={option.label}
            onChange={() => onToggle(option.key)}
          />
        ))}
      </div>
    </AppCard>
  );
}
