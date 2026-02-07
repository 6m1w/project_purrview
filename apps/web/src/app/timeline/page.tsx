import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function TimelinePage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Feeding Timeline</h1>
        <p className="mt-1 text-zinc-500">
          Today&apos;s feeding events with captured frames
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Today</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-zinc-500">
            No feeding events recorded today.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
