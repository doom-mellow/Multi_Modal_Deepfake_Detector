
import PageMeta from '@/components/common/PageMeta';

export default function SamplePage() {
  return (
    <>
      <PageMeta
        title="Sample Page"
        description="A placeholder page for development."
      />

      <main className="container mx-auto px-4 py-8">
        <h1 className="text-2xl font-semibold text-foreground">
          Sample Page
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          This page is reserved for development and testing.
        </p>
      </main>
    </>
  );
}
