import { useEffect, useState } from 'react';
import axios from 'axios';
import { cn } from './lib/utils';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5001/api';

console.log('App component loaded with API_BASE:', API_BASE);

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
      console.log('Fetching data from API:', API_BASE);
      console.log('API_BASE value:', API_BASE);
      
      const [losersRes, oppsRes] = await Promise.all([
        axios.get(`${API_BASE}/losers`),
        axios.get(`${API_BASE}/opportunities`)
      ]);
      
      console.log('Losers response status:', losersRes.status);
      console.log('Losers response data:', losersRes.data);
      console.log('Opportunities response status:', oppsRes.status);
      console.log('Opportunities response data:', oppsRes.data);
      
      // Extract data array from response
      const losersData = Array.isArray(losersRes.data.data) ? losersRes.data.data : [];
      const oppsData = Array.isArray(oppsRes.data.data) ? oppsRes.data.data : [];
      
      console.log('Processed losers count:', losersData.length);
      console.log('Processed opportunities count:', oppsData.length);
      console.log('First loser:', losersData[0]);
      console.log('First opportunity:', oppsData[0]);
      
      setLosers(losersData.slice(0, 10)); // Top 10 losers
      setOpportunities(oppsData.slice(0, 5)); // Top 5 opportunities
      setConnected(true);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch data:', error);
      console.error('Error details:', error.response?.data || error.message);
      setConnected(false);
      setLoading(false);
    }
  };

  const formatPnl = (pnl) => {
    if (pnl >= 0) return `+${pnl.toFixed(2)}%`;
    return `${pnl.toFixed(2)}%`;
  };

  const formatAddress = (address) => {
    return address; // Show full address
  };

  const getExplorerUrl = (address) => {
    return `https://app.hyperliquid.xyz/explorer/address/${address}`;
  };

  const getTradeExplorerUrl = (address, coin, transactionHash) => {
    // If we have a transaction hash, link to the specific transaction
    if (transactionHash && transactionHash !== "0x0000000000000000000000000000000000000000000000000000000000000000") {
      return `https://app.hyperliquid.xyz/explorer/tx/${transactionHash}`;
    }
    // Otherwise, fall back to trader address
    return `https://app.hyperliquid.xyz/explorer/address/${address}`;
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
              <div className="overflow-y-auto h-48 md:h-80">
                {losers.length === 0 ? (
                  <div className="text-gray-400 text-center py-8">
                    Loading traders... (Debug: {losers.length} items)
                  </div>
                ) : (
                  <table className="w-full text-xs">
                    <thead className="bg-gray-900 sticky top-0">
                      <tr className="text-green-400">
                        <th className="text-left p-1">Address</th>
                        <th className="text-right p-1">Account Balance</th>
                        <th className="text-right p-1">30d PnL</th>
                        <th className="text-right p-1">7d PnL</th>
                        <th className="text-right p-1">Last Active</th>
                      </tr>
                    </thead>
                    <tbody>
                      {losers.map((trader, index) => {
                        console.log('Rendering trader:', trader);
                        return (
                          <tr key={trader.address} className="border-b border-gray-800 hover:bg-gray-900">
                            <td className="p-1">
                              <a 
                                href={trader.explorer_url || getExplorerUrl(trader.address)}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-green-400 hover:text-green-300 underline cursor-pointer"
                                title={trader.address}
                              >
                                {trader.address.slice(0, 8)}...{trader.address.slice(-6)}
                              </a>
                            </td>
                            <td className="text-right p-1 text-white font-bold">
                              {trader.formatted_account_value || formatCurrency(trader.account_value)}
                            </td>
                            <td className="text-right p-1 text-red-400 font-bold">
                              {trader.formatted_pnl || formatPnl(trader.roi_30d_percent)}
                            </td>
                            <td className="text-right p-1 text-red-300">
                              {trader.formatted_pnl_7d || "N/A"}
                            </td>
                            <td className="text-right p-1 text-gray-400">
                              {trader.formatted_last_active || "Unknown"}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
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
                      <a 
                        href={getTradeExplorerUrl(opp.trader_address, opp.coin, opp.transaction_hash)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-green-400 hover:text-green-300 underline cursor-pointer"
                      >
                        {formatAddress(opp.trader_address)}
                      </a>
                      <span>opened</span>
                    </div>
                    
                    <div className="flex items-center gap-1 md:gap-2 text-xs md:text-sm mt-1">
                      <a 
                        href={opp.explorer_url || getTradeExplorerUrl(opp.trader_address, opp.coin, opp.transaction_hash)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-cyan-400 hover:text-cyan-300 underline cursor-pointer"
                        title={opp.transaction_hash ? `View transaction: ${opp.transaction_hash}` : `View trader: ${opp.trader_address}`}
                      >
                        {opp.loser_side} {opp.coin}
                      </a>
                      {opp.formatted_size && (
                        <>
                          <span className="text-gray-400">@</span>
                          <span className="text-white">{opp.formatted_size}</span>
                        </>
                      )}
                      <span className="text-gray-400">at</span>
                      <span className="text-white">{opp.formatted_price || `$${opp.loser_entry_price.toFixed(4)}`}</span>
                      {opp.formatted_leverage && (
                        <>
                          <span className="text-gray-400">({opp.formatted_leverage})</span>
                        </>
                      )}
                      <span className="text-gray-400">•</span>
                      <span className="text-yellow-400">{opp.formatted_time_ago}</span>
                    </div>
                    
                    <div className="flex items-center gap-1 md:gap-2 text-xs md:text-sm mt-1">
                      <span>→</span>
                      <span className="text-green-400">SUGGESTION:</span>
                      <span className="text-yellow-400 font-bold">{opp.suggested_side} {opp.coin}</span>
                      <span className="text-gray-400">({opp.confidence_score}% confidence)</span>
                      {opp.formatted_pnl && (
                        <>
                          <span className="text-gray-400">•</span>
                          <span className={opp.unrealized_pnl >= 0 ? "text-green-400" : "text-red-400"}>
                            PnL: {opp.formatted_pnl}
                          </span>
                        </>
                      )}
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