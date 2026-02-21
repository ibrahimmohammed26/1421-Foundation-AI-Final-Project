import { useState, useEffect } from "react";
import { Database, CheckCircle, XCircle, RefreshCw, X } from "lucide-react";

interface DocumentCheckPopupProps {
  onClose: () => void;
  onReindex: () => void;
}

export default function DocumentCheckPopup({ onClose, onReindex }: DocumentCheckPopupProps) {
  const [checking, setChecking] = useState(true);
  const [docCount, setDocCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkDocuments();
  }, []);

  const checkDocuments = async () => {
    setChecking(true);
    try {
      const response = await fetch('http://localhost:8000/api/stats');
      const data = await response.json();
      setDocCount(data.documents_count || 0);
      setError(null);
    } catch (err) {
      setError('Could not connect to backend server');
    } finally {
      setChecking(false);
    }
  };

  const handleReindex = async () => {
    setChecking(true);
    try {
      await onReindex();
      await checkDocuments();
    } catch (err) {
      setError('Failed to reindex documents');
    } finally {
      setChecking(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50">
      <div className="bg-navy rounded-xl border border-gray-800 p-6 max-w-md w-full mx-4">
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5 text-gold" />
            <h2 className="text-lg font-display font-bold text-gold">Document Check</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-200 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {checking ? (
          <div className="py-8 flex flex-col items-center">
            <RefreshCw className="h-8 w-8 text-gold animate-spin mb-3" />
            <p className="text-gray-300">Checking document database...</p>
          </div>
        ) : error ? (
          <div className="py-4">
            <div className="flex items-center gap-3 text-red-400 mb-4">
              <XCircle className="h-6 w-6" />
              <p>{error}</p>
            </div>
            <button
              onClick={checkDocuments}
              className="w-full py-2 bg-gold text-navy-dark rounded-lg hover:bg-gold/90 transition-colors"
            >
              Try Again
            </button>
          </div>
        ) : (
          <div className="py-4">
            <div className="flex items-center gap-3 mb-4">
              {docCount > 0 ? (
                <>
                  <CheckCircle className="h-6 w-6 text-green-500" />
                  <div>
                    <p className="text-gray-200 font-medium">Documents loaded successfully!</p>
                    <p className="text-sm text-gray-400">{docCount} documents found in database</p>
                  </div>
                </>
              ) : (
                <>
                  <XCircle className="h-6 w-6 text-yellow-500" />
                  <div>
                    <p className="text-gray-200 font-medium">No documents found</p>
                    <p className="text-sm text-gray-400">The database is empty or not accessible</p>
                  </div>
                </>
              )}
            </div>

            {docCount === 0 && (
              <div className="mt-4 space-y-3">
                <p className="text-sm text-gray-400">
                  To load documents, run the indexer script:
                </p>
                <div className="bg-navy-light p-3 rounded-lg">
                  <code className="text-xs text-gold block">
                    cd export/backend<br />
                    python scripts/index_documents_simple.py --reset
                  </code>
                </div>
                <button
                  onClick={handleReindex}
                  className="w-full py-2 bg-gold text-navy-dark rounded-lg hover:bg-gold/90 transition-colors flex items-center justify-center gap-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  Run Indexer Now
                </button>
              </div>
            )}

            {docCount > 0 && (
              <button
                onClick={onClose}
                className="w-full mt-4 py-2 bg-gold text-navy-dark rounded-lg hover:bg-gold/90 transition-colors"
              >
                Continue to App
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}