import { Cat } from "lucide-react";

export default function CatsPage() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-8 gap-6">
      <Cat className="h-16 w-16" />
      <h2 className="font-vt323 text-5xl uppercase tracking-widest">
        Cat Profiles
      </h2>
      <p className="font-space-mono text-sm font-bold uppercase text-black/50">
        Coming soon — individual cat stats &amp; history
      </p>
    </div>
  );
}
