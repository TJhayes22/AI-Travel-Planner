export default function Loading() {
  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <div className="mb-10 h-4 w-28 animate-pulse bg-mist/20" />

      <div className="mb-8 border-b border-mist/30 pb-8">
        <div className="mb-3 h-3 w-40 animate-pulse bg-mist/20" />
        <div className="mb-3 h-9 w-64 animate-pulse bg-mist/30" />
        <div className="h-5 w-36 animate-pulse bg-mist/20" />
      </div>

      <div className="mb-8 flex gap-1.5">
        <div className="h-5 w-16 animate-pulse bg-mist/20" />
        <div className="h-5 w-20 animate-pulse bg-mist/20" />
        <div className="h-5 w-14 animate-pulse bg-mist/20" />
      </div>

      <div className="mb-10 space-y-2">
        <div className="h-4 w-full animate-pulse bg-mist/15" />
        <div className="h-4 w-full animate-pulse bg-mist/15" />
        <div className="h-4 w-2/3 animate-pulse bg-mist/15" />
      </div>
    </main>
  );
}