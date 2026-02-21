// Shared cat color palette — used across charts, activity log, and cat status
// Colors chosen for maximum visual distinction on both light backgrounds and bar charts

export const CAT_NAMES = ["大吉", "小慢", "麻酱", "松花", "小黑"] as const;

export const CAT_COLORS: Record<string, string> = {
  大吉: "#f59e0b", // amber/orange-yellow
  小慢: "#B19379", // warm taupe
  麻酱: "#ef4444", // red
  松花: "#22c55e", // green
  小黑: "#1a1a1a", // black
};
