import { MOCK_FEEDING_EVENTS, MOCK_CATS } from "@/lib/mock";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { format } from "date-fns";
import { Utensils, Droplets } from "lucide-react";

export default function HistoryPage() {
  // Sort events by date descending
  const sortedEvents = [...MOCK_FEEDING_EVENTS].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">Feeding History</h2>
      </div>
      <div className="space-y-4">
        {sortedEvents.map((event) => {
          const cat = MOCK_CATS.find((c) => c.id === event.catId);
          if (!cat) return null;

          return (
            <Card key={event.id}>
              <CardHeader className="flex flex-row items-center gap-4 space-y-0">
                <Avatar className="h-12 w-12">
                  <AvatarImage src={cat.avatar} alt={cat.name} />
                  <AvatarFallback>{cat.name[0]}</AvatarFallback>
                </Avatar>
                <div className="grid gap-1">
                  <CardTitle>{cat.name}</CardTitle>
                  <p className="text-sm text-muted-foreground">
                    {format(new Date(event.timestamp), "PPpp")}
                  </p>
                </div>
                <div className="ml-auto flex items-center gap-4">
                  <Badge variant="outline" className="text-lg py-1 px-3 flex items-center gap-2">
                    {event.type === 'water' ? <Droplets className="h-4 w-4 text-blue-500" /> : <Utensils className="h-4 w-4 text-orange-500" />}
                    {event.amount}{event.type === 'water' ? 'ml' : 'g'}
                  </Badge>
                  <p className="text-sm text-muted-foreground">
                    Duration: {Math.round(event.duration / 60)} min
                  </p>
                </div>
              </CardHeader>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
