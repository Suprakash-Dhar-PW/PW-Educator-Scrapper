import { useState, useEffect } from 'react';
import { 
  Search, MapPin, BookOpen, GraduationCap, 
  CheckCircle, AlertCircle, ChevronDown, ChevronUp,
  Camera, Video, Briefcase, Globe, Users, Activity, Settings, Bookmark, RefreshCw
} from 'lucide-react';
import { apiClient, SearchResponse, SearchResult } from './apiClient';

export default function App() {
  const [locations, setLocations] = useState<string[]>([]);
  const [tracks, setTracks] = useState<string[]>([]);
  const [subjects, setSubjects] = useState<string[]>([]);

  const [location, setLocation] = useState("");
  const [track, setTrack] = useState("");
  const [subject, setSubject] = useState("");
  const [forceRefresh, setForceRefresh] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<SearchResponse | null>(null);

  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set());

  // Initial Data Fetch
  useEffect(() => {
    apiClient.getLocations().then(setLocations).catch(console.error);
    apiClient.getTracks().then(setTracks).catch(console.error);
  }, []);

  // Fetch subjects when track changes
  useEffect(() => {
    if (track) {
      apiClient.getSubjects(track).then(data => {
        setSubjects(data);
        if (!data.includes(subject)) setSubject("");
      }).catch(console.error);
    } else {
      setSubjects([]);
      setSubject("");
    }
  }, [track]);

  const handleSearch = async () => {
    if (!location || !track || !subject) return;

    setIsLoading(true);
    setError(null);
    
    try {
      const data = await apiClient.search({ location, track, subject, force_refresh: forceRefresh });
      setResponse(data);
    } catch (err: any) {
      setError(err.message || "Failed to fetch educators");
      setResponse(null);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleEvidence = (id: string) => {
    const newExpanded = new Set(expandedCards);
    if (newExpanded.has(id)) newExpanded.delete(id);
    else newExpanded.add(id);
    setExpandedCards(newExpanded);
  };

  const formatNumber = (num?: number) => {
    if (!num) return null;
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  const getPlatformIcon = (platform: string) => {
    const p = platform.toLowerCase();
    if (p.includes("instagram")) return <Camera size={14} className="mr-1" />;
    if (p.includes("youtube")) return <Video size={14} className="mr-1" />;
    if (p.includes("linkedin")) return <Briefcase size={14} className="mr-1" />;
    return <Globe size={14} className="mr-1" />;
  };

  const getVerificationBadge = (score: number) => {
    if (score >= 80) return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800"><CheckCircle size={12}/> Highly Verified</span>;
    if (score >= 50) return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"><CheckCircle size={12}/> Likely Match</span>;
    return <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800"><AlertCircle size={12}/> Uncertain</span>;
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans text-slate-900">
      
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-200 flex flex-col hidden md:flex">
        <div className="p-6 border-b border-slate-100">
          <div className="flex items-center gap-2 text-brand-600 font-bold text-lg">
            <Activity size={24} />
            <span>Educator Discovery</span>
          </div>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          <a href="#" className="flex items-center gap-3 px-3 py-2 bg-brand-50 text-brand-600 rounded-md font-medium">
            <Search size={18} />
            Discover Educators
          </a>
          <a href="#" className="flex items-center gap-3 px-3 py-2 text-slate-600 hover:bg-slate-50 rounded-md font-medium">
            <Bookmark size={18} />
            Saved Educators
          </a>
        </nav>
        <div className="p-4 border-t border-slate-100">
          <a href="#" className="flex items-center gap-3 px-3 py-2 text-slate-600 hover:bg-slate-50 rounded-md font-medium mb-4">
            <Settings size={18} />
            Settings
          </a>
          <div className="flex items-center gap-2 px-3 text-xs text-slate-500">
            <div className="w-2 h-2 rounded-full bg-emerald-500"></div>
            API Connected
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-8 py-5 flex items-center justify-between shadow-sm z-10">
          <div>
            <h1 className="text-2xl font-semibold text-slate-800">Discover Educators</h1>
            <p className="text-sm text-slate-500 mt-1">Evidence-based teacher search across multiple platforms</p>
          </div>
          <div className="md:hidden">
            {/* Mobile menu button could go here */}
          </div>
        </header>

        <div className="flex-1 overflow-auto p-8">
          <div className="max-w-6xl mx-auto space-y-8">
            
            {/* Search Workspace */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                
                <div className="flex flex-col gap-2">
                  <label className="text-sm font-semibold text-slate-700">Location</label>
                  <select 
                    className="p-2.5 border border-slate-300 rounded-lg bg-slate-50 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition-all"
                    value={location} onChange={e => setLocation(e.target.value)}
                  >
                    <option value="">Select a city...</option>
                    {locations.map(loc => <option key={loc} value={loc}>{loc}</option>)}
                  </select>
                </div>

                <div className="flex flex-col gap-2">
                  <label className="text-sm font-semibold text-slate-700">Track</label>
                  <select 
                    className="p-2.5 border border-slate-300 rounded-lg bg-slate-50 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition-all"
                    value={track} onChange={e => setTrack(e.target.value)}
                  >
                    <option value="">Select track...</option>
                    {tracks.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>

                <div className="flex flex-col gap-2">
                  <label className="text-sm font-semibold text-slate-700">Subject</label>
                  <select 
                    className="p-2.5 border border-slate-300 rounded-lg bg-slate-50 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none transition-all disabled:opacity-50"
                    value={subject} onChange={e => setSubject(e.target.value)} disabled={!track}
                  >
                    <option value="">Select subject...</option>
                    {subjects.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              </div>

              <div className="flex flex-col sm:flex-row justify-between items-center pt-4 border-t border-slate-100 gap-4">
                <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer select-none">
                  <input type="checkbox" className="rounded text-brand-600 focus:ring-brand-500 w-4 h-4" checked={forceRefresh} onChange={e => setForceRefresh(e.target.checked)} />
                  Bypass cache and force refresh
                </label>
                
                <div className="flex items-center gap-4 w-full sm:w-auto">
                  {response?.last_updated && (
                    <span className="text-xs text-slate-500 hidden md:block">
                      Last updated: {new Date(response.last_updated).toLocaleString()}
                    </span>
                  )}
                  <button 
                    className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-2.5 bg-brand-600 hover:bg-brand-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
                    disabled={!location || !track || !subject || isLoading}
                    onClick={handleSearch}
                  >
                    {isLoading ? <RefreshCw className="animate-spin" size={18} /> : <Search size={18} />}
                    {isLoading ? 'Discovering...' : 'Find Educators'}
                  </button>
                </div>
              </div>
            </div>

            {/* Error State */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-xl flex items-start gap-3">
                <AlertCircle className="shrink-0 mt-0.5" size={20} />
                <div>
                  <h3 className="font-semibold">Search Failed</h3>
                  <p className="text-sm mt-1">{error}</p>
                </div>
              </div>
            )}

            {/* Results Header */}
            {response && !isLoading && (
              <div className="flex justify-between items-end">
                <h2 className="text-lg font-semibold text-slate-800">
                  {response.total_results} Educators Found
                </h2>
              </div>
            )}

            {/* Empty State */}
            {response && !isLoading && response.results.length === 0 && (
              <div className="bg-white border border-slate-200 rounded-xl p-12 flex flex-col items-center justify-center text-center">
                <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4 text-slate-400">
                  <Search size={32} />
                </div>
                <h3 className="text-lg font-semibold text-slate-800">No educators found</h3>
                <p className="text-slate-500 mt-2 max-w-md">We couldn't find verified educators matching your exact criteria. Try broadening your search or forcing a refresh.</p>
              </div>
            )}

            {/* Results Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {response?.results.map((ed: SearchResult) => {
                const isExpanded = expandedCards.has(ed.educator_id);
                const totalFollowers = ed.profiles.reduce((acc, p) => acc + (p.followers || p.subscribers || p.connections || 0), 0);

                return (
                  <div key={ed.educator_id} className="bg-white border border-slate-200 rounded-xl overflow-hidden hover:shadow-md transition-shadow">
                    <div className="p-6 border-b border-slate-100 flex items-start gap-4">
                      <div className="w-12 h-12 bg-brand-100 text-brand-700 rounded-full flex items-center justify-center font-bold text-xl shrink-0">
                        {ed.name.charAt(0).toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-lg font-semibold text-slate-900 truncate">{ed.name}</h3>
                        <div className="mt-1 flex flex-wrap gap-2">
                          {getVerificationBadge(ed.scores.overall)}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-brand-600">{ed.scores.overall.toFixed(1)}</div>
                        <div className="text-xs text-slate-500 font-medium">RELEVANCE</div>
                      </div>
                    </div>

                    <div className="p-6 bg-slate-50/50">
                      <div className="grid grid-cols-2 gap-y-4 gap-x-2 text-sm text-slate-700">
                        <div className="flex items-center gap-2">
                          <MapPin size={16} className="text-slate-400" />
                          <span className="truncate">{ed.location}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <GraduationCap size={16} className="text-slate-400" />
                          <span className="truncate">{ed.track}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <BookOpen size={16} className="text-slate-400" />
                          <span className="truncate">{ed.subjects.join(", ") || subject}</span>
                        </div>
                        {totalFollowers > 0 && (
                          <div className="flex items-center gap-2 font-medium text-slate-900">
                            <Users size={16} className="text-slate-400" />
                            <span>~{formatNumber(totalFollowers)} Audience</span>
                          </div>
                        )}
                      </div>

                      {ed.profiles && ed.profiles.length > 0 && (
                        <div className="mt-6 flex flex-wrap gap-2">
                          {ed.profiles.map((p, idx) => (
                            <a key={idx} href={p.url} target="_blank" rel="noreferrer" 
                               className="inline-flex items-center px-3 py-1.5 bg-white border border-slate-200 hover:border-brand-300 hover:text-brand-600 rounded-lg text-xs font-medium text-slate-600 transition-colors">
                              {getPlatformIcon(p.platform)}
                              {p.platform}
                            </a>
                          ))}
                        </div>
                      )}
                    </div>

                    <div className="border-t border-slate-100 bg-white">
                      <button 
                        className="w-full px-6 py-3 flex items-center justify-between text-sm font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                        onClick={() => toggleEvidence(ed.educator_id)}
                      >
                        <span>Verification & Evidence</span>
                        {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                      </button>
                      
                      {isExpanded && (
                        <div className="px-6 pb-6 pt-2 border-t border-slate-50">
                          <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Ranking Factors</h4>
                          <ul className="space-y-2 mb-6">
                            {ed.scores.reasons.map((reason, idx) => (
                              <li key={idx} className="flex items-start gap-2 text-sm text-slate-700">
                                <CheckCircle size={14} className="text-emerald-500 mt-0.5 shrink-0" />
                                <span>{reason}</span>
                              </li>
                            ))}
                            {ed.scores.reasons.length === 0 && (
                              <li className="text-sm text-slate-500 italic">Score derived from profile metadata.</li>
                            )}
                          </ul>

                          <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Supporting Evidence</h4>
                          <div className="space-y-3">
                            {ed.evidence.map((ev, idx) => (
                              <div key={idx} className="bg-slate-50 rounded-lg p-3 text-xs border border-slate-100">
                                <div className="flex items-center gap-1.5 font-semibold text-slate-700 mb-1">
                                  {getPlatformIcon(ev.platform)}
                                  <span className="capitalize">{ev.dimension} Match</span>
                                </div>
                                <p className="text-slate-600 leading-relaxed">"{ev.text}"</p>
                              </div>
                            ))}
                            {ed.evidence.length === 0 && (
                              <p className="text-sm text-slate-500 italic">No direct text snippets extracted.</p>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

          </div>
        </div>
      </main>
    </div>
  );
}
