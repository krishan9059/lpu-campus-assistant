import { useRef, type FormEvent, type KeyboardEvent } from "react";
import { ArrowUp } from "lucide-react";

import { useAutoResizeTextarea } from "@/hooks/useAutoResizeTextarea";

import "./Composer.css";

export function Composer({
  value,
  onChange,
  onSubmit,
  disabled,
  placeholder,
}: {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled: boolean;
  placeholder: string;
}) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  useAutoResizeTextarea(textareaRef, value);

  const canSend = value.trim().length > 0 && !disabled;

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (canSend) onSubmit();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (canSend) onSubmit();
    }
  };

  return (
    <form className="composer" onSubmit={handleSubmit}>
      <textarea
        ref={textareaRef}
        className="composer-input"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        rows={1}
        maxLength={1000}
        aria-label="Message"
      />
      <button type="submit" className="composer-send" disabled={!canSend} aria-label="Send message">
        <ArrowUp size={18} aria-hidden="true" />
      </button>
    </form>
  );
}
