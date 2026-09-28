import { useState, useEffect } from 'react'
import { 
  Search, MapPin, BookOpen, GraduationCap, 
  CheckCircle, AlertCircle, ChevronDown, ChevronUp,
  Camera, Video, Briefcase, Globe, Users
} from 'lucide-react'

// Tracks & Subjects configuration
const TRACK_SUBJECTS = {
  "IIT-JEE": ["Physics", "Chemistry", "Mathematics"],
  "NEET": ["Physics", "Chemistry", "Biology"]
}

// Hardcoded locations for frontend since backend is not publicly deployed yet
const LOCATIONS = [
  { value: "Lucknow, Uttar Pradesh", label: "Lucknow" },
  { value: "Noida, Uttar Pradesh", label: "Noida" },
  { value: "Greater Noida, Uttar Pradesh", label: "Greater Noida" },
  { value: "Ghaziabad, Uttar Pradesh", label: "Ghaziabad" },
  { value: "Kanpur, Uttar Pradesh", label: "Kanpur" },
  { value: "Prayagraj, Uttar Pradesh", label: "Prayagraj" },
  { value: "Varanasi, Uttar Pradesh", label: "Varanasi" },
  { value: "Agra, Uttar Pradesh", label: "Agra" },
  { value: "Meerut, Uttar Pradesh", label: "Meerut" },
  { value: "Gorakhpur, Uttar Pradesh", label: "Gorakhpur" }
];

// Mock API endpoint for development. Ensure backend is running.
const API_BASE = "http://127.0.0.1:8000/api"

function App() {
  // Filters state
  const [location, setLocation] = useState("")
  const [track, setTrack] = useState("")
  const [subject, setSubject] = useState("")

  // Search state
  const [isLoading, setIsLoading] = useState(false)
  const [results, setResults] = useState([])
  const [hasSearched, setHasSearched] = useState(false)
  const [forceRefresh, setForceRefresh] = useState(false)
  const [lastUpdated, setLastUpdated] = useState(null)

  // Expanded evidence state
  const [expandedCards, setExpandedCards] = useState(new Set())

  // Handle Track change
  const handleTrackChange = (e) => {
    setTrack(e.target.value)
    setSubject("") // Reset subject when track changes
  }

  // Handle Search
  const handleSearch = async () => {
    if (!location || !track || !subject) return

    setIsLoading(true)
    setHasSearched(true)
    setResults([])

    try {
      const response = await fetch(`${API_BASE}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ location, track, subject, force_refresh: forceRefresh })
      })
      const data = await response.json()
      setResults(data.results || [])
      setLastUpdated(data.last_updated)
    } catch (err) {
      console.error("Search failed:", err)
      alert("Search failed. Ensure backend is running.")
    } finally {
      setIsLoading(false)
    }
  }

  const toggleEvidence = (id) => {
    const newExpanded = new Set(expandedCards)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedCards(newExpanded)
  }

  // Utility to format large numbers
  const formatNumber = (num) => {
    if (!num) return null
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M'
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K'
    return num.toString()
  }

  // Utility to render platform icon
  const getPlatformIcon = (platform) => {
    const p = platform.toLowerCase()
    if (p.includes("instagram")) return <Camera size={14} />
    if (p.includes("youtube")) return <Video size={14} />
    if (p.includes("linkedin")) return <Briefcase size={14} />
    return <Globe size={14} />
  }

  const getVerificationIcon = (scores) => {
    const overall = scores?.overall || 0;
    if (overall >= 80) return <span className="status-badge status-verified"><CheckCircle size={12}/> Highly Verified</span>
    if (overall >= 50) return <span className="status-badge status-likely"><CheckCircle size={12}/> Likely Match</span>
    return <span className="status-badge status-uncertain"><AlertCircle size={12}/> Uncertain</span>
  }

  return (
    <div className="container">
      <header className="header">
        <h1>Educator Discovery</h1>
        <p>Evidence-based teacher search across multiple platforms</p>
      </header>

      <div className="search-card">
        <div className="search-filters">
          <div className="filter-group">
            <label>Location</label>
            <select value={location} onChange={(e) => setLocation(e.target.value)}>
              <option value="">Select a city...</option>
              {LOCATIONS.map(loc => (
                <option key={loc.value} value={loc.value}>{loc.label}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Track</label>
            <select value={track} onChange={handleTrackChange}>
              <option value="">Select track...</option>
              {Object.keys(TRACK_SUBJECTS).map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Subject</label>
            <select 
              value={subject} 
              onChange={(e) => setSubject(e.target.value)}
              disabled={!track}
            >
              <option value="">Select subject...</option>
              {track && TRACK_SUBJECTS[track].map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', color: 'var(--text-muted)' }}>
            <input 
              type="checkbox" 
              checked={forceRefresh}
              onChange={(e) => setForceRefresh(e.target.checked)}
            />
            Bypass cache and force refresh
          </label>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            {lastUpdated && (
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Last updated: {new Date(lastUpdated).toLocaleString()}
              </span>
            )}
            <button 
              className="search-btn"
              disabled={!location || !track || !subject || isLoading}
              onClick={handleSearch}
            >
              {isLoading ? (
                <>Discovering educators...</>
              ) : (
                <><Search size={18} /> Find Educators</>
              )}
            </button>
          </div>
        </div>
      </div>

      {isLoading && (
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Scraping and verifying profiles in {location}...</p>
        </div>
      )}

      {!isLoading && hasSearched && results.length === 0 && (
        <div className="loading-container">
          <p>No educators found matching this criteria.</p>
        </div>
      )}

      <div className="results-grid">
        {results.map((ed) => {
          const isExpanded = expandedCards.has(ed.educator_id);
          // Aggregate followers for display
          const totalFollowers = ed.profiles.reduce((acc, p) => acc + (p.followers || p.subscribers || p.connections || 0), 0);

          return (
            <div key={ed.educator_id} className="educator-card">
              <div className="card-header">
                <div className="avatar-placeholder">
                  {ed.name ? ed.name.charAt(0).toUpperCase() : '?'}
                </div>
                <div className="header-info">
                  <h3>{ed.name}</h3>
                  {getVerificationIcon(ed.scores)}
                </div>
              </div>

              <div className="card-body">
                <div className="info-row">
                  <MapPin size={16} />
                  <span>{ed.location}</span>
                </div>
                <div className="info-row">
                  <GraduationCap size={16} />
                  <span>{ed.track}</span>
                </div>
                <div className="info-row">
                  <BookOpen size={16} />
                  <span>{ed.subjects.join(", ") || subject}</span>
                </div>
                
                {totalFollowers > 0 && (
                  <div className="info-row" style={{ marginTop: '0.5rem', color: 'var(--text-main)', fontWeight: '500' }}>
                    <Users size={16} />
                    <span>~{formatNumber(totalFollowers)} Total Audience</span>
                  </div>
                )}

                <div className="score-container">
                  <div className="score-header">
                    <span className="score-title">Relevance Score</span>
                    <span className="score-value">{ed.scores?.overall || 0}</span>
                  </div>
                  <div style={{ width: '100%', height: '6px', background: '#e2e8f0', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{ width: `${ed.scores?.overall || 0}%`, height: '100%', background: 'var(--primary)' }}></div>
                  </div>
                </div>

                {ed.profiles && ed.profiles.length > 0 && (
                  <div className="social-links">
                    {ed.profiles.map((p, idx) => (
                      <a 
                        key={idx} 
                        href={p.url} 
                        target="_blank" 
                        rel="noreferrer" 
                        className="social-pill"
                        title={p.url}
                      >
                        {getPlatformIcon(p.platform)}
                        {p.platform}
                      </a>
                    ))}
                  </div>
                )}
              </div>

              <div className="card-footer">
                <button 
                  className="evidence-toggle" 
                  onClick={() => toggleEvidence(ed.educator_id)}
                >
                  Why this educator?
                  {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>
                
                {isExpanded && (
                  <div className="evidence-content">
                    {ed.scores?.reasons?.map((reason, idx) => (
                      <div key={idx} className="reason-item">
                        <CheckCircle size={14} />
                        <span>{reason}</span>
                      </div>
                    ))}
                    {(!ed.scores?.reasons || ed.scores.reasons.length === 0) && (
                      <div className="reason-item">
                        <span>Evidence parsed from profile bios and activity.</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default App
