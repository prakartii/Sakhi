import { type FormEvent, type KeyboardEvent } from "react";
import { Loader2, Send, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import type { WebsiteChatMessage } from "@/lib/types";

/**
 * Website-Studio-page-only chat pieces, built on the shared design tokens.
 * Not imported anywhere else — safe to iterate on without touching the
 * rest of the app.
 */

export function ChatBubble({ message }: { message: WebsiteChatMessage }) {
  const isUser = message.role === "user";
  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[85%] rounded-2xl px-4 py-2.5 text-[13px] leading-relaxed",
          isUser ? "bg-primary text-primary-foreground" : "card-soft bg-card text-foreground/85",
        )}
      >
        {!isUser && (
          <span className="mb-1 flex items-center gap-1 text-[10px] font-semibold tracking-[0.14em] text-wine uppercase">
            <Sparkles className="h-2.5 w-2.5" /> Sakhi
          </span>
        )}
        {message.content}
      </div>
    </div>
  );
}

export function ChatThinkingBubble() {
  return (
    <div className="flex justify-start">
      <div className="card-soft flex items-center gap-2 rounded-2xl bg-card px-4 py-2.5 text-[12px] text-muted-foreground">
        <Loader2 className="h-3.5 w-3.5 animate-spin" /> Sakhi is working on it…
      </div>
    </div>
  );
}

export function ChatComposer({
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
  function submit() {
    if (!disabled && value.trim()) onSubmit();
  }
  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    submit();
  }
  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit();
    }
  }
  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-2 border-t border-clay/15 p-3">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        rows={1}
        disabled={disabled}
        className="max-h-28 flex-1 resize-none rounded-xl border border-clay/25 bg-card px-3.5 py-2.5 text-[13px] text-foreground placeholder:text-muted-foreground focus:border-wine/40 focus:outline-none disabled:opacity-60"
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-primary text-primary-foreground transition-transform hover:scale-105 disabled:pointer-events-none disabled:opacity-50"
        aria-label="Send"
      >
        {disabled ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
      </button>
    </form>
  );
}
