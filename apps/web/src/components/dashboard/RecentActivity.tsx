import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { MOCK_CATS, FeedingEvent } from "@/lib/mock";
import { formatDistanceToNow } from "date-fns";
import { Utensils, Droplets } from "lucide-react";

interface RecentActivityProps {
    events: FeedingEvent[];
}

export function RecentActivity({ events }: RecentActivityProps) {
    return (
        <Card className="col-span-3">
            <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-8">
                    {events.map((event) => {
                        const cat = MOCK_CATS.find((c) => c.id === event.catId);
                        if (!cat) return null;

                        return (
                            <div key={event.id} className="flex items-center">
                                <Avatar className="h-9 w-9">
                                    <AvatarImage src={cat.avatar} alt={cat.name} />
                                    <AvatarFallback>{cat.name[0]}</AvatarFallback>
                                </Avatar>
                                <div className="ml-4 space-y-1">
                                    <p className="text-sm font-medium leading-none flex items-center gap-2">
                                        {cat.name}
                                        <span className="text-muted-foreground font-normal">
                                            {event.type === 'water' ? 'drank' : 'ate'}
                                        </span>
                                        {event.type === 'water' ? (
                                            <Droplets className="h-3 w-3 text-blue-500" />
                                        ) : (
                                            <Utensils className="h-3 w-3 text-orange-500" />
                                        )}
                                    </p>
                                    <p className="text-xs text-muted-foreground">
                                        {formatDistanceToNow(new Date(event.timestamp), {
                                            addSuffix: true,
                                        })}
                                    </p>
                                </div>
                                <div className="ml-auto font-medium">
                                    +{event.amount}{event.type === 'water' ? 'ml' : 'g'}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </CardContent>
        </Card>
    );
}
