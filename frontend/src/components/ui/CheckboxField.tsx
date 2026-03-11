type CheckboxFieldProps = {
  checked: boolean;
  label: string;
  onChange: () => void;
};

export function CheckboxField({ checked, label, onChange }: CheckboxFieldProps) {
  return (
    <button
      type="button"
      className="checkbox-field"
      role="checkbox"
      aria-checked={checked}
      onClick={onChange}
    >
      <span className={`checkbox-field__box${checked ? " is-checked" : ""}`} aria-hidden="true" />
      <span>{label}</span>
    </button>
  );
}
