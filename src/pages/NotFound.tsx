
import { Link } from 'react-router-dom';
import PageMeta from '@/components/common/PageMeta';

export default function NotFound() {
  return (
    <>
      <PageMeta
        title="Page Not Found"
        description="The requested DeepShield AI page could not be found."
      />

      <main className="relative z-10 flex min-h-screen flex-col items-center justify-center overflow-hidden p-6">
        <div className="mx-auto w-full max-w-[472px] text-center">
          <h1 className="mb-8 text-3xl font-bold text-foreground">
            Page Not Found
          </h1>

          <img
            src="/images/error/404.svg"
            alt="Page not found"
            className="mx-auto dark:hidden"
          />
          <img
            src="/images/error/404-dark.svg"
            alt="Page not found"
            className="mx-auto hidden dark:block"
          />

          <p className="mb-6 mt-8 text-base text-muted-foreground">
            The page you're looking for may have moved or may no longer exist.
            Check the address or return to the homepage.
          </p>

          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-lg border border-border bg-card px-5 py-3 text-sm font-medium text-foreground transition-colors hover:bg-muted"
          >
            Back to Home
          </Link>
        </div>

        <p className="absolute bottom-6 text-center text-sm text-muted-foreground">
          © {new Date().getFullYear()} DeepShield AI
        </p>
      </main>
    </>
  );
}
