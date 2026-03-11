import { useRef, useState } from "react";
import { HeaderSection } from "./components/app/HeaderSection";
import { HomeScreen } from "./components/app/HomeScreen";
import { InputSection } from "./components/app/InputSection";
import { OptionsSection } from "./components/app/OptionsSection";
import { ResultSection } from "./components/app/ResultSection";
import { StatusSection } from "./components/app/StatusSection";
import { useAnonymizer } from "./hooks/useAnonymizer";
import { useHistory } from "./hooks/useHistory";

export default function App() {
  const [errorMessage, setErrorMessage] = useState("");
  const [screen, setScreen] = useState<"home" | "processing">("home");
  const resultSectionRef = useRef<HTMLDivElement | null>(null);
  const { history, addHistoryEntry } = useHistory();
  const {
    mode,
    setMode,
    options,
    updateOption,
    inputText,
    setInputText,
    outputText,
    resultPath,
    progress,
    status,
    busy,
    warning,
    characterCount,
    currentFileName,
    onFilesSelected,
    runText,
    runFile,
    clearText,
    copyOutput,
    downloadActive,
    activeItem,
    resultItems,
    setActiveItemId,
  } = useAnonymizer({ onHistoryEntry: addHistoryEntry });

  const handleAction = async (action: () => Promise<void>) => {
    setErrorMessage("");
    try {
      await action();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Произошла ошибка");
    }
  };

  const openProcessing = (nextMode: "file" | "text" = "file") => {
    setMode(nextMode);
    setScreen("processing");
  };

  if (screen === "home") {
    return <HomeScreen onOpenUpload={openProcessing} history={history} />;
  }

  return (
    <main className="app-shell">
      <div className="app-layout">
        <HeaderSection
          mode={mode}
          onModeChange={setMode}
          onBackHome={() => setScreen("home")}
          onResultsOpen={() => resultSectionRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })}
        />
        <StatusSection status={status} progress={progress} />
        <OptionsSection options={options} onToggle={updateOption} busy={busy} />

        <div className="app-columns">
          <InputSection
            mode={mode}
            inputText={inputText}
            onInputTextChange={setInputText}
            characterCount={characterCount}
            currentFileName={currentFileName}
            busy={busy}
            warning={warning}
            onSelectFiles={onFilesSelected}
            onSubmit={() => handleAction(mode === "text" ? runText : runFile)}
            onClear={clearText}
            onDownload={downloadActive}
          />
          <ResultSection
            mode={mode}
            outputText={outputText}
            busy={busy}
            onCopy={() => handleAction(copyOutput)}
            onDownload={downloadActive}
            items={resultItems}
            activeItemId={activeItem?.filename}
            onSelectItem={setActiveItemId}
            sectionRef={resultSectionRef}
            downloadName={activeItem?.result?.output_filename || currentFileName}
          />
        </div>

        {errorMessage ? <div className="app-error">{errorMessage}</div> : null}
      </div>
    </main>
  );
}
