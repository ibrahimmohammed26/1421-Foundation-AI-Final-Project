import { useState } from "react";
import { 
  Trash2, 
  MessageSquare, 
  Download,
  Bell,
  Moon,
  Globe,
  Check
} from "lucide-react";

export default function Settings() {
  const [notifications, setNotifications] = useState(true);
  const [language, setLanguage] = useState("en");
  const [darkMode, setDarkMode] = useState(true);
  const [showConfirmClear, setShowConfirmClear] = useState(false);
  const [clearSuccess, setClearSuccess] = useState(false);

  const handleClearChat = () => {
    // Clear chat history from localStorage or state management
    localStorage.removeItem('chatHistory');
    setShowConfirmClear(false);
    setClearSuccess(true);
    setTimeout(() => setClearSuccess(false), 3000);
  };

  const handleExportData = () => {
    // Export user data as JSON
    const data = {
      chatHistory: JSON.parse(localStorage.getItem('chatHistory') || '[]'),
      preferences: {
        notifications,
        language,
        darkMode
      },
      exportDate: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `1421-data-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
  };

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-gray-700 px-6 py-4">
        <h1 className="text-xl font-display font-bold text-gold">Settings</h1>
        <p className="text-xs text-gray-400 mt-0.5">
          Manage your preferences and data
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-2xl space-y-6">
          {/* Preferences Section */}
          <div className="bg-navy rounded-xl border border-gray-700 p-6">
            <h3 className="text-lg font-display font-bold text-gold mb-4">Preferences</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Bell className="h-4 w-4 text-gray-400" />
                  <span className="text-sm text-gray-300">Enable notifications</span>
                </div>
                <button
                  onClick={() => setNotifications(!notifications)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    notifications ? 'bg-gold' : 'bg-gray-600'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      notifications ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Moon className="h-4 w-4 text-gray-400" />
                  <span className="text-sm text-gray-300">Dark mode</span>
                </div>
                <button
                  onClick={() => setDarkMode(!darkMode)}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    darkMode ? 'bg-gold' : 'bg-gray-600'
                  }`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      darkMode ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Globe className="h-4 w-4 text-gray-400" />
                  <span className="text-sm text-gray-300">Language</span>
                </div>
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="bg-navy-light border border-gray-700 rounded-lg px-3 py-1.5 text-sm text-gray-200"
                >
                  <option value="en">English</option>
                  <option value="zh">中文</option>
                  <option value="es">Español</option>
                </select>
              </div>
            </div>
          </div>

          {/* Data Management Section */}
          <div className="bg-navy rounded-xl border border-gray-700 p-6">
            <h3 className="text-lg font-display font-bold text-gold mb-4">Data Management</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <MessageSquare className="h-4 w-4 text-gray-400" />
                  <div>
                    <span className="text-sm text-gray-300">Clear chat history</span>
                    <p className="text-xs text-gray-500">Delete all your conversations</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowConfirmClear(true)}
                  className="px-3 py-1.5 bg-red-500/10 text-red-500 rounded-lg text-xs hover:bg-red-500/20 transition-colors"
                >
                  Clear
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Download className="h-4 w-4 text-gray-400" />
                  <div>
                    <span className="text-sm text-gray-300">Export data</span>
                    <p className="text-xs text-gray-500">Download your conversations and settings</p>
                  </div>
                </div>
                <button
                  onClick={handleExportData}
                  className="px-3 py-1.5 bg-gold/10 text-gold rounded-lg text-xs hover:bg-gold/20 transition-colors"
                >
                  Export
                </button>
              </div>
            </div>
          </div>

          {/* About Section */}
          <div className="bg-navy rounded-xl border border-gray-700 p-6">
            <h3 className="text-lg font-display font-bold text-gold mb-4">About</h3>
            <div className="space-y-3">
              <p className="text-sm text-gray-400">
                1421 Foundation Research System v1.0.0
              </p>
              <p className="text-sm text-gray-400">
                A platform for exploring Chinese maritime history and the voyages of Zheng He.
              </p>
              <div className="pt-3 text-xs text-gray-500">
                © 2026 1421 Foundation. All rights reserved.
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Confirmation Modal for Clear Chat */}
      {showConfirmClear && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-navy rounded-xl border border-gray-700 p-6 max-w-md">
            <h3 className="text-lg font-display font-bold text-gold mb-3">Clear Chat History?</h3>
            <p className="text-sm text-gray-400 mb-6">
              This will permanently delete all your conversations. This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowConfirmClear(false)}
                className="px-4 py-2 text-sm text-gray-400 hover:text-gray-200 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleClearChat}
                className="px-4 py-2 bg-red-500 text-white rounded-lg text-sm hover:bg-red-600 transition-colors"
              >
                Clear All
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Success Toast */}
      {clearSuccess && (
        <div className="fixed bottom-6 right-6 bg-green-500 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
          <Check className="h-4 w-4" />
          <span className="text-sm">Chat history cleared successfully</span>
        </div>
      )}
    </div>
  );
}