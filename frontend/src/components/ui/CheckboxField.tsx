type CheckboxFieldProps = {
  checked: boolean;
  label: string;
  onChange: () => void;
};

export function CheckboxField({ checked, label, onChange }: CheckboxFieldProps) {
  return (
    <label className="checkbox-field">
      <input type="checkbox" checked={checked} onChange={onChange} />
      <span className="checkbox-field__box" aria-hidden="true" />
      <span>{label}</span>
    </label>
  );
}
