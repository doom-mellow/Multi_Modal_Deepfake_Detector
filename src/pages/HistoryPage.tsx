import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import { ResultBadge } from '@/components/ResultBadge';
import {
  Trash2,
  Video,
  Mic,
  FileText,
  Image as ImageIcon,
  Code2,
  Cpu,
  Fingerprint,
} from 'lucide-react';
import {
  fetchHistory,
  deleteHistoryRecord,
} from '@/services/historyService';
import type { HistoryRecord } from '@/types/types';
import { toast } from 'sonner';
import { Skeleton } from '@/components/ui/skeleton';

const PAGE_SIZE = 10;

function formatDate(dateString: string) {
  const date = new Date(dateString);

  if (Number.isNaN(date.getTime())) {
    return 'Unknown date';
  }

  return date.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function MediaIcon({ mediaType }: { mediaType: string }) {
  const className = 'h-5 w-5 text-primary';

  switch (mediaType) {
    case 'image':
      return <ImageIcon className={className} />;
    case 'video':
      return <Video className={className} />;
    case 'audio':
      return <Mic className={className} />;
    case 'text':
      return <FileText className={className} />;
    case 'code':
      return <Code2 className={className} />;
    case 'embedding':
      return <Cpu className={className} />;
    case 'watermark':
      return <Fingerprint className={className} />;
    default:
      return <FileText className={className} />;
  }
}

export default function HistoryPage() {
  const navigate = useNavigate();

  const [records, setRecords] = useState<HistoryRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalRecords, setTotalRecords] = useState(0);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const totalPages = Math.ceil(totalRecords / PAGE_SIZE);

  const loadHistory = useCallback(async () => {
    setIsLoading(true);

    try {
      const response = await fetchHistory(currentPage, PAGE_SIZE);

      if (response.error) {
        setRecords([]);
        setTotalRecords(0);
        toast.error(response.error);
        return;
      }

      setRecords(response.data ?? []);
      setTotalRecords(response.total ?? 0);
    } catch {
      setRecords([]);
      setTotalRecords(0);
      toast.error('Failed to load analysis history.');
    } finally {
      setIsLoading(false);
    }
  }, [currentPage]);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  const handleDelete = async () => {
    if (!deleteId || isDeleting) return;

    setIsDeleting(true);

    try {
      const response = await deleteHistoryRecord(deleteId);

      if (!response.success) {
        toast.error(response.error || 'Failed to delete the record.');
        return;
      }

      toast.success('Record deleted.');

      const isLastRecordOnPage = records.length === 1 && currentPage > 1;

      if (isLastRecordOnPage) {
        setCurrentPage((page) => page - 1);
      } else {
        await loadHistory();
      }
    } catch {
      toast.error('Failed to delete the record.');
    } finally {
      setIsDeleting(false);
      setDeleteId(null);
    }
  };

  return (
    <main className="min-h-screen bg-background px-4 py-8 text-foreground transition-colors">
      <div className="mx-auto max-w-6xl">
        <Card>
          <CardHeader>
            <CardTitle>Analysis History</CardTitle>
            <CardDescription>
              Review and manage your previous content analyses.
            </CardDescription>
          </CardHeader>

          <CardContent>
            {isLoading ? (
              <div className="space-y-3" aria-label="Loading history">
                {Array.from({ length: 5 }).map((_, index) => (
                  <Skeleton key={index} className="h-14 w-full" />
                ))}
              </div>
            ) : records.length === 0 ? (
              <div className="py-12 text-center">
                <p className="mb-4 text-muted-foreground">
                  No analysis history found.
                </p>
                <Button onClick={() => navigate('/detection')}>
                  Start an Analysis
                </Button>
              </div>
            ) : (
              <>
                <div className="overflow-x-auto rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Type</TableHead>
                        <TableHead>Content</TableHead>
                        <TableHead>Result</TableHead>
                        <TableHead className="text-right">
                          Confidence
                        </TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead className="w-16 text-right">
                          Action
                        </TableHead>
                      </TableRow>
                    </TableHeader>

                    <TableBody>
                      {records.map((record) => (
                        <TableRow key={record.id}>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              <MediaIcon mediaType={record.media_type} />
                              <span className="capitalize text-sm">
                                {record.media_type}
                              </span>
                            </div>
                          </TableCell>

                          <TableCell className="max-w-[220px] truncate">
                            {record.file_name ||
                              record.content_preview ||
                              'No preview available'}
                          </TableCell>

                          <TableCell>
                            <ResultBadge
                              result={record.result}
                              confidence={record.confidence}
                              showIcon={false}
                            />
                          </TableCell>

                          <TableCell className="text-right font-medium tabular-nums">
                            {Number.isFinite(Number(record.confidence))
                              ? `${record.confidence}%`
                              : '—'}
                          </TableCell>

                          <TableCell className="whitespace-nowrap text-sm text-muted-foreground">
                            {formatDate(record.created_at)}
                          </TableCell>

                          <TableCell className="text-right">
                            <Button
                              type="button"
                              variant="ghost"
                              size="icon"
                              aria-label={`Delete history record ${record.id}`}
                              onClick={() => setDeleteId(record.id)}
                            >
                              <Trash2 className="h-4 w-4 text-destructive" />
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                {totalPages > 1 && (
                  <div className="mt-5 flex items-center justify-between gap-3">
                    <p className="text-sm text-muted-foreground">
                      Page {currentPage} of {totalPages}
                    </p>

                    <div className="flex gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        disabled={currentPage <= 1 || isLoading}
                        onClick={() =>
                          setCurrentPage((page) => Math.max(1, page - 1))
                        }
                      >
                        Previous
                      </Button>

                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        disabled={currentPage >= totalPages || isLoading}
                        onClick={() =>
                          setCurrentPage((page) =>
                            Math.min(totalPages, page + 1),
                          )
                        }
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <AlertDialog
        open={Boolean(deleteId)}
        onOpenChange={(open) => {
          if (!open && !isDeleting) setDeleteId(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete analysis record?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete this history record. This action
              cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>

          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>
              Cancel
            </AlertDialogCancel>
            <AlertDialogAction
              disabled={isDeleting}
              onClick={(event) => {
                event.preventDefault();
                void handleDelete();
              }}
            >
              {isDeleting ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </main>
  );
}