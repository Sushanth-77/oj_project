"use client";

import { useQuery } from "@tanstack/react-query";
import { useSession } from "next-auth/react";
import Link from "next/link";
import { BookOpen, CheckCircle, Circle, ArrowRight, TrendingUp } from "lucide-react";

interface CollectionProblem {
  id: number;
  order: number;
  solved: boolean;
  problem: {
    id: number;
    name: string;
    shortCode: string;
    difficulty: string;
    topics: string[];
  };
}

interface Collection {
  id: number;
  title: string;
  description: string | null;
  slug: string;
  problemCount: number;
}

const DIFF_CONFIG: Record<string, { label: string; color: string }> = {
  E: { label: "Easy",   color: "text-green-400"  },
  M: { label: "Medium", color: "text-yellow-400" },
  H: { label: "Hard",   color: "text-red-400"    },
};

function CollectionCard({ collection }: { collection: Collection }) {
  return (
    <Link
      href={`/collections/${collection.slug}`}
      className="group bg-[#1a1f29] border border-[#2d3748] rounded-xl p-6 hover:border-[#00d4aa]/40 transition-all hover:shadow-lg hover:shadow-[#00d4aa]/5 block"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="p-2.5 bg-[#00d4aa]/10 rounded-lg">
          <BookOpen className="w-5 h-5 text-[#00d4aa]" />
        </div>
        <ArrowRight className="w-5 h-5 text-gray-600 group-hover:text-[#00d4aa] group-hover:translate-x-1 transition-all" />
      </div>
      <h3 className="text-lg font-bold text-white mb-2 group-hover:text-[#00d4aa] transition-colors">
        {collection.title}
      </h3>
      {collection.description && (
        <p className="text-gray-400 text-sm mb-4 line-clamp-2">{collection.description}</p>
      )}
      <div className="flex items-center gap-1.5 text-xs text-gray-500">
        <TrendingUp className="w-3.5 h-3.5" />
        {collection.problemCount} problems
      </div>
    </Link>
  );
}

export default function CollectionsPage() {
  const { data: collections = [], isLoading } = useQuery<Collection[]>({
    queryKey: ["collections"],
    queryFn: async () => {
      const res = await fetch("/api/collections");
      if (!res.ok) return [];
      return res.json();
    },
    staleTime: 60_000,
  });

  return (
    <div className="min-h-screen bg-[#0f1419]">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="mb-8 text-center">
          <div className="inline-flex items-center gap-3 mb-3">
            <BookOpen className="w-8 h-8 text-[#00d4aa]" />
            <h1 className="text-4xl font-bold text-white">Study Collections</h1>
          </div>
          <p className="text-gray-400">Curated problem sets to guide your learning journey</p>
        </div>

        {isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-44 bg-[#1a1f29] rounded-xl animate-pulse border border-[#2d3748]" />
            ))}
          </div>
        ) : collections.length === 0 ? (
          <div className="text-center py-20">
            <BookOpen className="w-12 h-12 text-gray-600 mx-auto mb-3" />
            <p className="text-gray-400">No collections yet. Check back soon!</p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {collections.map((c) => (
              <CollectionCard key={c.id} collection={c} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
