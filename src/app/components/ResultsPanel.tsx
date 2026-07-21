import { AlertCircle, CheckCircle2, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import { useState } from 'react';
import { WeaponClassification, PDF_URL } from '../data/weaponData';

interface ResultsPanelProps {
  possibleMatches: WeaponClassification[];
  totalClassifications: number;
}

export function ResultsPanel({ possibleMatches, totalClassifications }: ResultsPanelProps) {
  const [expandedWeaponId, setExpandedWeaponId] = useState<string | null>(null);
  const matchCount = possibleMatches.length;

  const toggleExpand = (weaponId: string) => {
    setExpandedWeaponId(expandedWeaponId === weaponId ? null : weaponId);
  };
  
  return (
    <div className="bg-white border-2 border-gray-200 rounded-lg p-6 h-full overflow-y-auto">
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-2">Possible Classifications</h2>
        <div className="flex items-center gap-2">
          {matchCount === 1 ? (
            <>
              <CheckCircle2 className="text-green-500" size={20} />
              <p className="text-green-700">
                Match found! You've identified the weapon.
              </p>
            </>
          ) : matchCount > 1 ? (
            <>
              <AlertCircle className="text-blue-500" size={20} />
              <p className="text-gray-700">
                {matchCount} of {totalClassifications} possible matches
              </p>
            </>
          ) : (
            <>
              <AlertCircle className="text-orange-500" size={20} />
              <p className="text-orange-700">
                No exact matches. Check your selections.
              </p>
            </>
          )}
        </div>
      </div>

      <div className="space-y-3">
        {possibleMatches.length > 0 ? (
          possibleMatches.map((weapon) => {
            const isExpanded = expandedWeaponId === weapon.id;
            const hasPdfPages = weapon.pdfPages && weapon.pdfPages.length > 0;
            const hasImage = weapon.imageUrl;

            return (
              <div key={weapon.id} className="space-y-2">
                <div
                  className={`
                    p-4 rounded-lg border-2 transition-all
                    ${matchCount === 1 
                      ? 'border-green-500 bg-green-50' 
                      : 'border-gray-200 bg-gray-50'
                    }
                  `}
                >
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <h3 className="font-semibold mb-1">{weapon.name}</h3>
                      <p className="text-sm text-gray-600 mb-2">{weapon.description}</p>
                      <div className="flex flex-wrap gap-2 text-xs">
                        <span className="px-2 py-1 bg-white rounded border border-gray-200">
                          {weapon.group}
                        </span>
                        <span className="px-2 py-1 bg-white rounded border border-gray-200">
                          {weapon.type}
                        </span>
                        {weapon.subType && (
                          <span className="px-2 py-1 bg-white rounded border border-gray-200">
                            {weapon.subType}
                          </span>
                        )}
                      </div>
                    </div>
                    {(hasPdfPages || hasImage) && (
                      <button
                        onClick={() => toggleExpand(weapon.id)}
                        className="flex-shrink-0 p-1 hover:bg-white rounded transition-colors"
                        aria-label={isExpanded ? 'Hide details' : 'Show details'}
                      >
                        {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                      </button>
                    )}
                  </div>
                </div>

                {/* Expanded Details */}
                {isExpanded && (
                  <div className="ml-4 space-y-3">
                    {/* Image */}
                    {hasImage && (
                      <div className="bg-white rounded-lg border border-gray-200 p-3">
                        <h4 className="text-sm font-medium mb-2">Reference Image</h4>
                        <img 
                          src={weapon.imageUrl} 
                          alt={weapon.name}
                          className="w-full rounded border border-gray-200"
                        />
                      </div>
                    )}

                    {/* PDF Link */}
                    {hasPdfPages && (
                      <div className="bg-white rounded-lg border border-gray-200 p-3">
                        <h4 className="text-sm font-medium mb-2">ARES Guide Reference</h4>
                        <a
                          href={`${PDF_URL}#page=${weapon.pdfPages![0]}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700"
                        >
                          <span>View in ARES Guide (Page {(weapon.rawPdfPages ?? weapon.pdfPages)!.join(', ')})</span>
                          <ExternalLink size={14} />
                        </a>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="text-center py-8 text-gray-500">
            <p>Select characteristics to narrow down the classification.</p>
          </div>
        )}
      </div>
    </div>
  );
}