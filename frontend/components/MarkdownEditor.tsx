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
        className="input h-72 font-mono"
        placeholder="Markdown урока…"
      />
      <div className="card h-72 overflow-auto p-3">
        <Markdown>{value || "_Предпросмотр появится здесь_"}</Markdown>
      </div>
    </div>
  );
}
