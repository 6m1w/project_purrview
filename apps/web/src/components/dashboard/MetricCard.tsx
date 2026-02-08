import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface MetricCardProps {
    title: string;
    value: string | number;
    description?: string;
    icon?: React.ReactNode;
    trend?: "up" | "down" | "neutral";
    trendValue?: string;
    className?: string;
}

export function MetricCard({
    title,
    value,
    description,
    icon,
    trend,
    trendValue,
    className,
}: MetricCardProps) {
    return (
        <Card className={cn("shadow-sm", className)}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                    {title}
                </CardTitle>
                {icon && <div className="text-muted-foreground">{icon}</div>}
            </CardHeader>
            <CardContent>
                <div className="text-2xl font-bold">{value}</div>
                {(description || trendValue) && (
                    <p className="text-xs text-muted-foreground mt-1">
                        {trendValue && (
                            <span
                                className={cn(
                                    "mr-1 font-medium",
                                    trend === "up" && "text-emerald-600",
                                    trend === "down" && "text-red-600"
                                )}
                            >
                                {trendValue}
                            </span>
                        )}
                        {description}
                    </p>
                )}
            </CardContent>
        </Card>
    );
}
