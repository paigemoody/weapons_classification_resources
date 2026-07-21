import { LucideIcon, X } from 'lucide-react';

interface CharacteristicCardProps {
  name: string;
  description: string;
  icon: LucideIcon;
  isSelected: boolean;
  selectedOption?: string;
  onClick: () => void;
  availableOptionsCount?: number;
  totalOptionsCount?: number;
  onClear?: () => void;
}

export function CharacteristicCard({
  name,
  description,
  icon: Icon,
  isSelected,
  selectedOption,
  onClick,
  availableOptionsCount,
  totalOptionsCount,
  onClear
}: CharacteristicCardProps) {
  const hasSelection = selectedOption !== undefined;
  
  return (
    <button
      onClick={onClick}
      className={`
        w-full p-5 rounded-lg border text-left transition-all relative group
        ${isSelected 
          ? 'border-neutral-darkest bg-cream-light shadow-sm' 
          : 'border-border bg-card hover:border-neutral-gray hover:shadow-sm'
        }
      `}
    >
      {/* Clear button */}
      {hasSelection && onClear && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onClear();
          }}
          className="absolute top-3 right-3 p-1 opacity-0 group-hover:opacity-100 hover:bg-neutral-darkest/10 rounded transition-all"
          aria-label={`Clear ${name} selection`}
        >
          <X size={14} className="text-neutral-gray" />
        </button>
      )}
      
      <div className="flex items-start gap-4 pr-6">
        <div className={`
          p-2.5 rounded-lg transition-colors
          ${isSelected ? 'bg-neutral-darkest text-neutral-white' : 'bg-neutral-white border border-border text-neutral-gray'}
        `}>
          <Icon size={20} />
        </div>
        
        <div className="flex-1 min-w-0">
          <h3 className="mb-1">{name}</h3>

          {selectedOption && selectedOption !== 'unknown' && (
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-accent/20 border border-accent/30 rounded-full">
              <span className="text-sm font-medium text-neutral-darkest">{selectedOption}</span>
            </div>
          )}
          
          {selectedOption === 'unknown' && (
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-muted border border-border rounded-full">
              <span className="text-sm font-medium text-muted-foreground">Can't tell</span>
            </div>
          )}
          
          {!hasSelection && availableOptionsCount !== undefined && totalOptionsCount !== undefined && (
            <div className="inline-flex items-center px-3 py-1 bg-muted border border-border rounded-full">
              <span className="text-sm text-muted-foreground">
                {availableOptionsCount}/{totalOptionsCount} options
              </span>
            </div>
          )}
        </div>
      </div>
    </button>
  );
}