import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Cat } from "@/lib/mock";
import { formatDistanceToNow } from "date-fns";
import { Utensils } from "lucide-react";

interface CatCardProps {
    cat: Cat;
}

export function CatCard({ cat }: CatCardProps) {
    return (
        <Card className="overflow-hidden">
            <div className="h-24 bg-gradient-to-r from-zinc-100 to-zinc-200 dark:from-zinc-800 dark:to-zinc-900" />
            <CardHeader className="-mt-12 relative z-10 flex flex-row items-end justify-between">
                <Avatar className="h-24 w-24 border-4 border-white dark:border-zinc-950">
                    <AvatarImage src={cat.avatar} alt={cat.name} className="object-cover" />
                    <AvatarFallback>{cat.name[0]}</AvatarFallback>
                </Avatar>
                <div className="mb-1">
                    {cat.status === 'eating' && <Badge variant="default" className="bg-emerald-500 hover:bg-emerald-600">Eating Now</Badge>}
                    {cat.status === 'hungry' && <Badge variant="destructive">Hungry</Badge>}
                    {cat.status === 'fed' && <Badge variant="secondary">Fed</Badge>}
                </div>
            </CardHeader>
            <CardContent className="space-y-4">
                <div>
                    <CardTitle className="text-2xl">{cat.name}</CardTitle>
                    <p className="text-sm text-muted-foreground">{cat.breed}</p>
                </div>
                <p className="text-sm text-muted-foreground line-clamp-2">
                    {cat.description}
                </p>
                <div className="flex items-center text-sm text-muted-foreground">
                    <Utensils className="mr-2 h-4 w-4" />
                    Last fed {formatDistanceToNow(new Date(cat.lastFedTime), { addSuffix: true })}
                </div>
            </CardContent>
            <CardFooter>
                <Button className="w-full" variant="outline">View History</Button>
            </CardFooter>
        </Card>
    );
}
