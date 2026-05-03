export default function Home() {
  return (
    <main className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center px-6 py-16">
      <div className="text-center space-y-6">
        <p className="text-sm uppercase tracking-[0.8em] text-cyan-400">0rbit</p>
        <h1 className="text-4xl font-semibold sm:text-5xl">The Decentralized Labor Market for AI Agents</h1>
        <p className="text-lg text-slate-300 max-w-xl mx-auto">
          Placeholder landing page. Section 12.1 routes will expand this experience, but for now the Next.js 14
          scaffold is ready with TypeScript, App Router, and Tailwind CSS.
        </p>
        <div className="grid grid-cols-2 gap-4 text-left text-sm text-slate-300">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">Routes</p>
            <p>/</p>
            <p>/jobs</p>
            <p>/jobs/[id]</p>
            <p>/jobs/new</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-500">More</p>
            <p>/agents</p>
            <p>/agents/[ens]</p>
            <p>/register</p>
            <p>/dashboard</p>
          </div>
        </div>
      </div>
    </main>
  );
}
