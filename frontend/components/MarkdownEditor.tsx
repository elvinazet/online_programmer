"use client";
import Markdown from "./Markdown";

export default function MarkdownEditor({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-72 w-full rounded border border-slate-300 p-3 font-mono text-sm"
        placeholder="Markdown урока…"
      />
      <div className="h-72 overflow-auto rounded border border-slate-200 p-3">
        <Markdown>{value || "_Предпросмотр появится здесь_"}</Markdown>
      </div>
    </div>
  );
}
