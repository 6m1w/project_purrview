import type { Metadata } from "next";
import { getCatProfiles } from "@/lib/queries";

export const metadata: Metadata = {
  title: "Cat Profiles",
  description: "Meet the 5 rescue cats — Majiang, Songhua, Xiaohei, Daji, and Xiaoman — with feeding stats and personality bios.",
};
import { CatProfileCard } from "@/components/cats/CatProfileCard";

export const dynamic = "force-dynamic";

export default async function CatsPage() {
  const profiles = await getCatProfiles();

  return (
    <div className="flex flex-col space-y-8 p-4 pt-6 max-w-[1600px] mx-auto">
      <section className="flex flex-col space-y-6">
        {/* Page header — brutalist style matching dashboard */}
        <div className="flex items-center justify-between border-b-4 border-black pb-2">
          <h2 className="font-press-start text-2xl md:text-3xl font-bold uppercase">
            Cat Profiles
          </h2>
          <div className="font-press-start text-sm font-bold bg-black text-[#00FF66] px-3 py-1.5 border-2 border-black">
            5 CATS
          </div>
        </div>

        {/* Profile cards grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {profiles.map((profile) => (
            <CatProfileCard key={profile.name} profile={profile} />
          ))}
        </div>
      </section>
    </div>
  );
}
