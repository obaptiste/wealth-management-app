import Image from "next/image";

export default function Home() {
  return (
    <div className="grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)]">
      <main className="flex flex-col gap-[32px] row-start-2 items-center sm:items-start">
        <h1 className="text-3xl font-bold">OpenBank Wealth Management</h1>
        
        <div className="max-w-2xl">
          <p className="text-lg mb-4">
            Welcome to your personalized wealth management dashboard. Monitor your investments, 
            track your portfolio performance, and plan your financial future.
          </p>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 my-8">
            <div className="p-6 border rounded-lg shadow-sm">
              <h2 className="text-xl font-semibold mb-2">Portfolio Tracking</h2>
              <p>View all your investments in one place with real-time updates and performance metrics.</p>
            </div>
            
            <div className="p-6 border rounded-lg shadow-sm">
              <h2 className="text-xl font-semibold mb-2">Financial Planning</h2>
              <p>Set goals, create retirement plans, and receive personalized financial advice.</p>
            </div>
          </div>
        </div>

        <div className="flex gap-4 items-center flex-col sm:flex-row">
          <a
            className="rounded-full border border-solid border-transparent transition-colors flex items-center justify-center bg-foreground text-background gap-2 hover:bg-[#383838] dark:hover:bg-[#ccc] font-medium text-sm sm:text-base h-10 sm:h-12 px-4 sm:px-5 sm:w-auto"
            href="/dashboard"
          >
            <Image
              src="/dashboard-icon.svg"
              alt="Dashboard icon"
              width={20}
              height={20}
            />
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
          <Image
            aria-hidden
            src="/education-icon.svg"
            alt="Education icon"
            width={16}
            height={16}
          />
          Financial Education
        </a>
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="/support"
        >
          <Image
            aria-hidden
            src="/support-icon.svg"
            alt="Support icon"
            width={16}
            height={16}
          />
          Support
        </a>
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="/contact"
        >
          <Image
            aria-hidden
            src="/contact-icon.svg"
            alt="Contact icon"
            width={16}
            height={16}
          />
          Contact an Advisor →
        </a>
      </footer>
    </div>
  );
}
