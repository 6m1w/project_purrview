import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ReportsPage() {
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Reports</h1>
        <p className="mt-1 text-zinc-500">
          Daily and weekly feeding statistics
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Daily Summary</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-zinc-500">
              Charts will appear here once feeding data is collected.
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Per-Cat Intake</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-zinc-500">
              Per-cat food consumption trends over time.
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
