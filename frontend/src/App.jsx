import { useState, useRef, useEffect } from 'react';
import { Target, Terminal, Shield, Zap, RefreshCw, Download, Map as MapIcon } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Polyline, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Custom neon markers
const targetIcon = L.divIcon({
  className: 'bg-transparent',
  html: '<div class="w-4 h-4 rounded-full bg-cyan-400 shadow-[0_0_15px_#00F3FF] border-2 border-white animate-pulse"></div>',
  iconSize: [16, 16],
  iconAnchor: [8, 8]
});

const dropoffIcon = L.divIcon({
  className: 'bg-transparent',
  html: '<div class="w-4 h-4 rounded-full bg-pink-500 shadow-[0_0_15px_#FF0055] border-2 border-white"></div>',
  iconSize: [16, 16],
  iconAnchor: [8, 8]
});

// Component to recenter map dynamically
function MapUpdater({ center }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center);
  }, [center, map]);
  return null;
}

export default function App() {
  const [loading, setLoading] = useState(false);
  const [isSalted, setIsSalted] = useState(false);
  const [cloakPrecision, setCloakPrecision] = useState(0);
  const [targetLat, setTargetLat] = useState(40.7725);
  const [targetLon, setTargetLon] = useState(-73.9600);
  const [targetTime, setTargetTime] = useState("2014-10-12 09:15:00");
  const [radiusM, setRadiusM] = useState(250);
  const [windowMin, setWindowMin] = useState(15);
  
  const [results, setResults] = useState(null);
  const [logs, setLogs] = useState([]);
  const logsEndRef = useRef(null);

  const addLog = (msg) => {
    setLogs(prev => [...prev, `[sys] ${msg}`]);
  };

  const sleep = (ms) => new Promise(r => setTimeout(r, ms));

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const executeAttack = async () => {
    setLoading(true);
    setResults(null);
    setLogs([]);
    
    addLog(`Initiating spatial query (r=${radiusM}m)...`);
    await sleep(600);
    
    try {
      const res = await fetch('http://localhost:8000/api/attack', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_lat: targetLat,
          target_lon: targetLon,
          target_time: targetTime,
          radius_m: radiusM,
          window_min: windowMin,
          crack_hack_license: false,
          cloak_precision: cloakPrecision > 0 ? cloakPrecision : null,
          is_salted: isSalted
        })
      });
      const data = await res.json();
      
      addLog(`${data.phase1_candidates || 0} candidates found in temporal delta.`);
      await sleep(800);
      
      if (data.phase1_candidates > 0 && !isSalted) {
         addLog(`Allocating CUDA cores for MD5 Rainbow Table...`);
         await sleep(1200);
         if (data.matched_trips && data.matched_trips.length > 0) {
            const firstMatch = data.matched_trips[0].medallion_hash.substring(0, 8);
            addLog(`Medallion hash cracked! [MD5: ${firstMatch}... -> ${data.cracked_medallion}]`);
         } else {
            addLog(`No exact match found in rainbow table.`);
         }
      } else if (isSalted) {
         addLog(`FATAL: Hashes are salted. Rainbow table generation impossible.`);
      }
      
      setResults(data);
    } catch (err) {
      addLog(`ERROR: Connection to KERNEL failed.`);
      console.error(err);
    }
    setLoading(false);
  };

  const downloadCsv = () => {
    if (!results || !results.matched_trips) return;
    
    const headers = ["MD5_HASH", "CRACKED_MEDALLION", "PICKUP_LAT", "PICKUP_LON", "PICKUP_TIME", "DROPOFF_LAT", "DROPOFF_LON", "DROPOFF_TIME", "FARE"];
    
    const rows = results.matched_trips.map(trip => [
      trip.medallion_hash,
      results.cracked_medallion || "[PROTECTED]",
      trip.pickup_latitude,
      trip.pickup_longitude,
      trip.pickup_datetime,
      trip.dropoff_latitude,
      trip.dropoff_longitude,
      trip.dropoff_datetime,
      trip.fare_amount
    ]);
    
    const csvContent = "data:text/csv;charset=utf-8," 
      + headers.join(",") + "\n" 
      + rows.map(e => e.join(",")).join("\n");
      
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "de-anonymized_dossier.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Safe parsing for map center
  const mapCenter = [isNaN(targetLat) ? 40.7725 : targetLat, isNaN(targetLon) ? -73.9600 : targetLon];

  return (
    <div className="min-h-screen bg-[#050505] text-[#E0FFFF] font-mono relative overflow-x-hidden selection:bg-pink-500 selection:text-black flex flex-col">
      {/* Background Cyber Glow */}
      <div className="fixed top-0 left-1/4 w-[600px] h-[300px] bg-cyan-500/5 blur-[140px] pointer-events-none -z-10" />
      <div className="fixed bottom-10 right-10 w-[500px] h-[400px] bg-pink-500/5 blur-[160px] pointer-events-none -z-10" />

      {/* Header */}
      <header className="w-full px-6 py-3 border-b border-cyan-500/30 bg-black/90 flex justify-between items-center z-40 shrink-0">
        <div className="flex items-center gap-4">
          <div className="flex items-center justify-center w-8 h-8 border border-cyan-400 bg-cyan-950/40 text-cyan-400 shadow-[0_0_10px_rgba(0,243,255,0.4)]">
            <Target size={18} />
          </div>
          <div>
            <h1 className="text-lg font-black tracking-widest text-cyan-400 drop-shadow-[0_0_8px_rgba(0,243,255,0.8)]">NYC_TAXI // RE-ID_CORE</h1>
            <div className="text-[10px] text-zinc-400 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-ping" />
              v4.2.09 // KERNEL: EXPLOIT_ONLINE
            </div>
          </div>
        </div>
      </header>

      {/* Main Layout */}
      <div className="flex flex-col lg:flex-row flex-1 min-h-0">
        
        {/* Sidebar */}
        <aside className="w-full lg:w-80 bg-black/95 border-r border-cyan-500/30 p-4 shrink-0 shadow-[4px_0_24px_rgba(0,0,0,0.9)] z-30 overflow-y-auto">
          <div className="pb-3 mb-4 border-b border-cyan-500/30">
            <div className="flex items-center gap-2 text-pink-500 text-sm font-bold tracking-widest">
              <Target size={16} /> SECTOR // MANHATTAN
            </div>
          </div>

          <div className="space-y-4">
            <div className="text-[11px] text-cyan-400 font-bold tracking-widest">// TARGET VECTORS</div>
            <div>
              <label className="text-[10px] text-zinc-400">LATITUDE [N]</label>
              <input value={targetLat} onChange={e=>setTargetLat(parseFloat(e.target.value))} className="w-full bg-black border border-cyan-500/50 text-cyan-300 text-xs px-2 py-1.5 focus:outline-none focus:border-cyan-400" />
            </div>
            <div>
              <label className="text-[10px] text-zinc-400">LONGITUDE [W]</label>
              <input value={targetLon} onChange={e=>setTargetLon(parseFloat(e.target.value))} className="w-full bg-black border border-cyan-500/50 text-cyan-300 text-xs px-2 py-1.5 focus:outline-none focus:border-cyan-400" />
            </div>
            <div>
              <label className="text-[10px] text-zinc-400">TIMESTAMP [UTC]</label>
              <input value={targetTime} onChange={e=>setTargetTime(e.target.value)} className="w-full bg-black border border-cyan-500/50 text-cyan-300 text-xs px-2 py-1.5 focus:outline-none focus:border-cyan-400" />
            </div>
            <div className="grid grid-cols-2 gap-2 mt-2">
              <div>
                <label className="text-[10px] text-zinc-400">RADIUS [m]</label>
                <input type="number" value={radiusM} onChange={e=>setRadiusM(parseInt(e.target.value))} className="w-full bg-black border border-cyan-500/50 text-cyan-300 text-xs px-2 py-1.5 focus:outline-none focus:border-cyan-400" />
              </div>
              <div>
                <label className="text-[10px] text-zinc-400">WINDOW [±min]</label>
                <input type="number" value={windowMin} onChange={e=>setWindowMin(parseInt(e.target.value))} className="w-full bg-black border border-cyan-500/50 text-cyan-300 text-xs px-2 py-1.5 focus:outline-none focus:border-cyan-400" />
              </div>
            </div>

            <div className="pt-4 border-t border-zinc-800 space-y-3">
              <div className="flex justify-between items-center text-xs">
                <div>
                  <div className="text-zinc-300 font-bold text-[11px]">SALTED HASHES</div>
                  <div className="text-[9px] text-cyan-400">{isSalted ? "ENABLED // SHA-256" : "DISABLED"}</div>
                </div>
                <button onClick={() => setIsSalted(!isSalted)} className={`w-9 h-5 border flex items-center px-0.5 transition-colors ${isSalted ? 'bg-cyan-950 border-cyan-400' : 'bg-black border-zinc-600'}`}>
                  <div className={`w-3.5 h-3.5 transition-transform ${isSalted ? 'bg-cyan-400 translate-x-4 shadow-[0_0_8px_#00F3FF]' : 'bg-zinc-500'}`} />
                </button>
              </div>

              <div>
                <div className="flex justify-between items-center text-xs mb-1">
                  <div>
                    <div className="text-zinc-300 font-bold text-[11px]">SPATIAL CLOAKING</div>
                    <div className="text-[9px] text-pink-400">{cloakPrecision ? `ACTIVE // EPSILON: ${cloakPrecision}` : "DISABLED"}</div>
                  </div>
                </div>
                <input type="range" min="0" max="4" value={cloakPrecision} onChange={e=>setCloakPrecision(parseInt(e.target.value))} className="w-full accent-pink-500" />
              </div>
            </div>

            <div className="mt-8">
              <button onClick={executeAttack} disabled={loading} className="w-full py-3 bg-pink-950/30 border-2 border-pink-500 text-pink-300 hover:text-white hover:bg-pink-600 font-bold tracking-widest text-sm flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(255,0,85,0.4)] transition-all disabled:opacity-50 disabled:cursor-not-allowed">
                {loading ? <RefreshCw className="animate-spin" size={18} /> : <Zap size={18} />}
                EXECUTE RE-ID ATTACK
              </button>
            </div>
          </div>
        </aside>

        {/* Main Area */}
        <main className="flex-1 overflow-y-auto flex flex-col">
          
          {/* Cyber Map (Always visible) */}
          <div className="h-[40vh] min-h-[300px] w-full border-b border-cyan-500/30 relative z-0">
             <div className="absolute top-4 left-4 z-[400] bg-black/80 border border-cyan-500/50 px-3 py-1 text-[10px] tracking-widest text-cyan-400 flex items-center gap-2 shadow-[0_0_10px_rgba(0,243,255,0.2)]">
                <MapIcon size={12} /> TACTICAL MAPPING
             </div>
             
             {/* Note: In a real app we'd hide default leaflet controls or style them via CSS, 
                 for this demo we just rely on standard zoom controls. */}
             <MapContainer center={mapCenter} zoom={13} style={{ height: '100%', width: '100%', backgroundColor: '#050505' }} zoomControl={false}>
                <MapUpdater center={mapCenter} />
                
                {/* Standard OSM with CSS inversion for Dark Mode (No API Key Required) */}
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                  className="map-tiles"
                />
                
                {/* Target Pickup Location */}
                <Marker position={mapCenter} icon={targetIcon} />
                
                {/* If attack is successful and we have matched trips, draw lines to dropoffs */}
                {results?.matched_trips?.map((trip, idx) => (
                  <div key={idx}>
                     <Marker position={[trip.dropoff_latitude, trip.dropoff_longitude]} icon={dropoffIcon} />
                     <Polyline 
                        positions={[
                           [trip.pickup_latitude, trip.pickup_longitude], 
                           [trip.dropoff_latitude, trip.dropoff_longitude]
                        ]} 
                        pathOptions={{ color: '#00F3FF', weight: 2, dashArray: '5, 5', opacity: 0.6 }} 
                     />
                  </div>
                ))}
             </MapContainer>
          </div>

          <div className="flex-1 p-6 flex flex-col space-y-6">
            
            {/* Metrics & Data (Only visible after attack) */}
            {results ? (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <MetricCard title="CANDIDATES" value={results.phase1_candidates} icon={<Shield size={16} className="text-cyan-400" />} />
                  <MetricCard title="KEYSPACE SIZE" value={results.rainbow_table_stats?.medallion_keyspace || '0'} icon={<Target size={16} className="text-cyan-400" />} />
                  <MetricCard title="BUILD TIME (ms)" value={results.rainbow_table_stats?.medallion_build_time_s === "∞" ? "∞" : (results.rainbow_table_stats?.medallion_build_time_s * 1000).toFixed(1)} icon={<Terminal size={16} className="text-pink-500" />} borderColor="border-pink-500/40" />
                  <MetricCard title="MEMORY (MB)" value={results.rainbow_table_stats?.memory_usage_mb || 0} icon={<Terminal size={16} className="text-pink-500" />} borderColor="border-pink-500/40" />
                </div>

                <div className="bg-black/80 border border-cyan-500/40 p-4 shadow-[0_0_20px_rgba(0,243,255,0.1)] flex-1">
                  <div className="flex justify-between items-center mb-4">
                    <h3 className="text-cyan-300 font-bold tracking-widest flex items-center gap-2">
                      <Terminal size={16} /> DE-ANONYMIZED TRIPS
                    </h3>
                    <button onClick={downloadCsv} className="px-3 py-1 bg-cyan-950/40 border border-cyan-500 text-cyan-400 hover:bg-cyan-500 hover:text-black font-bold text-xs flex items-center gap-2 transition-colors">
                      <Download size={14} /> DUMP CSV
                    </button>
                  </div>
                  
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-zinc-950/80 text-zinc-500 tracking-wider">
                        <tr>
                          <th className="p-3">MD5_HASH</th>
                          <th className="p-3">CRACKED_MEDALLION</th>
                          <th className="p-3">PICKUP</th>
                          <th className="p-3">DROPOFF</th>
                          <th className="p-3">FARE</th>
                          <th className="p-3">STATUS</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-zinc-800">
                        {results.matched_trips?.map((trip, i) => (
                          <tr key={i} className="hover:bg-cyan-950/20 transition-colors group">
                            <td className="p-3 text-pink-400 font-bold">{trip.medallion_hash.substring(0, 8)}...</td>
                            <td className="p-3 text-cyan-300">{results.cracked_medallion || "[PROTECTED]"}</td>
                            <td className="p-3 text-zinc-400">
                              {trip.pickup_latitude.toFixed(4)}, {trip.pickup_longitude.toFixed(4)}<br/>
                              <span className="text-[10px] text-zinc-600">{trip.pickup_datetime}</span>
                            </td>
                            <td className="p-3 text-zinc-400">
                              {trip.dropoff_latitude.toFixed(4)}, {trip.dropoff_longitude.toFixed(4)}<br/>
                              <span className="text-[10px] text-zinc-600">{trip.dropoff_datetime}</span>
                            </td>
                            <td className="p-3 text-cyan-300 font-bold">${trip.fare_amount}</td>
                            <td className="p-3">
                              <span className={`px-2 py-1 border-l-2 text-[10px] tracking-wider ${results.cracked_medallion !== '[PROTECTED]' ? 'bg-cyan-950/40 text-cyan-400 border-cyan-400' : 'bg-amber-950/40 text-amber-400 border-amber-400'}`}>
                                {results.cracked_medallion !== '[PROTECTED]' ? 'DE-ANONYMIZED' : 'CLOAKED'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {results.matched_trips?.length === 0 && (
                      <div className="p-4 text-center text-zinc-500 italic">No trips matched the spatial/temporal filters.</div>
                    )}
                  </div>
                </div>
              </>
            ) : (
              !loading && (
                <div className="flex-1 flex items-center justify-center py-12">
                    <div className="text-zinc-600 tracking-widest text-sm flex flex-col items-center gap-4">
                        <Target size={48} className="opacity-20" />
                        <span>SYSTEM STANDBY // AWAITING COMMAND</span>
                    </div>
                </div>
              )
            )}
            
            {/* Live Terminal Logs */}
            <div className="bg-black border border-zinc-800 p-4 h-40 overflow-y-auto text-[11px] font-mono shadow-[inset_0_0_10px_rgba(0,0,0,0.5)] shrink-0">
               <div className="text-zinc-600 mb-2 uppercase tracking-widest">// TERMINAL OUTPUT</div>
               {logs.map((log, i) => (
                  <div key={i} className={`mb-1 ${log.includes("FATAL") || log.includes("ERROR") ? "text-pink-500" : log.includes("cracked") ? "text-cyan-400 font-bold" : "text-zinc-400"}`}>
                     {log}
                  </div>
               ))}
               {loading && <div className="text-cyan-400 animate-pulse mt-1">_</div>}
               <div ref={logsEndRef} />
            </div>
            
          </div>
        </main>
      </div>
    </div>
  );
}

function MetricCard({ title, value, icon, borderColor = "border-cyan-500/40" }) {
  return (
    <div className={`bg-black/80 border ${borderColor} p-4 shadow-[inset_0_0_12px_rgba(0,243,255,0.08)]`}>
      <div className="flex items-center justify-between text-[11px] text-zinc-400 tracking-wider mb-2">
        <span>{title}</span>
        {icon}
      </div>
      <div className="text-2xl font-black text-white">{value}</div>
    </div>
  );
}
