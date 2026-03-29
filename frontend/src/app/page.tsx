interface ImagePlaceholderProps {
  label: string;
  size: "sm" | "md";
}

function ImagePlaceholder({ label, size }: ImagePlaceholderProps) {
  const classes =
    size === "md"
      ? "h-5 w-5 rounded-md text-[7px]"
      : "h-4 w-4 rounded text-[6px]";

  return (
    <span
      aria-hidden="true"
      className={`inline-flex shrink-0 items-center justify-center border border-dashed border-current/40 bg-current/5 font-semibold uppercase tracking-[0.08em] ${classes}`}
      title={`${label} placeholder`}
    >
      Img
    </span>
  );
}

export default function Home() {
  return (
    <div className="grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)]">
      <main className="flex flex-col gap-[32px] row-start-2 items-center sm:items-start">
        <h1 className="text-3xl font-bold">OpenBank Wealth Management</h1>

        <div className="max-w-2xl">
          <p className="text-lg mb-4">
            Welcome to your personalized wealth management dashboard. Monitor
            your investments, track your portfolio performance, and plan your
            financial future.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 my-8">
            <div className="p-6 border rounded-lg shadow-sm">
              <h2 className="text-xl font-semibold mb-2">Portfolio Tracking</h2>
              <p>
                View all your investments in one place with real-time updates
                and performance metrics.
              </p>
            </div>

            <div className="p-6 border rounded-lg shadow-sm">
              <h2 className="text-xl font-semibold mb-2">Financial Planning</h2>
              <p>
                Set goals, create retirement plans, and receive personalized
                financial advice.
              </p>
            </div>
          </div>
        </div>

        <div className="flex gap-4 items-center flex-col sm:flex-row">
          <a
            className="rounded-full border border-solid border-transparent transition-colors flex items-center justify-center bg-foreground text-background gap-2 hover:bg-[#383838] dark:hover:bg-[#ccc] font-medium text-sm sm:text-base h-10 sm:h-12 px-4 sm:px-5 sm:w-auto"
            href="/dashboard"
          >
            <ImagePlaceholder label="Dashboard icon" size="md" />
            View Dashboard
          </a>
          <a
            className="rounded-full border border-solid border-black/[.08] dark:border-white/[.145] transition-colors flex items-center justify-center hover:bg-[#f2f2f2] dark:hover:bg-[#1a1a1a] hover:border-transparent font-medium text-sm sm:text-base h-10 sm:h-12 px-4 sm:px-5 w-full sm:w-auto md:w-[158px]"
            href="/investments"
          >
            Manage Investments
          </a>
        </div>
      </main>
      <footer className="row-start-3 flex gap-[24px] flex-wrap items-center justify-center">
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="/financial-education"
        >
          <ImagePlaceholder label="Education icon" size="sm" />
          Financial Education
        </a>
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="/support"
        >
          <ImagePlaceholder label="Support icon" size="sm" />
          Support
        </a>
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="/contact"
        >
          <ImagePlaceholder label="Contact icon" size="sm" />
          Contact an Advisor →
        </a>
      </footer>
    </div>
  );
}
