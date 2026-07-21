import { CheckCircle2, Circle, ExternalLink } from 'lucide-react';
import { WeaponClassification, PDF_URL, formatLabel } from '../data/weaponData';

interface ProgressPanelProps {
  possibleMatches: WeaponClassification[];
  totalClassifications: number;
  selections: Record<string, string>;
}

export function ProgressPanel({ 
  possibleMatches, 
  totalClassifications,
  selections 
}: ProgressPanelProps) {
  const matchCount = possibleMatches.length;
  const selectionCount = Object.keys(selections).length;
  const progressPercent = selectionCount === 0 ? 0 : ((totalClassifications - matchCount) / totalClassifications) * 100;

  return (
    <div className="bg-card border border-border rounded-lg h-full flex flex-col overflow-hidden">
      <div className="p-6 border-b border-border flex-shrink-0">
        <p className="text-sm text-muted-foreground mb-4">
          Watch as your selections narrow down the possibile classifications. The more characteristics you select, the shorter the list of possible weapon classification.
        </p>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-sm mb-2">
            <span className="text-muted-foreground">Possibilities eliminated</span>
            <span className="font-semibold text-foreground">
              {totalClassifications - matchCount} / {totalClassifications}
            </span>
          </div>
          <div className="w-full h-3 bg-muted rounded-full overflow-hidden">
            <div 
              className="h-full bg-accent transition-all duration-500"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>

        {/* Current Status */}
        <div className={`
          p-4 rounded-lg border transition-all
          ${matchCount === 1 
            ? 'border-accent bg-cream-light/50' 
            : matchCount <= 5
            ? 'border-neutral-gray/30 bg-cream-light/30'
            : 'border-border bg-muted/30'
          }
        `}>
          <div className="flex items-center gap-2 mb-2">
            {matchCount === 1 ? (
              <>
                <CheckCircle2 className="text-accent" size={20} />
                <span className="font-semibold text-neutral-darkest">Classification hypothesis narrowed</span>
              </>
            ) : (
              <>
                <Circle className="text-neutral-gray" size={20} />
                <span className="font-semibold text-neutral-darkest">
                  {matchCount} possible {matchCount === 1 ? 'match' : 'matches'}
                </span>
              </>
            )}
          </div>
          {matchCount > 1 && (
            <p className="text-sm text-muted-foreground">
              Continue selecting characteristics to narrow down further
            </p>
          )}
        </div>
      </div>

      {/* List of Possible Matches */}
      <div className="flex-1 overflow-y-auto p-6">
        <h3 className="text-sm font-semibold text-muted-foreground mb-3">
          Remaining Possibilities ({matchCount})
        </h3>
        <div className="space-y-2">
          {possibleMatches.map((weapon) => (
            <div
              key={weapon.id}
              className={`
                p-3 rounded-lg border transition-all
                ${matchCount === 1
                  ? 'border-accent/40 bg-cream-light/50 shadow-sm'
                  : 'border-border bg-card hover:border-neutral-gray hover:shadow-sm'
                }
              `}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  <h4 className="font-medium text-sm mb-1">{weapon.name}</h4>
                  <div className="flex flex-wrap gap-1 mb-2">
                    <span className="text-xs px-2 py-0.5 bg-muted rounded border border-border">
                      {formatLabel(weapon.group)}
                    </span>
                    <span className="text-xs px-2 py-0.5 bg-muted rounded border border-border">
                      {formatLabel(weapon.type)}
                    </span>
                  </div>
                  {weapon.pdfPages && weapon.pdfPages.length > 0 && (
                    <a
                      href={`${PDF_URL}#page=${weapon.pdfPages[0]}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-xs text-neutral-darkest hover:text-accent transition-colors"
                    >
                      <span>View in ARES Guide (p. {(weapon.rawPdfPages ?? weapon.pdfPages)[0]})</span>
                      <ExternalLink size={10} />
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}