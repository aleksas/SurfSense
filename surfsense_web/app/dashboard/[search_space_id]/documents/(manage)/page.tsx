"use client";

import { useQuery } from "@tanstack/react-query";
import { useAtomValue } from "jotai";
import { motion } from "motion/react";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { deleteDocumentMutationAtom } from "@/atoms/documents/document-mutation.atoms";
import type { DocumentTypeEnum } from "@/contracts/types/document.types";
import { documentsApiService } from "@/lib/apis/documents-api.service";
import { cacheKeys } from "@/lib/query-client/cache-keys";
import { DocumentsFilters } from "./components/DocumentsFilters";
import { DocumentsTableShell, type SortKey } from "./components/DocumentsTableShell";
import { PAGE_SIZE, PaginationControls } from "./components/PaginationControls";
import type { ColumnVisibility, Document } from "./components/types";

function useDebounced<T>(value: T, delay = 250) {
	const [debounced, setDebounced] = useState(value);
	useEffect(() => {
		const t = setTimeout(() => setDebounced(value), delay);
		return () => clearTimeout(t);
	}, [value, delay]);
	return debounced;
}

export default function DocumentsTable() {
	const t = useTranslations("documents");
	const params = useParams();
	const searchSpaceId = Number(params.search_space_id);

	const [search, setSearch] = useState("");
	const debouncedSearch = useDebounced(search, 250);
	const [activeTypes, setActiveTypes] = useState<DocumentTypeEnum[]>([]);
	const [columnVisibility, setColumnVisibility] = useState<ColumnVisibility>({
		document_type: true,
		created_by: true,
		created_at: true,
		status: true,
	});
	const [pageIndex, setPageIndex] = useState(0);
	const [sortKey, setSortKey] = useState<SortKey>("created_at");
	const [sortDesc, setSortDesc] = useState(true);
	const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
	const { mutateAsync: deleteDocumentMutation } = useAtomValue(deleteDocumentMutationAtom);

	const isSearchMode = !!debouncedSearch.trim();

	const { data: typeCounts = {}, isLoading: typeCountsLoading } = useQuery({
		queryKey: cacheKeys.documents.typeCounts(String(searchSpaceId)),
		queryFn: () =>
			documentsApiService.getDocumentTypeCounts({
				queryParams: { search_space_id: searchSpaceId },
			}),
		staleTime: 30 * 1000,
		enabled: !!searchSpaceId,
	});

	const listQueryParams = useMemo(
		() => ({
			search_space_id: searchSpaceId,
			page: pageIndex,
			page_size: PAGE_SIZE,
			...(activeTypes.length > 0 && { document_types: activeTypes }),
		}),
		[searchSpaceId, pageIndex, activeTypes]
	);

	const {
		data: listResponse,
		isLoading: isListLoading,
		refetch: refetchList,
		error: listError,
	} = useQuery({
		queryKey: cacheKeys.documents.globalQueryParams(listQueryParams),
		queryFn: () => documentsApiService.getDocuments({ queryParams: listQueryParams }),
		staleTime: 30 * 1000,
		enabled: !!searchSpaceId && !isSearchMode,
	});

	const searchQueryParams = useMemo(
		() => ({
			search_space_id: searchSpaceId,
			page: pageIndex,
			page_size: PAGE_SIZE,
			title: debouncedSearch.trim(),
			...(activeTypes.length > 0 && { document_types: activeTypes }),
		}),
		[searchSpaceId, pageIndex, activeTypes, debouncedSearch]
	);

	const {
		data: searchResponse,
		isLoading: isSearchLoading,
		refetch: refetchSearch,
		error: searchError,
	} = useQuery({
		queryKey: cacheKeys.documents.globalQueryParams(searchQueryParams),
		queryFn: () => documentsApiService.searchDocuments({ queryParams: searchQueryParams }),
		staleTime: 30 * 1000,
		enabled: !!searchSpaceId && isSearchMode,
	});

	const { documents, total, loading, error } = useMemo(() => {
		const response = isSearchMode ? searchResponse : listResponse;
		const items = response?.items || [];
		const docs: Document[] = items.map((item) => ({
			id: item.id,
			title: item.title,
			document_type: item.document_type,
			document_metadata: item.document_metadata,
			content: item.content,
			created_at: item.created_at,
			search_space_id: item.search_space_id,
			created_by_id: item.created_by_id ?? null,
			created_by_name: item.created_by_name ?? null,
			status: (item as { status?: Document["status"] }).status,
		}));

		return {
			documents: docs,
			total: response?.total || 0,
			loading: isSearchMode ? isSearchLoading : isListLoading,
			error: isSearchMode ? searchError : listError,
		};
	}, [
		isSearchMode,
		searchResponse,
		listResponse,
		isSearchLoading,
		isListLoading,
		searchError,
		listError,
	]);

	const pageEnd = Math.min((pageIndex + 1) * PAGE_SIZE, total);

	const onToggleType = (type: DocumentTypeEnum, checked: boolean) => {
		setActiveTypes((prev) => {
			if (checked) return prev.includes(type) ? prev : [...prev, type];
			return prev.filter((t) => t !== type);
		});
		setPageIndex(0);
	};

	const onBulkDelete = async () => {
		if (selectedIds.size === 0) {
			toast.error(t("no_rows_selected"));
			return;
		}

		const selectedDocs = documents.filter((doc) => selectedIds.has(doc.id));
		const deletableIds = selectedDocs
			.filter((doc) => doc.status?.state !== "pending" && doc.status?.state !== "processing")
			.map((doc) => doc.id);
		const inProgressCount = selectedIds.size - deletableIds.length;

		if (inProgressCount > 0) {
			toast.warning(
				`${inProgressCount} document(s) are pending or processing and cannot be deleted.`
			);
		}
		if (deletableIds.length === 0) return;

		try {
			let conflictCount = 0;
			const results = await Promise.all(
				deletableIds.map(async (id) => {
					try {
						await deleteDocumentMutation({ id });
						return true;
					} catch (err: unknown) {
						const status =
							(err as { response?: { status?: number } })?.response?.status ??
							(err as { status?: number })?.status;
						if (status === 409) conflictCount++;
						return false;
					}
				})
			);

			const okCount = results.filter(Boolean).length;
			if (okCount === deletableIds.length) toast.success(t("delete_success_count", { count: okCount }));
			else if (conflictCount > 0)
				toast.error(`${conflictCount} document(s) started processing. Please try again later.`);
			else toast.error(t("delete_partial_failed"));

			if (isSearchMode) await refetchSearch();
			else await refetchList();

			setSelectedIds(new Set());
		} catch (e) {
			console.error(e);
			toast.error(t("delete_error"));
		}
	};

	const handleDeleteDocument = useCallback(
		async (id: number): Promise<boolean> => {
			try {
				await deleteDocumentMutation({ id });
				toast.success(t("delete_success") || "Document deleted");
				if (isSearchMode) await refetchSearch();
				else await refetchList();
				return true;
			} catch (e) {
				console.error("Error deleting document:", e);
				return false;
			}
		},
		[deleteDocumentMutation, isSearchMode, refetchSearch, refetchList, t]
	);

	const handleSortChange = useCallback((key: SortKey) => {
		setSortKey((currentKey) => {
			if (currentKey === key) {
				setSortDesc((v) => !v);
				return currentKey;
			}
			setSortDesc(false);
			return key;
		});
	}, []);

	// Reset page + selection when search changes.
	// biome-ignore lint/correctness/useExhaustiveDependencies: intended
	useEffect(() => {
		setPageIndex(0);
		setSelectedIds(new Set());
	}, [debouncedSearch]);

	// Keep selection scoped to visible docs.
	useEffect(() => {
		setSelectedIds(new Set());
	}, [pageIndex, activeTypes, isSearchMode]);

	useEffect(() => {
		const mq = window.matchMedia("(max-width: 768px)");
		const apply = (isSmall: boolean) => {
			setColumnVisibility((prev) => ({ ...prev, created_by: !isSmall, created_at: !isSmall }));
		};
		apply(mq.matches);
		const onChange = (e: MediaQueryListEvent) => apply(e.matches);
		mq.addEventListener("change", onChange);
		return () => mq.removeEventListener("change", onChange);
	}, []);

	return (
		<motion.div
			initial={{ opacity: 0, y: 20 }}
			animate={{ opacity: 1, y: 0 }}
			transition={{ duration: 0.3 }}
			className="w-full max-w-7xl mx-auto px-6 pt-17 pb-6 space-y-6 min-h-[calc(100vh-64px)]"
		>
			<DocumentsFilters
				typeCounts={typeCounts as Partial<Record<DocumentTypeEnum, number>>}
				selectedIds={selectedIds}
				onSearch={setSearch}
				searchValue={search}
				onBulkDelete={onBulkDelete}
				onToggleType={onToggleType}
				activeTypes={activeTypes}
			/>

			<DocumentsTableShell
				documents={documents}
				loading={!!loading || typeCountsLoading}
				error={!!error}
				selectedIds={selectedIds}
				setSelectedIds={setSelectedIds}
				columnVisibility={columnVisibility}
				sortKey={sortKey}
				sortDesc={sortDesc}
				onSortChange={handleSortChange}
				deleteDocument={handleDeleteDocument}
				searchSpaceId={String(searchSpaceId)}
			/>

			<PaginationControls
				pageIndex={pageIndex}
				total={total}
				onFirst={() => setPageIndex(0)}
				onPrev={() => setPageIndex((i) => Math.max(0, i - 1))}
				onNext={() => setPageIndex((i) => (pageEnd < total ? i + 1 : i))}
				onLast={() => setPageIndex(Math.max(0, Math.ceil(total / PAGE_SIZE) - 1))}
				canPrev={pageIndex > 0}
				canNext={pageEnd < total}
			/>
		</motion.div>
	);
}

export { DocumentsTable };

