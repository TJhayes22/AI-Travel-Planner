import { getHealth } from "@/lib/api";

export default async function Home() {
  let status: { ok: boolean; message: string };

  try {
    const health = await getHealth();
    const allOk = health.api === "ok" && health.database === "ok";
    status = {
      ok: allOk,
      message: allOk
        ? "Connected to backend. API and database are both healthy."
        : `Backend reachable, but reporting an issue: ${JSON.stringify(health)}`,
    };
  } catch (err) {
    status = {
      ok: false,
      message: `Could not reach backend at the configured API URL. Is it running? (${
        err instanceof Error ? err.message : String(err)
      })`,
    };
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 p-8">
      <h1 className="text-2xl font-semibold">AI Travel Planner</h1>
      <div
        className={`rounded-lg border px-4 py-3 text-sm ${
          status.ok
            ? "border-green-300 bg-green-50 text-green-800"
            : "border-red-300 bg-red-50 text-red-800"
        }`}
      >
        {status.message}
      </div>
    </main>
  );
}