import { useState, useEffect } from 'react';
import {
  Search, MapPin, BookOpen, GraduationCap,
  AlertCircle, CheckCircle2, ChevronDown, ChevronUp,
  Camera, Video, Briefcase, Globe, Users, Activity, Settings, Bookmark,
  RefreshCw, X, ExternalLink, ShieldCheck, Download, Trash2, Sliders,
  Server, HelpCircle
} from 'lucide-react';
import { apiClient, SearchResponse, SearchResult } from './apiClient';

const formatNumber = (num?: number) => {
  if (!num) return null;
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
  return num.toString();
};

const getPlatformIcon = (platform: string) => {
  const p = platform.toLowerCase();
  if (p.includes("instagram")) return <Camera size={14} className="mr-1 text-pink-600" />;
  if (p.includes("youtube")) return <Video size={14} className="mr-1 text-red-600" />;
  if (p.includes("linkedin")) return <Briefcase size={14} className="mr-1 text-blue-600" />;
  return <Globe size={14} className="mr-1 text-slate-600" />;
};

export default function App() {
  const [activeTab, setActiveTab] = useState<'discover' | 'saved' | 'settings'>('discover');
  
  // Locations, tracks, subjects
  const [locations, setLocations] = useState<string[]>([]);
  const [tracks, setTracks] = useState<string[]>([]);
  const [subjects, setSubjects] = useState<string[]>([]);

  // Search parameters
  const [location, setLocation] = useState("");
  const [track, setTrack] = useState("");
  const [subject, setSubject] = useState("");
  
  // Advanced settings (collapsed by default)
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [forceRefresh, setForceRefresh] = useState(false);
  const [targetCount, setTargetCount] = useState(50);
  const [budgetSearches, setBudgetSearches] = useState(5);
  const [budgetEnrichments, setBudgetEnrichments] = useState(20);
  const [budgetCandidates, setBudgetCandidates] = useState(60);

  // Search execution state
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<SearchResponse | null>(null);

  // Saved educators state (persisted in Supabase PostgreSQL)
  const [savedEducators, setSavedEducators] = useState<SearchResult[]>([]);

  // Comparison state
  const [comparedEducators, setComparedEducators] = useState<SearchResult[]>([]);
  const [showCompareModal, setShowCompareModal] = useState(false);

  // Evidence modal state
  const [evidenceModalEd, setEvidenceModalEd] = useState<SearchResult | null>(null);

  // Settings & Diagnostics state
  const [diagnosticsData, setDiagnosticsData] = useState<any>(null);
  const [cacheClearMessage, setCacheClearMessage] = useState<string | null>(null);

  // Sync saved educators from Supabase PostgreSQL on mount
  useEffect(() => {
    apiClient.getSavedEducators()
      .then(res => {
        if (res && res.items) {
          const mapped: SearchResult[] = res.items.map(item => ({
            educator_id: item.id,
            full_name: item.name,
            professional_headline: item.professional_headline,
            current_job_title: item.current_job_title,
            current_employer: item.current_employer,
            location: item.location || "India",
            track: item.track || "IIT-JEE",
            subjects: item.subjects || [],
            profiles: item.profiles || (item.profile_url ? [{ platform: item.source_platform || "Web", url: item.profile_url }] : []),
            scores: { overall: 0, components: {}, reasons: [] },
            evidence: [],
            pw_exclusion_status: item.pw_exclusion_status || "ELIGIBLE",
            identity_confidence: 1.0,
            employment_verification_status: "verified",
            source_platform: item.source_platform || "Web",
            profile_url: item.profile_url || ""
          }));
          setSavedEducators(mapped);
          try {
            localStorage.setItem('saved_educators', JSON.stringify(mapped));
          } catch {}
        }
      })
      .catch(err => {
        console.warn("Could not load saved educators from Supabase, checking local backup:", err);
        try {
          const local = localStorage.getItem('saved_educators');
          if (local) setSavedEducators(JSON.parse(local));
        } catch {}
      });
  }, []);

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

  // Fetch diagnostics on settings tab
  useEffect(() => {
    if (activeTab === 'settings') {
      apiClient.getDiagnostics().then(setDiagnosticsData).catch(console.error);
    }
  }, [activeTab]);

  const handleSearch = async () => {
    if (!location || !track || !subject) return;

    setIsLoading(true);
    setError(null);

    try {
      const data = await apiClient.search({
        location,
        track,
        subject,
        force_refresh: forceRefresh,
        target_count: targetCount,
        budget_max_anakin_searches: budgetSearches,
        budget_max_enrichments: budgetEnrichments,
        budget_max_candidates: budgetCandidates,
      });
      setResponse(data);
      if (data.results && data.results.length > 0) {
        apiClient.recordExposure(data.results.map(r => r.educator_id));
      }
    } catch (err: any) {
      setError(err.message || "Failed to discover educators. Please check connection and try again.");
      setResponse(null);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleSaveEducator = async (ed: SearchResult) => {
    const isSaved = savedEducators.some(s => s.educator_id === ed.educator_id);
    if (isSaved) {
      // Optimistic update
      const updated = savedEducators.filter(s => s.educator_id !== ed.educator_id);
      setSavedEducators(updated);
      try {
        localStorage.setItem('saved_educators', JSON.stringify(updated));
        await apiClient.unsaveEducator(ed.educator_id);
      } catch (e) {
        console.error("Failed to unsave educator from Supabase:", e);
      }
    } else {
      // Optimistic update
      const updated = [...savedEducators, ed];
      setSavedEducators(updated);
      try {
        localStorage.setItem('saved_educators', JSON.stringify(updated));
        await apiClient.saveEducator(ed.educator_id);
      } catch (e) {
        console.error("Failed to save educator to Supabase:", e);
      }
    }
  };

  const toggleCompareEducator = (ed: SearchResult) => {
    const isCompared = comparedEducators.some(c => c.educator_id === ed.educator_id);
    if (isCompared) {
      setComparedEducators(comparedEducators.filter(c => c.educator_id !== ed.educator_id));
    } else {
      if (comparedEducators.length >= 4) {
        alert("You can compare up to 4 educators at a time.");
        return;
      }
      setComparedEducators([...comparedEducators, ed]);
    }
  };

  const handleClearCache = async () => {
    try {
      const res = await apiClient.clearCache();
      setCacheClearMessage(res.message || "Cache cleared successfully.");
      setTimeout(() => setCacheClearMessage(null), 4000);
    } catch (err: any) {
      setCacheClearMessage(`Error clearing cache: ${err.message}`);
    }
  };

  const exportSavedEducators = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(savedEducators, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `saved_educators_${new Date().toISOString().slice(0, 10)}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const renderCard = (ed: SearchResult, isReview: boolean = false) => {
    const totalFollowers = ed.profiles.reduce((acc, p) => acc + (p.followers || p.subscribers || p.connections || 0), 0);
    const isSaved = savedEducators.some(s => s.educator_id === ed.educator_id);
    const isCompared = comparedEducators.some(c => c.educator_id === ed.educator_id);

    return (
      <div
        key={ed.educator_id}
        className={`bg-white rounded-2xl border ${isReview ? 'border-amber-200 shadow-sm' : 'border-slate-200/80 shadow-sm hover:shadow-md'} transition-all duration-200 flex flex-col justify-between overflow-hidden`}
      >
        <div>
          {/* Header & Identity */}
          <div className={`p-5 border-b border-slate-100 ${isReview ? 'bg-amber-50/40' : 'bg-slate-50/40'}`}>
            <div className="flex items-start gap-3.5">
              <div className="w-12 h-12 rounded-xl bg-brand-100 text-brand-700 font-bold text-lg flex items-center justify-center shrink-0 shadow-sm">
                {ed.full_name ? ed.full_name.charAt(0).toUpperCase() : '?'}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h3 className="text-base font-bold text-slate-900 truncate" title={ed.full_name}>
                    {ed.full_name || "Unknown Educator"}
                  </h3>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-semibold tracking-wide shrink-0 ${
                    isReview 
                      ? 'bg-amber-100 text-amber-800 border border-amber-200' 
                      : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                  }`}>
                    {isReview ? 'Needs Review' : 'Verified Educator'}
                  </span>
                </div>

                {ed.professional_headline && (
                  <p className="text-xs text-slate-600 line-clamp-2 mt-1 leading-relaxed">
                    {ed.professional_headline}
                  </p>
                )}

                {ed.current_employer && (
                  <div className="mt-2 flex items-center gap-1.5 text-xs font-medium text-purple-700 bg-purple-50 px-2 py-0.5 rounded-md w-fit">
                    <Briefcase size={12} />
                    <span className="truncate">{ed.current_employer}</span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Teaching Information */}
          <div className="p-5 space-y-3 text-xs text-slate-700">
            <div className="grid grid-cols-2 gap-2 pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <BookOpen size={14} className="text-brand-500 shrink-0" />
                <span className="font-medium truncate">{ed.subjects.join(", ") || subject || "Subject Faculty"}</span>
              </div>
              <div className="flex items-center gap-2">
                <GraduationCap size={14} className="text-brand-500 shrink-0" />
                <span className="font-medium truncate">{ed.track || track || "Competitive Track"}</span>
              </div>
              <div className="flex items-center gap-2">
                <MapPin size={14} className="text-brand-500 shrink-0" />
                <span className="font-medium truncate">{ed.location || location || "India"}</span>
              </div>
              {totalFollowers > 0 ? (
                <div className="flex items-center gap-2">
                  <Users size={14} className="text-brand-500 shrink-0" />
                  <span className="font-medium truncate">~{formatNumber(totalFollowers)} Audience</span>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-slate-400">
                  <ShieldCheck size={14} className="shrink-0 text-emerald-500" />
                  <span className="truncate">Independent Mentor</span>
                </div>
              )}
            </div>

            {/* Evidence summary */}
            {ed.evidence && ed.evidence.length > 0 && (
              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                  Match Evidence
                </span>
                <ul className="space-y-1">
                  {ed.evidence.slice(0, 2).map((ev, idx) => (
                    <li key={idx} className="flex items-start gap-1.5 text-[11px] text-slate-600">
                      <span className="text-emerald-500 font-bold">•</span>
                      <span className="line-clamp-2">
                        <strong className="capitalize text-slate-700">{ev.dimension}:</strong> {ev.text}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Discovered Profile Links */}
            {ed.profiles && ed.profiles.length > 0 && (
              <div className="pt-2">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1.5">
                  Verified Profiles
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {ed.profiles.map((p, idx) => (
                    <a
                      key={idx}
                      href={p.url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 px-2.5 py-1 bg-slate-50 hover:bg-brand-50 hover:text-brand-700 border border-slate-200 hover:border-brand-200 rounded-md text-[11px] font-medium text-slate-700 transition-colors"
                    >
                      {getPlatformIcon(p.platform)}
                      <span>{p.platform}</span>
                      <ExternalLink size={10} className="text-slate-400" />
                    </a>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Card Actions Footer */}
        <div className="p-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-xs gap-2">
          <div className="flex items-center gap-2">
            <button
              onClick={() => toggleSaveEducator(ed)}
              className={`inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg font-medium transition-all ${
                isSaved
                  ? 'bg-brand-600 text-white shadow-sm'
                  : 'bg-white hover:bg-slate-100 text-slate-700 border border-slate-200'
              }`}
            >
              <Bookmark size={13} className={isSaved ? 'fill-current' : ''} />
              {isSaved ? 'Saved' : 'Save'}
            </button>

            <button
              onClick={() => toggleCompareEducator(ed)}
              className={`inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg font-medium transition-all ${
                isCompared
                  ? 'bg-purple-600 text-white shadow-sm'
                  : 'bg-white hover:bg-slate-100 text-slate-700 border border-slate-200'
              }`}
            >
              {isCompared ? 'Comparing' : 'Compare'}
            </button>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => setEvidenceModalEd(ed)}
              className="px-2 py-1 text-slate-600 hover:text-brand-600 font-medium hover:underline transition-colors"
            >
              Verify Sources
            </button>

            {ed.profile_url && (
              <a
                href={ed.profile_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 px-2.5 py-1.5 bg-brand-50 hover:bg-brand-100 text-brand-700 font-semibold rounded-lg transition-colors"
              >
                <span>View Profile</span>
                <ExternalLink size={12} />
              </a>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans text-slate-900">

      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-slate-200 flex flex-col hidden md:flex shrink-0">
        <div className="p-6 border-b border-slate-100">
          <div className="flex items-center gap-2.5 text-brand-600 font-bold text-lg">
            <Activity size={24} />
            <span>Educator Discovery</span>
          </div>
          <p className="text-xs text-slate-500 mt-1">Verified Teacher Search</p>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          <button
            onClick={() => setActiveTab('discover')}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-colors text-left ${
              activeTab === 'discover'
                ? 'bg-brand-50 text-brand-700 font-semibold'
                : 'text-slate-600 hover:bg-slate-50'
            }`}
          >
            <Search size={18} />
            <span>Discover Educators</span>
          </button>

          <button
            onClick={() => setActiveTab('saved')}
            className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl font-medium text-sm transition-colors text-left ${
              activeTab === 'saved'
                ? 'bg-brand-50 text-brand-700 font-semibold'
                : 'text-slate-600 hover:bg-slate-50'
            }`}
          >
            <div className="flex items-center gap-3">
              <Bookmark size={18} />
              <span>Saved Educators</span>
            </div>
            {savedEducators.length > 0 && (
              <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-brand-100 text-brand-700">
                {savedEducators.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('settings')}
            className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-colors text-left ${
              activeTab === 'settings'
                ? 'bg-brand-50 text-brand-700 font-semibold'
                : 'text-slate-600 hover:bg-slate-50'
            }`}
          >
            <Settings size={18} />
            <span>Settings & Diagnostics</span>
          </button>
        </nav>

        <div className="p-4 border-t border-slate-100">
          <div className="flex items-center gap-2 px-2 text-xs text-slate-500">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
            <span>Search Pipeline Active</span>
          </div>
        </div>
      </aside>

      {/* Main Content Viewport */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="bg-white border-b border-slate-200 px-8 py-5 flex items-center justify-between shadow-sm z-10 shrink-0">
          <div>
            <h1 className="text-2xl font-bold text-slate-800">
              {activeTab === 'discover' && 'Discover Educators'}
              {activeTab === 'saved' && 'Saved Educators'}
              {activeTab === 'settings' && 'Settings & Diagnostics'}
            </h1>
            <p className="text-xs text-slate-500 mt-1">
              {activeTab === 'discover' && 'Evidence-based educator discovery across IIT-JEE & NEET preparation hubs'}
              {activeTab === 'saved' && 'Your shortlisted and saved educator profiles'}
              {activeTab === 'settings' && 'System configuration, crawler settings, API metrics, and cache management'}
            </p>
          </div>

          {comparedEducators.length > 0 && (
            <button
              onClick={() => setShowCompareModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-medium text-xs rounded-xl shadow-sm transition-all"
            >
              <span>Compare Selected ({comparedEducators.length})</span>
            </button>
          )}
        </header>

        <div className="flex-1 overflow-auto p-8">
          <div className="max-w-6xl mx-auto space-y-8">

            {/* TAB 1: DISCOVER EDUCATORS */}
            {activeTab === 'discover' && (
              <>
                {/* Search Workspace Card */}
                <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
                  {/* Primary 3-field Search Form */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-5">
                    {/* Location Field */}
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                        Location / Hub
                      </label>
                      <select
                        className="p-3 border border-slate-300 rounded-xl bg-slate-50/70 focus:bg-white focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none text-sm transition-all"
                        value={location}
                        onChange={e => setLocation(e.target.value)}
                      >
                        <option value="">Select location or city...</option>
                        <option value="Online">Online (All India)</option>
                        {locations.filter(l => l.toLowerCase() !== "online").map(loc => (
                          <option key={loc} value={loc}>{loc}</option>
                        ))}
                      </select>
                    </div>

                    {/* Track Field */}
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                        Exam Track
                      </label>
                      <select
                        className="p-3 border border-slate-300 rounded-xl bg-slate-50/70 focus:bg-white focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none text-sm transition-all"
                        value={track}
                        onChange={e => setTrack(e.target.value)}
                      >
                        <option value="">Select exam track...</option>
                        {tracks.map(t => <option key={t} value={t}>{t}</option>)}
                      </select>
                    </div>

                    {/* Subject Field */}
                    <div className="flex flex-col gap-1.5">
                      <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                        Subject
                      </label>
                      <select
                        className="p-3 border border-slate-300 rounded-xl bg-slate-50/70 focus:bg-white focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none text-sm transition-all disabled:opacity-50"
                        value={subject}
                        onChange={e => setSubject(e.target.value)}
                        disabled={!track}
                      >
                        <option value="">Select subject...</option>
                        {subjects.map(s => <option key={s} value={s}>{s}</option>)}
                      </select>
                    </div>
                  </div>

                  {/* Collapsible Advanced Settings */}
                  <div className="border-t border-slate-100 pt-4">
                    <button
                      type="button"
                      onClick={() => setShowAdvanced(!showAdvanced)}
                      className="inline-flex items-center gap-2 text-xs font-semibold text-slate-500 hover:text-slate-800 transition-colors"
                    >
                      <Sliders size={14} />
                      <span>Advanced Settings & Budgets</span>
                      {showAdvanced ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>

                    {showAdvanced && (
                      <div className="mt-4 p-4 bg-slate-50 rounded-xl border border-slate-200/80 space-y-4">
                        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                          <label className="flex items-center gap-2.5 text-xs text-slate-700 cursor-pointer select-none">
                            <input
                              type="checkbox"
                              className="rounded text-brand-600 focus:ring-brand-500 w-4 h-4"
                              checked={forceRefresh}
                              onChange={e => setForceRefresh(e.target.checked)}
                            />
                            <div>
                              <span className="font-semibold block">Bypass Cache and Force Refresh</span>
                              <span className="text-[11px] text-slate-500">
                                When enabled, fetches fresh external profiles. May trigger live API calls.
                              </span>
                            </div>
                          </label>

                          <div className="flex items-center gap-2 text-xs">
                            <span className="text-slate-600 font-medium">Search Target:</span>
                            <input
                              type="number"
                              min={5}
                              max={100}
                              value={targetCount}
                              onChange={e => setTargetCount(Math.max(5, Number(e.target.value)))}
                              className="w-16 p-1.5 text-center bg-white border border-slate-300 rounded-lg text-xs"
                            />
                            <span className="text-slate-400 text-[11px]">educators</span>
                          </div>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-3 border-t border-slate-200 text-xs">
                          <div>
                            <label className="text-[11px] font-medium text-slate-600 block mb-1">
                              Max Searches ({budgetSearches})
                            </label>
                            <input
                              type="range"
                              min={1}
                              max={15}
                              value={budgetSearches}
                              onChange={e => setBudgetSearches(Number(e.target.value))}
                              className="w-full accent-brand-600"
                            />
                          </div>

                          <div>
                            <label className="text-[11px] font-medium text-slate-600 block mb-1">
                              Max Candidate URLs ({budgetCandidates})
                            </label>
                            <input
                              type="range"
                              min={10}
                              max={100}
                              value={budgetCandidates}
                              onChange={e => setBudgetCandidates(Number(e.target.value))}
                              className="w-full accent-brand-600"
                            />
                          </div>

                          <div>
                            <label className="text-[11px] font-medium text-slate-600 block mb-1">
                              Max Profile Enrichments ({budgetEnrichments})
                            </label>
                            <input
                              type="range"
                              min={5}
                              max={50}
                              value={budgetEnrichments}
                              onChange={e => setBudgetEnrichments(Number(e.target.value))}
                              className="w-full accent-brand-600"
                            />
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Submit Button Bar */}
                  <div className="flex items-center justify-end pt-5 border-t border-slate-100 mt-4">
                    <button
                      className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-3 bg-brand-600 hover:bg-brand-700 text-white font-semibold text-sm rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-sm hover:shadow"
                      disabled={!location || !track || !subject || isLoading}
                      onClick={handleSearch}
                    >
                      {isLoading ? <RefreshCw className="animate-spin" size={18} /> : <Search size={18} />}
                      <span>{isLoading ? 'Searching Educators...' : 'Find Educators'}</span>
                    </button>
                  </div>
                </div>

                {/* Error Banner */}
                {error && (
                  <div className="bg-red-50 border border-red-200 text-red-700 px-6 py-4 rounded-2xl flex items-start gap-3">
                    <AlertCircle className="shrink-0 mt-0.5 text-red-600" size={20} />
                    <div>
                      <h3 className="font-semibold text-sm">Unable to complete search</h3>
                      <p className="text-xs mt-1 text-red-600/90">{error}</p>
                    </div>
                  </div>
                )}

                {/* Clean, Non-Technical Results Summary */}
                {response && !isLoading && (
                  <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2.5">
                          <h2 className="text-xl font-bold text-slate-800">
                            {response.total_results} {response.total_results === 1 ? 'Educator' : 'Educators'} Found
                          </h2>
                          <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                            response.target_reached
                              ? 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                              : 'bg-blue-100 text-blue-800 border border-blue-200'
                          }`}>
                            <CheckCircle2 size={12} />
                            Completed
                          </span>
                        </div>

                        {/* Honest Shortfall Explanation */}
                        <p className="text-sm text-slate-600 mt-1.5">
                          {response.target_shortfall > 0 ? (
                            <>
                              Showing <strong className="text-slate-900">{response.total_results}</strong> verified matches. We couldn't find <strong className="text-slate-900">{response.target_shortfall}</strong> more educators matching all your criteria in this search pass.
                            </>
                          ) : (
                            <>
                              Showing <strong className="text-slate-900">{response.total_results}</strong> verified matches. Target of {response.target_count} educators reached.
                            </>
                          )}
                        </p>
                      </div>

                      <div className="flex items-center gap-4 text-xs text-slate-500">
                        {response.last_updated && (
                          <div className="text-right">
                            <span className="block text-slate-400 text-[11px]">Updated</span>
                            <span className="font-medium text-slate-700">
                              {new Date(response.last_updated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                        )}
                        <div className="text-right pl-3 border-l border-slate-200">
                          <span className="block text-slate-400 text-[11px]">Target</span>
                          <span className="font-semibold text-slate-800">{response.target_count} profiles</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Empty State */}
                {response && !isLoading && response.results.length === 0 && (
                  <div className="bg-white border border-slate-200 rounded-2xl p-12 flex flex-col items-center justify-center text-center">
                    <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4 text-slate-400">
                      <Search size={32} />
                    </div>
                    <h3 className="text-base font-semibold text-slate-800">No verified educators found</h3>
                    <p className="text-xs text-slate-500 mt-2 max-w-md">
                      We couldn't locate educators meeting all strict subject, exam-track, and non-PW verification criteria. Try selecting "Online" to expand to all-India educators or toggling force refresh.
                    </p>
                  </div>
                )}

                {/* Main Results Grid */}
                {response?.results && response.results.length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {response.results.map((ed) => renderCard(ed, false))}
                  </div>
                )}

                {/* Optional Review Queue Section */}
                {response?.review_results && response.review_results.length > 0 && (
                  <div className="mt-12 pt-6 border-t border-slate-200">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-base font-bold text-slate-800">
                          Leads for Review ({response.review_results.length})
                        </h3>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Uncertain role, student profiles, or pending employer verification
                        </p>
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {response.review_results.map((ed) => renderCard(ed, true))}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* TAB 2: SAVED EDUCATORS */}
            {activeTab === 'saved' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                  <div>
                    <h2 className="text-lg font-bold text-slate-800">
                      Saved Candidates ({savedEducators.length})
                    </h2>
                    <p className="text-xs text-slate-500 mt-1">
                      Shortlisted educators stored for recruiter outreach and interview scheduling
                    </p>
                  </div>

                  {savedEducators.length > 0 && (
                    <div className="flex items-center gap-3">
                      <button
                        onClick={exportSavedEducators}
                        className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium text-xs rounded-xl transition-colors"
                      >
                        <Download size={14} />
                        <span>Export JSON</span>
                      </button>
                      <button
                        onClick={() => setSavedEducators([])}
                        className="inline-flex items-center gap-1.5 px-3 py-2 text-red-600 hover:bg-red-50 font-medium text-xs rounded-xl transition-colors"
                      >
                        <Trash2 size={14} />
                        <span>Clear All</span>
                      </button>
                    </div>
                  )}
                </div>

                {savedEducators.length === 0 ? (
                  <div className="bg-white border border-slate-200 rounded-2xl p-12 flex flex-col items-center justify-center text-center">
                    <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4 text-slate-400">
                      <Bookmark size={32} />
                    </div>
                    <h3 className="text-base font-semibold text-slate-800">No saved educators yet</h3>
                    <p className="text-xs text-slate-500 mt-1.5 max-w-sm">
                      Click the "Save" button on any educator card in Discover Educators to add candidates to this shortlist.
                    </p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {savedEducators.map((ed) => renderCard(ed, false))}
                  </div>
                )}
              </div>
            )}

            {/* TAB 3: SETTINGS & DIAGNOSTICS */}
            {activeTab === 'settings' && (
              <div className="space-y-6">
                {/* System & Provider Configuration Card */}
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                  <h2 className="text-base font-bold text-slate-800 mb-4 flex items-center gap-2">
                    <Server size={18} className="text-brand-600" />
                    <span>Provider Integrations & Engine Health</span>
                  </h2>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-slate-700">Anakin URL Scraper</span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                          {diagnosticsData?.providers?.anakin_scraper?.configured ? 'Connected' : 'Active'}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-2 font-mono break-all">
                        {diagnosticsData?.providers?.anakin_scraper?.endpoint || 'https://api.anakin.io/v1/url-scraper'}
                      </p>
                      <span className="text-[10px] text-slate-400 block mt-1">Deep profile data enrichment</span>
                    </div>

                    <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-slate-700">Anakin Search API</span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                          {diagnosticsData?.providers?.anakin_search?.configured ? 'Connected' : 'Active'}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-2 font-mono break-all">
                        {diagnosticsData?.providers?.anakin_search?.endpoint || 'https://api.anakin.io/v1/search'}
                      </p>
                      <span className="text-[10px] text-slate-400 block mt-1">Targeted faculty web discovery</span>
                    </div>

                    <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-slate-700">DDGS Search Engine</span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800">
                          Active
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-500 mt-2 font-mono break-all">
                        DuckDuckGo Discovery Pipeline
                      </p>
                      <span className="text-[10px] text-slate-400 block mt-1">Zero-credit candidate indexing</span>
                    </div>
                  </div>

                  <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between">
                    <div className="text-xs text-slate-600">
                      Pipeline Version: <strong className="text-slate-800">{diagnosticsData?.pipeline_version || 'v4'}</strong>
                      <span className="mx-2">•</span>
                      Supported Indian Hubs: <strong className="text-slate-800">{locations.length} cities</strong>
                    </div>

                    <button
                      onClick={handleClearCache}
                      className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium text-xs rounded-xl transition-colors"
                    >
                      Clear Search Cache
                    </button>
                  </div>

                  {cacheClearMessage && (
                    <div className="mt-3 p-3 bg-emerald-50 text-emerald-800 text-xs rounded-xl border border-emerald-200">
                      {cacheClearMessage}
                    </div>
                  )}
                </div>

                {/* Last Search Diagnostic Metrics */}
                {response ? (
                  <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
                    <h2 className="text-base font-bold text-slate-800 flex items-center gap-2">
                      <Activity size={18} className="text-brand-600" />
                      <span>Diagnostics from Most Recent Search</span>
                    </h2>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                        <span className="text-[11px] text-slate-500 block">Sources Attempted</span>
                        <strong className="text-base text-slate-800 block mt-0.5">{response.sources_searched}</strong>
                      </div>
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                        <span className="text-[11px] text-slate-500 block">Unique URLs Found</span>
                        <strong className="text-base text-slate-800 block mt-0.5">{response.unique_candidates_discovered}</strong>
                      </div>
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                        <span className="text-[11px] text-slate-500 block">Profiles Enriched</span>
                        <strong className="text-base text-slate-800 block mt-0.5">{response.profiles_enriched}</strong>
                      </div>
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                        <span className="text-[11px] text-slate-500 block">Search Duration</span>
                        <strong className="text-base text-slate-800 block mt-0.5">{response.search_duration_seconds}s</strong>
                      </div>
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                        <span className="text-[11px] text-slate-500 block">Credits Used</span>
                        <strong className="text-base text-slate-800 block mt-0.5">{response.credits_used} credits</strong>
                      </div>
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                        <span className="text-[11px] text-slate-500 block">Cache Status</span>
                        <strong className="text-base text-slate-800 block mt-0.5">{response.cache_status}</strong>
                      </div>
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                        <span className="text-[11px] text-slate-500 block">Current PW Excluded</span>
                        <strong className="text-base text-slate-800 block mt-0.5">{response.rejected_counts?.EXCLUDED_CURRENT_PW || 0}</strong>
                      </div>
                      <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                        <span className="text-[11px] text-slate-500 block">Former PW Excluded</span>
                        <strong className="text-base text-slate-800 block mt-0.5">{response.rejected_counts?.EXCLUDED_FORMER_PW || 0}</strong>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm text-center py-10">
                    <HelpCircle size={28} className="mx-auto text-slate-400 mb-2" />
                    <p className="text-xs text-slate-500">
                      No search diagnostics available yet. Run a search from the Discover Educators tab to view live pipeline metrics.
                    </p>
                  </div>
                )}
              </div>
            )}

          </div>
        </div>
      </main>

      {/* Compare Modal */}
      {showCompareModal && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-6 z-50">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-4xl w-full max-h-[85vh] flex flex-col overflow-hidden">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-slate-900 text-base">Compare Educators</h3>
                <p className="text-xs text-slate-500">Side-by-side comparison of selected candidate profiles</p>
              </div>
              <button
                onClick={() => setShowCompareModal(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
              >
                <X size={18} />
              </button>
            </div>

            <div className="p-6 overflow-auto flex-1 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {comparedEducators.map(ed => (
                <div key={ed.educator_id} className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-slate-900 truncate">{ed.full_name}</span>
                    <button
                      onClick={() => toggleCompareEducator(ed)}
                      className="text-red-500 hover:text-red-700"
                      title="Remove from comparison"
                    >
                      <X size={14} />
                    </button>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase font-semibold block">Headline</span>
                    <p className="text-slate-700 line-clamp-2">{ed.professional_headline || 'Not stated'}</p>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase font-semibold block">Employer</span>
                    <p className="text-slate-700">{ed.current_employer || 'Independent / Not verified'}</p>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase font-semibold block">Subject & Track</span>
                    <p className="text-slate-700">{ed.subjects.join(", ")} ({ed.track})</p>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase font-semibold block">Location</span>
                    <p className="text-slate-700">{ed.location}</p>
                  </div>
                  {ed.profile_url && (
                    <a
                      href={ed.profile_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-brand-600 font-semibold hover:underline"
                    >
                      <span>Profile Link</span>
                      <ExternalLink size={11} />
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Evidence & Verification Modal */}
      {evidenceModalEd && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-6 z-50">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-xl w-full max-h-[85vh] flex flex-col overflow-hidden">
            <div className="p-5 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h3 className="font-bold text-slate-900 text-base">{evidenceModalEd.full_name}</h3>
                <p className="text-xs text-slate-500">Verification Audit Trail & Matched Evidence</p>
              </div>
              <button
                onClick={() => setEvidenceModalEd(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
              >
                <X size={18} />
              </button>
            </div>

            <div className="p-6 overflow-auto flex-1 space-y-4 text-xs">
              <div className="flex flex-wrap gap-2">
                <span className="px-2.5 py-1 rounded-full font-semibold bg-emerald-100 text-emerald-800">
                  {evidenceModalEd.pw_exclusion_status.replace(/_/g, ' ')}
                </span>
                <span className="px-2.5 py-1 rounded-full font-semibold bg-blue-100 text-blue-800">
                  {evidenceModalEd.track} {evidenceModalEd.subjects.join(", ")}
                </span>
                <span className="px-2.5 py-1 rounded-full font-semibold bg-slate-100 text-slate-700">
                  {evidenceModalEd.location}
                </span>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-2 uppercase text-[11px] tracking-wider">
                  Supporting Evidence Citations
                </h4>
                <ul className="space-y-2">
                  {evidenceModalEd.evidence?.map((ev, idx) => (
                    <li key={idx} className="p-3 bg-slate-50 rounded-xl border border-slate-200/70 text-slate-700">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold capitalize text-slate-900">{ev.dimension} Verification</span>
                        <span className="text-[10px] text-slate-400">{ev.platform}</span>
                      </div>
                      <p className="text-slate-600 leading-relaxed">{ev.text}</p>
                    </li>
                  ))}
                </ul>
              </div>

              <div>
                <h4 className="font-semibold text-slate-800 mb-2 uppercase text-[11px] tracking-wider">
                  Associated Social & Web Accounts
                </h4>
                <div className="space-y-1.5">
                  {evidenceModalEd.profiles?.map((p, idx) => (
                    <a
                      key={idx}
                      href={p.url}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center justify-between p-2.5 bg-slate-50 hover:bg-brand-50 border border-slate-200 hover:border-brand-200 rounded-lg text-slate-700 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        {getPlatformIcon(p.platform)}
                        <span className="font-medium">{p.platform}</span>
                      </div>
                      <span className="text-[11px] text-brand-600 hover:underline flex items-center gap-1 truncate max-w-xs">
                        {p.url}
                        <ExternalLink size={10} />
                      </span>
                    </a>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
