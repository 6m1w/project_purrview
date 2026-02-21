import { Clock } from "lucide-react";

export default function TimelinePage() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8 gap-6">
      <Clock className="h-16 w-16" />
      <h2 className="font-vt323 text-5xl uppercase tracking-widest">
        Feeding Timeline
      </h2>
      <p className="font-space-mono text-sm font-bold uppercase text-black/50">
        Coming soon — full event history with filters
      </p>
    </div>
  );
}
