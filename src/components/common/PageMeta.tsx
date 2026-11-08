import { Helmet, HelmetProvider } from 'react-helmet-async';
import type { ReactNode } from 'react';

import { TooltipProvider } from '@/components/ui/tooltip';

interface PageMetaProps {
  title: string;
  description: string;
}

/**
 * Sets page-specific document metadata.
 */
const PageMeta = ({ title, description }: PageMetaProps) => (
  <Helmet>
    <title>{title}</title>
    <meta name="description" content={description} />
  </Helmet>
);

/**
 * Provides application-wide metadata and tooltip contexts.
 */
export const AppWrapper = ({ children }: { children: ReactNode }) => (
  <HelmetProvider>
    <TooltipProvider>{children}</TooltipProvider>
  </HelmetProvider>
);

export default PageMeta;