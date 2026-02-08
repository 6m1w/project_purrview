import { MOCK_CATS } from "@/lib/mock";
import { CatCard } from "@/components/dashboard/CatCard";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

export default function CatsPage() {
  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight">My Cats</h2>
        <Button>
          <Plus className="mr-2 h-4 w-4" /> Add Cat
        </Button>
      </div>
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {MOCK_CATS.map((cat) => (
          <CatCard key={cat.id} cat={cat} />
        ))}
      </div>
    </div>
  );
}
