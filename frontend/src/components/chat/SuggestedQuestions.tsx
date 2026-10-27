import "./SuggestedQuestions.css";

export function SuggestedQuestions({
  questions,
  onSelect,
}: {
  questions: string[];
  onSelect: (question: string) => void;
}) {
  if (questions.length === 0) return null;
  return (
    <div className="suggested-questions" role="group" aria-label="Suggested questions">
      {questions.map((question) => (
        <button
          key={question}
          type="button"
          className="suggested-chip"
          onClick={() => onSelect(question)}
        >
          {question}
        </button>
      ))}
    </div>
  );
}
