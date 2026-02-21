import { useState, useEffect } from "react";
import { fetchLocations } from "@/lib/api";  // Import your existing function

export default function Dashboard() {
  const [stats, setStats] = useState({ feedback_count: 0, locations_count: 0 });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Since you don't have a getStats endpoint in your API file yet,
    // we'll use fetchLocations to get count and you'll need to add a stats endpoint
    const fetchStats = async () => {
      try {
        // Get locations count
        const locations = await fetchLocations(1421);
        
        // For feedback count, you'll need to either:
        // Option 1: Add a getStats function to your API file
        // Option 2: Create a separate fetch for stats
        
        // For now, let's use what we have:
        setStats({
          locations_count: locations.length,
          feedback_count: 0 // You'll need to implement this
        });
        setLoading(false);
      } catch (error) {
        console.error('Error fetching stats:', error);
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-gray-700 px-6 py-4">
        <h1 className="text-xl font-display font-bold text-gold">Dashboard</h1>
        <p className="text-xs text-gray-400 mt-0.5">System overview and statistics</p>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gold"></div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-navy rounded-xl border border-gray-700 p-6">
              <h3 className="text-sm text-gray-400 mb-2">Total Feedback</h3>
              <p className="text-4xl font-display font-bold text-gold">{stats.feedback_count}</p>
            </div>
            <div className="bg-navy rounded-xl border border-gray-700 p-6">
              <h3 className="text-sm text-gray-400 mb-2">Voyage Locations</h3>
              <p className="text-4xl font-display font-bold text-gold">{stats.locations_count}</p>
            </div>
            <div className="bg-navy rounded-xl border border-gray-700 p-6 md:col-span-2">
              <h3 className="text-sm text-gray-400 mb-4">Recent Activity</h3>
              <p className="text-gray-300">No recent activity to display</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}