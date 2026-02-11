"use client";

import { Plus } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { Progress } from "@/components/ui/progress";

interface PageUsageDisplayProps {
	pagesUsed: number;
	pagesLimit: number;
}

const UNLIMITED_PAGES_LIMIT = 999_999_999;

export function PageUsageDisplay({ pagesUsed, pagesLimit }: PageUsageDisplayProps) {
	const params = useParams();
	const searchSpaceId = params.search_space_id;
	const isUnlimited = pagesLimit >= UNLIMITED_PAGES_LIMIT;
	const usagePercentage =
		!isUnlimited && pagesLimit > 0 ? Math.min(100, (pagesUsed / pagesLimit) * 100) : 0;

	return (
		<div className="px-3 py-3 border-t">
			<div className="space-y-2">
				<div className="flex justify-between items-center text-xs">
					<span className="text-muted-foreground">
						{isUnlimited
							? `${pagesUsed.toLocaleString()} / Unlimited pages`
							: `${pagesUsed.toLocaleString()} / ${pagesLimit.toLocaleString()} pages`}
					</span>
					{!isUnlimited && <span className="font-medium">{usagePercentage.toFixed(0)}%</span>}
				</div>
				{!isUnlimited && <Progress value={usagePercentage} className="h-1.5" />}
				{!isUnlimited && (
					<Link
						href={`/dashboard/${searchSpaceId}/more-pages`}
						className="flex items-center gap-1.5 text-[10px] text-muted-foreground hover:text-primary transition-colors"
					>
						<Plus className="h-3 w-3 shrink-0" />
						<span>Get More Pages</span>
					</Link>
				)}
			</div>
		</div>
	);
}
