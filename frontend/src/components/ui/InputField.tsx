import type { InputHTMLAttributes } from "react";

type InputFieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  error?: string;
};

export function InputField({ label, error, id, ...props }: InputFieldProps) {
  return (
    <label className="input-group" htmlFor={id}>
      <span className="input-label">{label}</span>
      <input className="input-control" id={id} {...props} />
      {error ? <span className="input-error">{error}</span> : null}
    </label>
  );
}
