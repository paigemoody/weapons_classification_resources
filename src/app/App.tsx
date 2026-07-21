import { useState, useMemo } from 'react';
import { Hand, Circle, Package, Settings } from 'lucide-react';
import { CharacteristicCard } from './components/CharacteristicCard';
import { OptionPanel } from './components/OptionPanel';
import { ProgressPanel } from './components/ProgressPanel';
import {
  CHARACTERISTICS,
  WEAPON_CLASSIFICATIONS,
  CharacteristicType
} from './data/weaponData';

const CHARACTERISTIC_ICONS = {
  'how_held': Hand,
  'bore_type': Circle,
  'loading': Package,
  'method_of_operation': Settings
};

export default function App() {
  const [selectedCharacteristic, setSelectedCharacteristic] = useState<CharacteristicType | null>('how_held');
  const [selections, setSelections] = useState<Partial<Record<CharacteristicType, string>>>({});

  const handleSelectOption = (characteristicId: CharacteristicType, optionId: string) => {
    setSelections((prev) => ({ ...prev, [characteristicId]: optionId }));
  };

  const handleClearSingleSelection = (characteristicId: CharacteristicType) => {
    setSelections((prev) => {
      const newSelections = { ...prev };
      delete newSelections[characteristicId];
      return newSelections;
    });
  };

  const handleClearSelections = () => {
    setSelections({});
    setSelectedCharacteristic(null);
  };

  const possibleMatches = useMemo(() => {
    if (Object.keys(selections).length === 0) {
      return [...WEAPON_CLASSIFICATIONS].sort((a, b) => a.name.localeCompare(b.name));
    }

    return WEAPON_CLASSIFICATIONS.filter((weapon) => {
      return Object.entries(selections).every(([charType, optionId]) => {
        if (optionId === 'unknown') return true;
        return weapon.characteristics[charType as CharacteristicType] === optionId;
      });
    }).sort((a, b) => a.name.localeCompare(b.name));
  }, [selections]);

  const getAvailableOptions = useMemo(() => {
    const availableByCharacteristic: Record<CharacteristicType, Set<string>> = {
      'how_held': new Set(),
      'bore_type': new Set(),
      'loading': new Set(),
      'method_of_operation': new Set()
    };

    possibleMatches.forEach((weapon) => {
      Object.entries(weapon.characteristics).forEach(([charType, optionId]) => {
        if (optionId) {
          availableByCharacteristic[charType as CharacteristicType].add(optionId);
        }
      });
    });

    return availableByCharacteristic;
  }, [possibleMatches]);

  const currentCharacteristic = selectedCharacteristic
    ? CHARACTERISTICS.find((c) => c.id === selectedCharacteristic)
    : null;

  const getSelectedOptionName = (charId: CharacteristicType) => {
    const optionId = selections[charId];
    if (!optionId) return undefined;
    if (optionId === 'unknown') return 'unknown';
    const char = CHARACTERISTICS.find((c) => c.id === charId);
    const option = char?.options.find((o) => o.id === optionId);
    return option?.name;
  };

  return (
    <div className="size-full bg-neutral-white overflow-hidden">
      <div className="h-full flex flex-col">
        {/* Header */}
        <div className="bg-card border-b border-border px-6 py-8">
          <div className="max-w-7xl mx-auto">
            <h1 className="mb-2 text-4xl font-bold">Weapon Classification Assistant</h1>
            <p className="text-muted-foreground">
              This tool assists in narrowing down possible weapon classifications to help focus your research.
            </p>
            <p className="text-muted-foreground">
              📑 Based on the{' '}
              <a
                href="https://armamentresearch.com/wp-content/uploads/2022/08/The-ARES-Arms-Munitions-Classification-System-ARCS-ver1.3-public-release.pdf"
                className="underline hover:text-foreground"
                target="_blank"
                rel="noopener noreferrer"
              >
                ARES Arms & Munitions Classification System (ARCS)
              </a>
              {' '}and the{' '}
              <a
                href="https://www.smallarmssurvey.org/sites/default/files/SAS-HB-06-Weapons-ID-Guide-Full.pdf"
                className="underline hover:text-foreground"
                target="_blank"
                rel="noopener noreferrer"
              >
                Small Arms Survey Handbook
              </a>
              .
            </p>
            <p className="mt-1 text-sm italic text-muted-foreground">
              Developed in partnership with Bellingcat through the{' '}
              <a
                href="https://www.hackshackers.com/every-organization-has-a-process-yours-just-isnt-written-down/"
                className="underline hover:text-foreground"
                target="_blank"
                rel="noopener noreferrer"
              >
                Hacks/Hackers Newsroom AI Lab
              </a>
              .
            </p>
          </div>
        </div>

        {/* Main Content */}
        <div className="flex-1 overflow-hidden">
          <div className="h-full max-w-[1800px] mx-auto p-6">
            <div className="h-full grid grid-cols-1 lg:grid-cols-[1fr_2fr_1fr] gap-6">
              {/* Left Column - Characteristics */}
              <div className="flex flex-col min-h-0">
                <div className="flex-1 overflow-y-auto space-y-4">
                  <h2 className="text-base font-semibold px-1">Step 1: Select a Characteristic to Review</h2>

                  {/* Controls */}
                  <div className="flex items-center justify-between px-1">
                    <p className="text-sm text-muted-foreground">
                      {Object.keys(selections).length} of {CHARACTERISTICS.length} reviewed
                    </p>
                    {Object.keys(selections).length > 0 && (
                      <button
                        onClick={handleClearSelections}
                        className="px-3 py-1.5 text-sm text-neutral-darkest hover:bg-cream-light rounded transition-colors"
                      >
                        Clear All
                      </button>
                    )}
                  </div>

                  {/* Characteristic Cards */}
                  <div className="space-y-3">
                    {CHARACTERISTICS.map((char) => (
                      <CharacteristicCard
                        key={char.id}
                        name={char.name}
                        description={char.description}
                        icon={CHARACTERISTIC_ICONS[char.id]}
                        isSelected={selectedCharacteristic === char.id}
                        selectedOption={getSelectedOptionName(char.id)}
                        onClick={() => setSelectedCharacteristic(char.id)}
                        availableOptionsCount={getAvailableOptions[char.id].size}
                        totalOptionsCount={char.options.length}
                        onClear={() => handleClearSingleSelection(char.id)}
                      />
                    ))}
                  </div>
                </div>
              </div>

              {/* Middle Column - Options */}
              <div className="hidden lg:flex flex-col min-h-0 gap-4">
                <h2 className="text-base font-semibold px-1 flex-shrink-0">Step 2: Determine which Option fits best</h2>
                <div className="flex-1 min-h-0">
                  {currentCharacteristic ? (
                    <OptionPanel
                      characteristic={currentCharacteristic}
                      selectedOptionId={selections[selectedCharacteristic!]}
                      onSelectOption={(optionId) =>
                        handleSelectOption(selectedCharacteristic!, optionId)
                      }
                      onClose={() => setSelectedCharacteristic(null)}
                      availableOptionIds={getAvailableOptions[selectedCharacteristic!]}
                      currentSelections={selections}
                    />
                  ) : (
                    <div className="bg-card border border-border rounded-lg p-6 h-full flex items-center justify-center">
                      <div className="text-center text-muted-foreground">
                        <Package size={48} className="mx-auto mb-3 opacity-30" />
                        <p className="text-sm">Select a characteristic to view options</p>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Right Column - Progress/Results */}
              <div className="hidden lg:flex flex-col min-h-0 gap-4">
                <h2 className="text-base font-semibold px-1 flex-shrink-0">Narrowing Results</h2>
                <div className="flex-1 min-h-0">
                  <ProgressPanel
                    possibleMatches={possibleMatches}
                    totalClassifications={WEAPON_CLASSIFICATIONS.length}
                    selections={selections}
                  />
                </div>
              </div>

              {/* Mobile Option Panel */}
              {currentCharacteristic && (
                <div className="lg:hidden">
                  <OptionPanel
                    characteristic={currentCharacteristic}
                    selectedOptionId={selections[selectedCharacteristic!]}
                    onSelectOption={(optionId) =>
                      handleSelectOption(selectedCharacteristic!, optionId)
                    }
                    onClose={() => setSelectedCharacteristic(null)}
                    availableOptionIds={getAvailableOptions[selectedCharacteristic!]}
                    currentSelections={selections}
                  />
                </div>
              )}

              {/* Mobile Progress Panel */}
              <div className="lg:hidden">
                <ProgressPanel
                  possibleMatches={possibleMatches}
                  totalClassifications={WEAPON_CLASSIFICATIONS.length}
                  selections={selections}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}