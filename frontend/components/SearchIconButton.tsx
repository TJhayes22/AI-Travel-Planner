interface SearchIconButtonProps {
  loading?: boolean;
}

export function SearchIconButton({ loading = false }: SearchIconButtonProps) {
  return (
    <button
      type="submit"
      disabled={loading}
      aria-label={loading ? "Searching" : "Search"}
      className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-navy text-paper transition-colors hover:bg-ink disabled:opacity-40"
    >
      {loading ? (
        <svg
          className="h-4 w-4 animate-spin"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
        >
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
      ) : (
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
      )}
    </button>
  );
}