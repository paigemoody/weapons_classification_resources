import { useState } from 'react';
import { ChevronLeft, ChevronRight, ExternalLink } from 'lucide-react';
import { PDF_URL } from '../data/weaponData';

interface PdfViewerProps {
  pages: number[];
  displayPages?: number[];  // raw page numbers to show in labels (no offset)
  title: string;
}

export function PdfViewer({ pages, displayPages, title }: PdfViewerProps) {
  const [currentPageIndex, setCurrentPageIndex] = useState(0);
  const currentPage = pages[currentPageIndex];
  const displayPage = (displayPages ?? pages)[currentPageIndex];

  const handlePrevious = () => {
    setCurrentPageIndex((prev) => Math.max(0, prev - 1));
  };

  const handleNext = () => {
    setCurrentPageIndex((prev) => Math.min(pages.length - 1, prev + 1));
  };

  return (
    <div className="bg-muted rounded-lg border border-border overflow-hidden">
      {/* Header */}
      <div className="bg-card border-b border-border px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-foreground">
              ARES Guide - Page {displayPage}
            </span>
            {pages.length > 1 && (
              <div className="flex items-center gap-1">
                <button
                  onClick={handlePrevious}
                  disabled={currentPageIndex === 0}
                  className="p-1 rounded hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label="Previous page"
                >
                  <ChevronLeft size={16} />
                </button>
                <span className="text-xs text-muted-foreground">
                  {currentPageIndex + 1} / {pages.length}
                </span>
                <button
                  onClick={handleNext}
                  disabled={currentPageIndex === pages.length - 1}
                  className="p-1 rounded hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
                  aria-label="Next page"
                >
                  <ChevronRight size={16} />
                </button>
              </div>
            )}
          </div>
          <a
            href={`${PDF_URL}#page=${currentPage}`}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-xs text-neutral-darkest hover:text-accent transition-colors"
          >
            <span>Open in new tab</span>
            <ExternalLink size={12} />
          </a>
        </div>
      </div>

      {/* PDF Iframe */}
      <div className="relative" style={{ height: '500px' }}>
        <iframe
          src={`${PDF_URL}#page=${currentPage}&view=FitH&toolbar=0&navpanes=0`}
          className="w-full h-full"
          title={`${title} - Page ${displayPage}`}
        />
      </div>
    </div>
  );
}