import { X, ChevronDown, ChevronUp } from 'lucide-react';
import { useState, useEffect } from 'react'; // useEffect resets expansion on characteristic change
import { Characteristic, WEAPON_CLASSIFICATIONS } from '../data/weaponData';
import { PdfViewer } from './PdfViewer';

interface OptionPanelProps {
  characteristic: Characteristic | null;
  selectedOptionId?: string;
  onSelectOption: (optionId: string) => void;
  onClose: () => void;
  availableOptionIds?: Set<string>;
  currentSelections?: Partial<Record<string, string>>;
}

export function OptionPanel({
  characteristic,
  selectedOptionId,
  onSelectOption,
  onClose,
  availableOptionIds,
  currentSelections = {}
}: OptionPanelProps) {
  const [expandedOptionIds, setExpandedOptionIds] = useState<Set<string>>(new Set());

  useEffect(() => {
    setExpandedOptionIds(new Set());
  }, [characteristic?.id]);

  if (!characteristic) return null;

  const toggleExpand = (optionId: string) => {
    setExpandedOptionIds(prev => {
      const next = new Set(prev);
      if (next.has(optionId)) next.delete(optionId);
      else next.add(optionId);
      return next;
    });
  };

  const getFilteredClassifications = (optionId: string) => {
    return WEAPON_CLASSIFICATIONS.filter(weapon => {
      if (weapon.characteristics[characteristic.id] !== optionId) {
        return false;
      }
      
      return Object.entries(currentSelections).every(([charType, selectedValue]) => {
        if (charType === characteristic.id || selectedValue === 'unknown') {
          return true;
        }
        return weapon.characteristics[charType] === selectedValue;
      });
    })
    .map(weapon => weapon.name)
    .sort();
  };

  return (
    <div className="bg-card border border-border rounded-lg p-6 h-full overflow-y-auto">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="mb-1">{characteristic.name}</h2>
          <p className="text-sm text-muted-foreground">{characteristic.description}</p>
        </div>
        <button
          onClick={onClose}
          className="p-2 hover:bg-muted rounded-lg transition-colors"
          aria-label="Close"
        >
          <X size={20} />
        </button>
      </div>

      <div className="mb-6 p-4 bg-cream-light/50 border border-accent/20 rounded-lg">
        <p className="text-sm text-muted-foreground">
          Select the option that best matches what you see in your image
        </p>
      </div>

      <div className="space-y-3">
        {characteristic.options.map((option) => {
          const isSelected = selectedOptionId === option.id;
          const isExpanded = expandedOptionIds.has(option.id);
          const hasPdfPages = option.pdfPages && option.pdfPages.length > 0;
          const isAvailable = !availableOptionIds || availableOptionIds.has(option.id);
          const classificationsWithOption = getFilteredClassifications(option.id);
          
          return (
            <div 
              key={option.id} 
              className={`
                rounded-lg border transition-all
                ${isSelected 
                  ? 'border-neutral-darkest bg-cream-light shadow-sm' 
                  : isAvailable
                  ? 'border-border bg-card hover:border-neutral-gray hover:shadow-sm'
                  : 'border-border bg-muted/30 opacity-50'
                }
              `}
            >
              <button
                onClick={() => isAvailable && onSelectOption(option.id)}
                disabled={!isAvailable}
                className="w-full p-4 text-left"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <h4 className={`mb-1 ${isSelected ? 'text-neutral-darkest' : ''}`}>
                      {option.name}
                      {!isAvailable && <span className="ml-2 text-xs text-muted-foreground">(Not available)</span>}
                    </h4>
                    <p className="text-sm text-muted-foreground">{option.guidance}</p>
                  </div>
                  {hasPdfPages && isAvailable && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        toggleExpand(option.id);
                      }}
                      className="flex-shrink-0 p-1 hover:bg-muted rounded transition-colors"
                      aria-label={isExpanded ? 'Hide guide' : 'Show guide'}
                    >
                      {isExpanded ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                    </button>
                  )}
                </div>
              </button>

              {/* Expanded details */}
              {isExpanded && (
                <div className="px-4 pb-4 space-y-3">
                  {classificationsWithOption.length > 0 && (
                    <div className="pt-2 border-t border-border">
                      <p className="text-sm text-muted-foreground">
                        <span className="font-medium">Points towards:</span> {classificationsWithOption.join(', ')}
                      </p>
                    </div>
                  )}
                  
                  {hasPdfPages && (
                    <PdfViewer pages={option.pdfPages!} displayPages={option.rawPdfPages} title={option.name} />
                  )}
                </div>
              )}
            </div>
          );
        })}

        {/* Can't tell option */}
        <div
          className={`
            rounded-lg border transition-all
            ${selectedOptionId === 'unknown'
              ? 'border-neutral-gray bg-muted shadow-sm' 
              : 'border-border bg-card hover:border-neutral-gray hover:shadow-sm'
            }
          `}
        >
          <button
            onClick={() => onSelectOption('unknown')}
            className="w-full p-4 text-left"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <h4 className={`mb-1 ${selectedOptionId === 'unknown' ? 'text-neutral-darkest' : ''}`}>
                  can't tell / don't know
                </h4>
                <p className="text-sm text-muted-foreground">
                  Select this if you're unable to determine this characteristic from your image
                </p>
              </div>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}