import { redirect } from "next/navigation";

// Reports content has been merged into the Dashboard page
export default function ReportsPage() {
  redirect("/dashboard#analytics");
}
