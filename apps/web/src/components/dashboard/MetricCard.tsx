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
        <div className={cn("border-4 border-black bg-white shadow-[8px_8px_0_0_rgba(0,0,0,1)] transition-transform hover:-translate-y-1 hover:shadow-[12px_12px_0_0_rgba(0,0,0,1)]", className)}>
            <div className="flex flex-row items-center justify-between p-6 pb-2">
                <h3 className="font-press-start text-sm font-bold uppercase text-black">
                    {title}
                </h3>
                {icon && <div className="text-black">{icon}</div>}
            </div>
            <div className="p-6 pt-0">
                <div className="font-press-start text-2xl font-bold">{value}</div>
                {(description || trendValue) && (
                    <p className="font-space-mono text-xs font-bold text-black/70 mt-2 uppercase">
                        {trendValue && (
                            <span
                                className={cn(
                                    "mr-2 px-1 border-2 border-black",
                                    trend === "up" && "bg-[#00FF66] text-black",
                                    trend === "down" && "bg-[#FF5722] text-black"
                                )}
                            >
                                {trendValue}
                            </span>
                        )}
                        {description}
                    </p>
                )}
            </div>
        </div>
    );
}
