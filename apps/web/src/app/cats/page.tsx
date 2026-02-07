import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function CatsPage() {
  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Cats</h1>
          <p className="mt-1 text-zinc-500">
            Manage cat profiles and reference photos
          </p>
        </div>
        <Button>Add Cat</Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card className="flex flex-col items-center justify-center border-dashed p-8 text-center">
          <p className="text-sm text-zinc-500">
            No cats added yet. Add your first cat profile to get started.
          </p>
        </Card>
      </div>
    </div>
  );
}
