import { useState } from "react";

export default function Settings() {
  const [apiKey, setApiKey] = useState("");
  const [notifications, setNotifications] = useState(true);
  const [theme, setTheme] = useState("dark");

  const handleSave = () => {
    // Save settings logic here
    alert("Settings saved!");
  };

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-gray-700 px-6 py-4">
        <h1 className="text-xl font-display font-bold text-gold">Settings</h1>
        <p className="text-xs text-gray-400 mt-0.5">Configure your preferences</p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-2xl space-y-6">
          <div className="bg-navy rounded-xl border border-gray-700 p-6">
            <h3 className="text-lg font-display font-bold text-gold mb-4">Appearance</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">Theme</label>
                <select 
                  value={theme}
                  onChange={(e) => setTheme(e.target.value)}
                  className="w-full bg-navy-light border border-gray-600 rounded-lg px-4 py-2 text-gray-200"
                >
                  <option value="dark">Dark</option>
                  <option value="light">Light</option>
                  <option value="system">System</option>
                </select>
              </div>
            </div>
          </div>

          <div className="bg-navy rounded-xl border border-gray-700 p-6">
            <h3 className="text-lg font-display font-bold text-gold mb-4">Notifications</h3>
            <div className="flex items-center justify-between">
              <span className="text-gray-300">Enable notifications</span>
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
          </div>

          <div className="bg-navy rounded-xl border border-gray-700 p-6">
            <h3 className="text-lg font-display font-bold text-gold mb-4">API Configuration</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-400 mb-2">OpenAI API Key</label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="Enter your API key"
                  className="w-full bg-navy-light border border-gray-600 rounded-lg px-4 py-2 text-gray-200"
                />
              </div>
            </div>
          </div>

          <button
            onClick={handleSave}
            className="bg-gold text-navy-dark px-6 py-2 rounded-lg font-medium hover:bg-gold-light transition"
          >
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
}