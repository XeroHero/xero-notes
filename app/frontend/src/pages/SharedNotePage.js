
Action: file_editor create /app/frontend/src/pages/SharedNotePage.js --file-text "import { useState, useEffect } from \"react\";
import { useParams, Link } from \"react-router-dom\";
import { ArrowLeft } from \"lucide-react\";
import { Button } from \"@/components/ui/button\";
import { Avatar, AvatarFallback, AvatarImage } from \"@/components/ui/avatar\";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SharedNotePage = () => {
  const { shareLink } = useParams();
  const [note, setNote] = useState(null);
  const [author, setAuthor] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSharedNote = async () => {
      try {
        const response = await fetch(`${API}/shared/${shareLink}`);

        if (!response.ok) {
          throw new Error(\"Note not found or no longer shared\");
        }

        const data = await response.json();
        setNote(data.note);
        setAuthor(data.author);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSharedNote();
  }, [shareLink]);

  if (isLoading) {
    return (
      <div className=\"min-h-screen flex items-center justify-center bg-[#F4F0EB]\">
        <div className=\"animate-spin rounded-full h-12 w-12 border-b-2 border-[#E06A4F]\"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className=\"min-h-screen flex items-center justify-center bg-[#F4F0EB] p-4\">
        <div className=\"text-center max-w-md\">
          <div className=\"w-16 h-16 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4\">
            <svg className=\"w-8 h-8 text-red-500\" fill=\"none\" stroke=\"currentColor\" viewBox=\"0 0 24 24\">
              <path strokeLinecap=\"round\" strokeLinejoin=\"round\" strokeWidth=\"2\" d=\"M6 18L18 6M6 6l12 12\" />
            </svg>
          </div>
          <h1 className=\"font-heading text-2xl font-semibold text-[#1C1917] mb-2\">
            Note not found
          </h1>
          <p className=\"text-[#78716C] font-body mb-6\">
            {error}
          </p>
          <Link to=\"/login\">
            <Button className=\"bg-[#E06A4F] hover:bg-[#C95A41] text-white rounded-full\">
              Go to Xero Notes
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className=\"min-h-screen bg-[#F4F0EB]\" data-testid=\"shared-note-page\">
      {/* Header */}
      <header className=\"bg-white border-b border-[#E7E5E4] px-4 py-3\">
        <div className=\"max-w-3xl mx-auto flex items-center justify-between\">
          <Link to=\"/login\">
            <Button variant=\"ghost\" size=\"sm\" className=\"text-[#78716C] hover:text-[#1C1917]\">
              <ArrowLeft className=\"h-4 w-4 mr-2\" />
              Go to Xero Notes
            </Button>
          </Link>

          {author && (
            <div className=\"flex items-center gap-2\">
              <span className=\"text-sm text-[#78716C] font-body\">Shared by</span>
              <Avatar className=\"h-8 w-8\">
                <AvatarImage src={author.picture} alt={author.name} />
                <AvatarFallback className=\"bg-[#E06A4F] text-white text-xs\">
                  {author.name?.charAt(0)?.toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <span className=\"text-sm font-medium text-[#1C1917] font-body\">{author.name}</span>
            </div>
          )}
        </div>
      </header>

      {/* Content */}
      <main className=\"max-w-3xl mx-auto px-4 py-8 md:py-12\">
        <article className=\"bg-white rounded-2xl shadow-sm border border-[#E7E5E4] p-6 md:p-10\">
          <h1 className=\"font-heading text-3xl md:text-4xl font-semibold text-[#1C1917] mb-4 tracking-tight\">
            {note.title}
          </h1>

          <div className=\"text-sm text-[#A8A29E] font-body mb-8\">
            Last updated {new Date(note.updated_at).toLocaleDateString(\"en-US\", {
              year: \"numeric\",
              month: \"long\",
              day: \"numeric\"
            })}
          </div>

          <div
            className=\"prose prose-stone max-w-none font-body leading-relaxed\"
            dangerouslySetInnerHTML={{ __html: note.content }}
          />
        </article>
      </main>

      {/* Footer */}
      <footer className=\"text-center py-8\">
        <p className=\"text-sm text-[#A8A29E] font-body\">
          Powered by <span className=\"text-[#E06A4F] font-medium\">Xero Notes</span>
        </p>
      </footer>
    </div>
  );
};

export default SharedNotePage;
"
Observation: Create successful: /app/frontend/src/pages/SharedNotePage.js