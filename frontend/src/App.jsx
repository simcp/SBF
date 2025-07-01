import { useEffect, useState } from 'react';
import axios from 'axios';
import { cn } from './lib/utils';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5001/api';

function App() {
  const [losers, setLosers] = useState([]);
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      console.log('Fetching data from API...');
      const [losersRes, oppsRes] = await Promise.all([
        axios.get(`${API_BASE}/losers`),
        axios.get(`${API_BASE}/opportunities`)
      ]);
      
      console.log('Losers response:', losersRes.data);
      console.log('Opportunities response:', oppsRes.data);
      
      const losersData = losersRes.data.data || losersRes.data; // Handle both data formats
      const oppsData = oppsRes.data.data || oppsRes.data;
      
      console.log('Setting losers:', losersData.slice(0, 10));
      console.log('Setting opportunities:', oppsData.slice(0, 5));
      
      setLosers(losersData.slice(0, 10)); // Top 10 losers
      setOpportunities(oppsData.slice(0, 5)); // Top 5 opportunities
      setConnected(true);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      setConnected(false);
      setLoading(false);
    }
  };

  const formatPnl = (pnl) => {
    if (pnl >= 0) return `+${pnl.toFixed(2)}%`;
    return `${pnl.toFixed(2)}%`;
  };

  const formatAddress = (address) => {
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  const formatCurrency = (amount) => {
    if (amount >= 1000000) return `$${(amount / 1000000).toFixed(1)}M`;
    if (amount >= 1000) return `$${(amount / 1000).toFixed(1)}K`;
    return `$${amount.toFixed(0)}`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-green-400 font-mono flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-green-400 font-mono p-2 md:p-4">
      {/* Header */}
      <div className="border border-green-400 mb-4">
        <div className="flex justify-between items-center p-2 bg-green-400 text-black">
          <div className="flex items-center gap-2">
            <span className="text-red-600">🔴</span>
            <span className="font-bold">FADE THE LOSERS</span>
          </div>
          <div className="flex items-center gap-2">
            <span>{connected ? 'Connected' : 'Disconnected'}</span>
            <span className={cn("w-2 h-2 rounded-full", connected ? "bg-green-600" : "bg-red-600")}></span>
            <span>Mainnet</span>
          </div>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 p-2 md:p-4">
          {/* Worst Traders */}
          <div>
            <div className="border border-green-400 h-64 md:h-96">
              <div className="bg-green-400 text-black p-2 font-bold">
                WORST TRADERS ▼ 30d PnL
              </div>
              <div className="p-2 space-y-1 overflow-y-auto h-48 md:h-80">
                {losers.length === 0 ? (
                  <div className="text-gray-400 text-center py-8">
                    Loading traders... (Debug: {losers.length} items)
                  </div>
                ) : (
                  losers.map((trader, index) => {
                    console.log('Rendering trader:', trader);
                    return (
                      <div key={trader.address} className="flex justify-between items-center text-xs md:text-sm">
                        <div className="flex items-center gap-2">
                          <span className="text-yellow-400">#{index + 1}</span>
                          <span>{formatAddress(trader.address)}</span>
                          <span className="text-red-400">[{formatPnl(trader.roi_30d_percent)}]</span>
                          <span className="text-red-400">📉</span>
                        </div>
                        <div className="text-xs md:text-sm text-gray-400">
                          {formatCurrency(trader.account_value)}
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          </div>

          {/* Opportunities */}
          <div>
            <div className="border border-green-400 h-64 md:h-96">
              <div className="bg-green-400 text-black p-2 font-bold">
                OPPORTUNITIES
              </div>
              <div className="p-2 space-y-2 overflow-y-auto h-48 md:h-80">
                {opportunities.map((opp, index) => (
                  <div key={index} className="border border-yellow-400 p-2">
                    <div className="flex items-center gap-1 md:gap-2 text-xs md:text-sm">
                      <span className="text-red-400">🚨</span>
                      <span className="text-yellow-400">NEW:</span>
                      <span>{formatAddress(opp.trader_address)}</span>
                      <span>opened</span>
                      <span className="text-cyan-400">{opp.loser_side}</span>
                      <span className="text-cyan-400">{opp.coin}</span>
                    </div>
                    <div className="flex items-center gap-1 md:gap-2 text-xs md:text-sm mt-1">
                      <span>→</span>
                      <span className="text-green-400">SUGGESTION:</span>
                      <span className="text-yellow-400 font-bold">{opp.suggested_side} {opp.coin}</span>
                      <span className="text-gray-400">({opp.confidence_score}% confidence)</span>
                    </div>
                  </div>
                ))}
                
                {opportunities.length === 0 && (
                  <div className="text-gray-400 text-center py-8">
                    No active opportunities
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Status Bar */}
        <div className="border-t border-green-400 p-2 text-xs flex flex-col md:flex-row justify-between gap-2 md:gap-0">
          <div>
            Active Losers: {losers.length} | 
            Opportunities: {opportunities.length} |
            Last Update: {new Date().toLocaleTimeString()}
          </div>
          <div>
            Auto-refresh: 30s
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;