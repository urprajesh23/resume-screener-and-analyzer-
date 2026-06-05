import React, { useState, useEffect, useCallback } from 'react';

export default function HRDashboard({ onExit }) {
  const [files, setFiles] = useState([]);
  const [jdText, setJdText] = useState('');
  const [customSkills, setCustomSkills] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  
  // Sidebar states
  const [sidebarWidth, setSidebarWidth] = useState(340);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isResizing, setIsResizing] = useState(false);

  // Accordion & Tab states
  const [expandedId, setExpandedId] = useState(null);
  const [activeTabs, setActiveTabs] = useState({});

  // Sourcing & Assistant states
  const [booleanQueries, setBooleanQueries] = useState(null);
  const [loadingBoolean, setLoadingBoolean] = useState(false);
  const [showBooleanModal, setShowBooleanModal] = useState(false);

  // Candidate Actions states
  const [emailType, setEmailType] = useState({});
  const [emailDraft, setEmailDraft] = useState({});
  const [emailLoading, setEmailLoading] = useState({});

  const [interviewerGuide, setInterviewerGuide] = useState({});
  const [guideLoading, setGuideLoading] = useState({});

  const handleGenerateBoolean = async () => {
    if (!jdText) return;
    setLoadingBoolean(true);
    try {
      const response = await fetch('http://localhost:8000/api/hr/generate-boolean', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jd_text: jdText })
      });
      const data = await response.json();
      if (response.ok) {
        setBooleanQueries(data);
        setShowBooleanModal(true);
      } else {
        alert("Error: " + data.detail);
      }
    } catch (error) {
      console.error(error);
      alert("Error connecting to server to build Boolean query.");
    }
    setLoadingBoolean(false);
  };

  const handleGenerateEmail = async (candidateIndex) => {
    const cand = sortedResults[candidateIndex];
    setEmailLoading(prev => ({ ...prev, [candidateIndex]: true }));
    try {
      const response = await fetch('http://localhost:8000/api/hr/generate-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          candidate_name: cand.candidate_name || cand.filename,
          score: cand.match_score,
          matched: cand.matched_skills || [],
          missing: cand.missing_skills || [],
          email_type: emailType[candidateIndex] || 'interview'
        })
      });
      const data = await response.json();
      if (response.ok) {
        setEmailDraft(prev => ({ ...prev, [candidateIndex]: data.email }));
      } else {
        alert("Error: " + data.detail);
      }
    } catch (error) {
      console.error(error);
      alert("Error generating email draft.");
    }
    setEmailLoading(prev => ({ ...prev, [candidateIndex]: false }));
  };

  const handleGenerateGuide = async (candidateIndex) => {
    const cand = sortedResults[candidateIndex];
    setGuideLoading(prev => ({ ...prev, [candidateIndex]: true }));
    try {
      const response = await fetch('http://localhost:8000/api/hr/generate-guide', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          resume_text: cand.resume_text || "",
          jd_text: jdText || "Job Description",
          candidate_name: cand.candidate_name || cand.filename
        })
      });
      const data = await response.json();
      if (response.ok) {
        setInterviewerGuide(prev => ({ ...prev, [candidateIndex]: data }));
      } else {
        alert("Error: " + data.detail);
      }
    } catch (error) {
      console.error(error);
      alert("Error generating interviewer guide.");
    }
    setGuideLoading(prev => ({ ...prev, [candidateIndex]: false }));
  };

  const startResizing = useCallback((e) => {
    setIsResizing(true);
  }, []);

  const stopResizing = useCallback(() => {
    setIsResizing(false);
  }, []);

  const resize = useCallback((e) => {
    if (isResizing) {
      const newWidth = e.clientX;
      if (newWidth > 250 && newWidth < 600) {
        setSidebarWidth(newWidth);
      }
    }
  }, [isResizing]);

  useEffect(() => {
    window.addEventListener('mousemove', resize);
    window.addEventListener('mouseup', stopResizing);
    return () => {
      window.removeEventListener('mousemove', resize);
      window.removeEventListener('mouseup', stopResizing);
    };
  }, [resize, stopResizing]);

  const handleFileChange = (e) => {
    setFiles(e.target.files);
  };

  const handleAnalyze = async () => {
    if (files.length === 0) {
      alert("Please upload at least one resume.");
      return;
    }

    setLoading(true);
    setResults(null);

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }
    formData.append('jd_text', jdText);
    formData.append('custom_skills', customSkills);

    try {
      const response = await fetch('http://localhost:8000/api/hr/upload-resumes', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (response.ok) {
        setResults(data.results);
      } else {
        alert("Error: " + data.detail);
      }
    } catch (error) {
      console.error(error);
      alert("Failed to connect to the backend server. Is FastAPI running?");
    }
    setLoading(false);
  };

  // Sort results by match_score descending
  const sortedResults = results ? [...results].sort((a, b) => b.match_score - a.match_score) : [];
  const topCandidate = sortedResults.length > 0 ? sortedResults[0] : null;

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#0f172a', color: 'white', overflow: 'hidden' }}>
      
      {/* LEFT SIDEBAR (Control Panel) */}
      <div style={{ 
        width: isCollapsed ? '60px' : `${sidebarWidth}px`, 
        backgroundColor: '#1e293b', 
        borderRight: '1px solid rgba(255,255,255,0.05)', 
        padding: isCollapsed ? '20px 10px' : '30px 25px', 
        display: 'flex', 
        flexDirection: 'column',
        transition: isResizing ? 'none' : 'width 0.3s ease, padding 0.3s ease',
        position: 'relative',
        flexShrink: 0
      }}>
        
        {/* Collapse Toggle Button */}
        <button 
          onClick={() => setIsCollapsed(!isCollapsed)}
          style={{
            position: 'absolute',
            right: '-12px',
            top: '25px',
            width: '24px',
            height: '24px',
            borderRadius: '50%',
            backgroundColor: '#6366F1',
            border: 'none',
            color: 'white',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            zIndex: 20,
            boxShadow: '0 2px 5px rgba(0,0,0,0.3)',
            fontSize: '0.8rem'
          }}
        >
          {isCollapsed ? '▶' : '◀'}
        </button>

        {!isCollapsed ? (
          <>
            <button onClick={onExit} style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.4)', color: '#fca5a5', padding: '10px', borderRadius: '8px', cursor: 'pointer', marginBottom: '30px', fontWeight: 'bold' }}>
              🚪 Exit HR Session
            </button>
            
            <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '20px', borderRadius: '12px', marginBottom: '30px', textAlign: 'center', border: '1px solid rgba(255,255,255,0.05)' }}>
              <h2 style={{ fontSize: '1.2rem', margin: 0, color: 'white' }}>⚙️ Control Panel</h2>
              <p style={{ fontSize: '0.85rem', color: '#94a3b8', margin: '8px 0 0 0' }}>Configure your screening</p>
            </div>

            <div style={{ marginBottom: '25px' }}>
              <label style={{ fontSize: '0.9rem', fontWeight: 'bold', display: 'block', marginBottom: '10px', color: '#e2e8f0' }}>📤 Upload Candidate Resume(s)</label>
              <input type="file" multiple accept=".pdf,.docx,.txt,.png,.jpg,.jpeg" onChange={handleFileChange} style={{ width: '100%', padding: '12px', background: 'rgba(15, 23, 42, 0.6)', borderRadius: '8px', border: '1px dashed #475569', color: '#cbd5e1' }} />
            </div>

            <div style={{ marginBottom: '25px' }}>
              <label style={{ fontSize: '0.9rem', fontWeight: 'bold', display: 'block', marginBottom: '10px', color: '#e2e8f0' }}>📝 Enter Job Description</label>
              <textarea placeholder="Paste Job Description..." rows="12" value={jdText} onChange={(e) => setJdText(e.target.value)} style={{ width: '100%', padding: '12px', background: 'rgba(15, 23, 42, 0.6)', borderRadius: '8px', border: '1px solid #334155', color: '#cbd5e1', resize: 'none' }} />
            </div>

            <div style={{ marginBottom: '30px' }}>
              <label style={{ fontSize: '0.9rem', fontWeight: 'bold', display: 'block', marginBottom: '10px', color: '#e2e8f0' }}>🎯 Define Required Skills</label>
              <input type="text" placeholder="Python, AWS, Agile..." value={customSkills} onChange={(e) => setCustomSkills(e.target.value)} style={{ width: '100%', padding: '12px', background: 'rgba(15, 23, 42, 0.6)', borderRadius: '8px', border: '1px solid #334155', color: '#cbd5e1' }} />
            </div>

            <button onClick={handleAnalyze} disabled={loading} style={{ background: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)', color: 'white', padding: '16px', borderRadius: '10px', border: 'none', fontWeight: 'bold', fontSize: '1.1rem', cursor: loading ? 'not-allowed' : 'pointer', marginTop: 'auto', boxShadow: '0 4px 15px rgba(99, 102, 241, 0.4)' }}>
              {loading ? '⏳ Processing...' : '⚡ Analyze Resumes'}
            </button>

          </>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '30px', marginTop: '50px' }}>
            <div title="Exit" onClick={onExit} style={{ cursor: 'pointer', fontSize: '1.5rem' }}>🚪</div>
            <div title="Upload" style={{ cursor: 'pointer', fontSize: '1.5rem' }}>📤</div>
            <div title="Analyze" onClick={handleAnalyze} style={{ cursor: 'pointer', fontSize: '1.5rem' }}>⚡</div>
          </div>
        )}
      </div>

      {/* Resize Handle */}
      {!isCollapsed && (
        <div 
          onMouseDown={startResizing}
          style={{ 
            width: '6px', 
            cursor: 'col-resize', 
            backgroundColor: isResizing ? '#6366F1' : 'transparent', 
            transition: 'background-color 0.2s',
            zIndex: 10,
            flexShrink: 0
          }} 
          onMouseEnter={(e) => e.target.style.backgroundColor = 'rgba(99, 102, 241, 0.3)'}
          onMouseLeave={(e) => e.target.style.backgroundColor = isResizing ? '#6366F1' : 'transparent'}
        />
      )}

      {/* MAIN CONTENT AREA */}
      <div style={{ flex: 1, padding: '40px', overflowY: 'auto', backgroundColor: '#0f172a' }}>
        
        {/* Banner */}
        <div style={{ background: 'linear-gradient(90deg, #1e293b 0%, #334155 100%)', padding: '50px 40px', borderRadius: '16px', textAlign: 'center', border: '1px solid rgba(255,255,255,0.05)', marginBottom: '30px', boxShadow: '0 10px 30px rgba(0,0,0,0.3)' }}>
          <h1 style={{ fontSize: '3.5rem', margin: '0 0 15px 0', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '15px', color: 'white', fontWeight: '800' }}>
            🚀 ProCareer Platform
          </h1>
          <p style={{ fontSize: '1.3rem', color: '#cbd5e1', margin: 0, fontWeight: '500' }}>AI-Powered Resume Screening, Analysis & Commercial Optimization</p>
        </div>

        {!results && !loading && (
          <div style={{ textAlign: 'center', padding: '100px 20px', color: '#475569' }}>
            <h2 style={{ fontSize: '2rem', marginBottom: '10px' }}>Awaiting Candidates...</h2>
            <p style={{ fontSize: '1.1rem' }}>Upload resumes and provide a Job Description in the Control Panel to begin screening.</p>
          </div>
        )}

        {loading && (
          <div style={{ background: 'rgba(34, 197, 94, 0.15)', color: '#4ade80', padding: '20px 25px', borderRadius: '10px', display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '30px', border: '1px solid rgba(34, 197, 94, 0.3)', fontSize: '1.1rem', fontWeight: '600' }}>
            <span style={{ animation: 'spin 1s linear infinite', display: 'inline-block' }}>⚙️</span> Processing {files.length} candidates against Job Description...
          </div>
        )}

        {results && (
          <>
            {/* Candidate Leaderboard Table */}
            <h2 style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px', fontSize: '1.8rem' }}>🏆 Candidate Leaderboard</h2>
            <p style={{ color: '#94a3b8', marginBottom: '20px' }}>All candidates ranked by Job Description match score (highest to lowest)</p>
            
            <div style={{ background: '#1e293b', borderRadius: '12px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.05)', marginBottom: '40px' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                <thead>
                  <tr style={{ background: 'rgba(15, 23, 42, 0.8)', color: '#94a3b8', fontSize: '0.85rem', borderBottom: '1px solid rgba(255,255,255,0.05)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    <th style={{ padding: '18px 20px', fontWeight: '600' }}>Filename</th>
                    <th style={{ padding: '18px 20px', fontWeight: '600' }}>Candidate Name</th>
                    <th style={{ padding: '18px 20px', fontWeight: '600' }}>Predicted Category</th>
                    <th style={{ padding: '18px 20px', fontWeight: '600' }}>Match Score</th>
                    <th style={{ padding: '18px 20px', fontWeight: '600' }}>Matched Skills Count</th>
                    <th style={{ padding: '18px 20px', fontWeight: '600' }}>Missing Skills Count</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedResults.map((res, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)', background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.015)', transition: 'background 0.2s' }}>
                      <td style={{ padding: '16px 20px', color: '#cbd5e1' }}>{res.filename}</td>
                      <td style={{ padding: '16px 20px', fontWeight: '500' }}>{res.candidate_name !== "Unknown" ? res.candidate_name : "-"}</td>
                      <td style={{ padding: '16px 20px', color: '#94a3b8' }}>{res.category}</td>
                      <td style={{ padding: '16px 20px', fontWeight: 'bold', color: res.match_score >= 80 ? '#4ade80' : res.match_score >= 50 ? '#facc15' : '#f87171' }}>{res.match_score}%</td>
                      <td style={{ padding: '16px 20px', color: '#cbd5e1' }}>{res.matched_skills?.length || 0}</td>
                      <td style={{ padding: '16px 20px', color: '#cbd5e1' }}>{res.missing_skills?.length || 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Top Candidate Cards */}
            {topCandidate && (
              <div style={{ display: 'flex', gap: '30px', marginBottom: '50px' }}>
                <div style={{ flex: 1, background: '#1e293b', border: '1px solid rgba(255,255,255,0.05)', padding: '30px', borderRadius: '16px', boxShadow: '0 4px 20px rgba(0,0,0,0.2)' }}>
                  <div style={{ fontSize: '1rem', color: '#facc15', fontWeight: '600', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '8px' }}>🥇 Top Candidate</div>
                  <div style={{ fontSize: '2.2rem', fontWeight: '700', color: 'white' }}>{topCandidate.candidate_name !== "Unknown" ? topCandidate.candidate_name : topCandidate.filename}</div>
                </div>
                <div style={{ flex: 1, background: '#1e293b', border: '1px solid rgba(255,255,255,0.05)', padding: '30px', borderRadius: '16px', boxShadow: '0 4px 20px rgba(0,0,0,0.2)' }}>
                  <div style={{ fontSize: '1rem', color: '#94a3b8', fontWeight: '600', marginBottom: '10px' }}>Match Score</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                    <div style={{ fontSize: '2.5rem', fontWeight: '800', color: topCandidate.match_score >= 80 ? '#4ade80' : topCandidate.match_score >= 50 ? '#facc15' : '#f87171' }}>
                      {topCandidate.match_score}%
                    </div>
                    {topCandidate.match_score >= 80 && <span style={{ background: 'rgba(34, 197, 94, 0.15)', color: '#4ade80', padding: '6px 12px', borderRadius: '20px', fontSize: '0.85rem', fontWeight: 'bold' }}>↑ Excellent Match</span>}
                  </div>
                </div>
              </div>
            )}

            {/* Detailed Profiles Accordion */}
            <h2 style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '10px', fontSize: '1.8rem' }}>📄 Detailed Candidate Profiles</h2>
            <p style={{ color: '#94a3b8', marginBottom: '25px' }}>Expand any candidate below to view their complete analysis</p>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
              {sortedResults.map((res, i) => (
                <div key={i} style={{ background: '#1e293b', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)', overflow: 'hidden' }}>
                  
                  {/* Accordion Header */}
                  <div 
                    onClick={() => setExpandedId(expandedId === i ? null : i)}
                    style={{ padding: '20px 25px', cursor: 'pointer', display: 'flex', alignItems: 'center', background: expandedId === i ? 'rgba(255,255,255,0.02)' : 'transparent', transition: 'background 0.2s' }}
                  >
                    <span style={{ marginRight: '15px', color: '#94a3b8', fontSize: '0.8rem' }}>{expandedId === i ? '▼' : '▶'}</span>
                    <strong style={{ fontSize: '1.1rem' }}>{res.filename}</strong>
                    <span style={{ marginLeft: '10px', color: '#94a3b8' }}>- {res.match_score}% Match</span>
                  </div>

                  {/* Accordion Content */}
                  {expandedId === i && (
                    <div style={{ padding: '30px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                      
                      {/* Metric Cards Row */}
                      <div style={{ display: 'flex', gap: '20px', marginBottom: '30px' }}>
                        <div style={{ flex: 1, background: 'rgba(15, 23, 42, 0.4)', padding: '20px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.03)' }}>
                          <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '5px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>👤 Name</div>
                          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{res.candidate_name !== "Unknown" ? res.candidate_name : "-"}</div>
                        </div>
                        <div style={{ flex: 1, background: 'rgba(15, 23, 42, 0.4)', padding: '20px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.03)' }}>
                          <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '5px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>📂 Category</div>
                          <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{res.category}</div>
                        </div>
                        <div style={{ flex: 1, background: 'rgba(15, 23, 42, 0.4)', padding: '20px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.03)' }}>
                          <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '5px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>🎯 Match Score</div>
                          <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: res.match_score >= 80 ? '#4ade80' : res.match_score >= 50 ? '#facc15' : '#f87171' }}>{res.match_score}%</div>
                        </div>
                      </div>

                      {/* Tabs */}
                      <div style={{ display: 'flex', gap: '30px', borderBottom: '1px solid rgba(255,255,255,0.05)', marginBottom: '30px', paddingBottom: '2px', overflowX: 'auto', whiteSpace: 'nowrap' }}>
                        {['Skill Gap Analysis', 'Extracted Resume Info', 'Career Progression', 'Career Timeline', 'AI Email Assistant', 'Interviewer Guide'].map(tab => {
                          const isActive = (activeTabs[i] || 'Skill Gap Analysis') === tab;
                          return (
                            <div 
                              key={tab} 
                              onClick={() => setActiveTabs({...activeTabs, [i]: tab})}
                              style={{ 
                                cursor: 'pointer', 
                                fontSize: '0.95rem', 
                                fontWeight: isActive ? '600' : '500',
                                color: isActive ? '#f87171' : '#94a3b8',
                                borderBottom: isActive ? '3px solid #f87171' : '3px solid transparent',
                                paddingBottom: '12px',
                                transition: 'all 0.2s'
                              }}
                            >
                              {tab}
                            </div>
                          );
                        })}
                      </div>

                      {/* Tab Content */}
                      {((activeTabs[i] || 'Skill Gap Analysis') === 'Skill Gap Analysis') && (
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '30px' }}>
                          <div>
                            <h4 style={{ color: '#4ade80', marginBottom: '15px', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>✓ Matched Skills</h4>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                              {res.matched_skills?.map((s, idx) => (
                                <div key={idx} style={{ background: 'rgba(34, 197, 94, 0.1)', border: '1px solid rgba(34, 197, 94, 0.2)', padding: '12px 15px', borderRadius: '8px', color: '#4ade80', fontWeight: '500' }}>
                                  ✓ {s}
                                </div>
                              ))}
                              {(!res.matched_skills || res.matched_skills.length === 0) && <div style={{ color: '#94a3b8' }}>No matched skills found.</div>}
                            </div>
                          </div>
                          <div>
                            <h4 style={{ color: '#facc15', marginBottom: '15px', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>⚠ Missing Skills</h4>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                              {res.missing_skills?.map((s, idx) => (
                                <div key={idx} style={{ background: 'rgba(234, 179, 8, 0.1)', border: '1px solid rgba(234, 179, 8, 0.2)', padding: '12px 15px', borderRadius: '8px', color: '#facc15', fontWeight: '500' }}>
                                  ⚠ {s}
                                </div>
                              ))}
                              {(!res.missing_skills || res.missing_skills.length === 0) && <div style={{ color: '#94a3b8' }}>No missing skills found.</div>}
                            </div>
                          </div>
                        </div>
                      )}

                      {((activeTabs[i] || 'Skill Gap Analysis') === 'Extracted Resume Info') && (
                        <div>
                          <h4 style={{ marginBottom: '20px', fontSize: '1.1rem', color: '#e2e8f0' }}>📞 Contact Information</h4>
                          <div style={{ display: 'flex', gap: '60px', marginBottom: '30px', background: 'rgba(15, 23, 42, 0.4)', padding: '20px', borderRadius: '10px' }}>
                            <div><strong style={{ color: '#94a3b8' }}>Email:</strong> <span style={{ color: '#60a5fa', marginLeft: '10px' }}>{res.email}</span></div>
                            <div><strong style={{ color: '#94a3b8' }}>Phone:</strong> <span style={{ marginLeft: '10px', color: '#e2e8f0' }}>{res.phone}</span></div>
                          </div>
                          
                          <h4 style={{ marginBottom: '15px', fontSize: '1.1rem', color: '#e2e8f0' }}>🤖 AI Summary</h4>
                          <div style={{ background: 'rgba(15, 23, 42, 0.4)', padding: '20px', borderRadius: '10px', lineHeight: '1.7', color: '#cbd5e1' }}>
                            {res.summary}
                          </div>
                        </div>
                      )}

                      {((activeTabs[i] || 'Skill Gap Analysis') === 'Career Progression') && (
                        <div>
                          <h4 style={{ marginBottom: '15px', fontSize: '1.1rem', color: '#e2e8f0' }}>📈 Career Progression</h4>
                          <div style={{ background: 'rgba(15, 23, 42, 0.4)', padding: '20px', borderRadius: '10px', lineHeight: '1.7', color: '#cbd5e1' }}>
                            {res.career_progression}
                          </div>
                        </div>
                      )}

                      {((activeTabs[i] || 'Skill Gap Analysis') === 'Career Timeline') && (
                        <div>
                          <h4 style={{ marginBottom: '15px', fontSize: '1.1rem', color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '8px' }}>⌚ Career Timeline</h4>
                          <div style={{ background: '#1e293b', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', overflow: 'hidden' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                              <thead>
                                <tr style={{ background: 'rgba(15, 23, 42, 0.8)', color: '#94a3b8', fontSize: '0.85rem', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                  <th style={{ padding: '15px 20px', width: '50px' }}>#</th>
                                  <th style={{ padding: '15px 20px', width: '200px' }}>Date Range</th>
                                  <th style={{ padding: '15px 20px' }}>Context</th>
                                </tr>
                              </thead>
                              <tbody>
                                {res.career_timeline?.map((item, idx) => (
                                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)', background: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.015)' }}>
                                    <td style={{ padding: '15px 20px', color: '#94a3b8' }}>{idx}</td>
                                    <td style={{ padding: '15px 20px', color: '#cbd5e1', fontWeight: '500' }}>{item.date}</td>
                                    <td style={{ padding: '15px 20px', color: '#94a3b8' }}>{item.context}</td>
                                  </tr>
                                ))}
                                {(!res.career_timeline || res.career_timeline.length === 0) && (
                                  <tr>
                                    <td colSpan="3" style={{ padding: '15px 20px', color: '#94a3b8', textAlign: 'center' }}>No timeline extracted.</td>
                                  </tr>
                                )}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}

                      {((activeTabs[i] || 'Skill Gap Analysis') === 'AI Email Assistant') && (
                        <div>
                          <h4 style={{ marginBottom: '15px', fontSize: '1.1rem', color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '8px' }}>📧 AI Recruiter Email Assistant</h4>
                          <p style={{ fontSize: '0.9rem', color: '#94a3b8', marginBottom: '20px' }}>Select an email purpose to draft a personalized message for this candidate:</p>
                          
                          <div style={{ display: 'flex', gap: '15px', alignItems: 'center', marginBottom: '20px', flexWrap: 'wrap' }}>
                            <select 
                              value={emailType[i] || 'interview'} 
                              onChange={(e) => setEmailType({...emailType, [i]: e.target.value})}
                              style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid #334155', color: 'white', padding: '10px 15px', borderRadius: '8px', minWidth: '200px' }}
                            >
                              <option value="interview">📅 Invite for Interview</option>
                              <option value="info">📋 Request More Information</option>
                              <option value="rejection">✉️ Polite Constructive Rejection</option>
                            </select>
                            
                            <button 
                              onClick={() => handleGenerateEmail(i)}
                              disabled={emailLoading[i]}
                              style={{ background: 'linear-gradient(135deg, #6366F1 0%, #4F46E5 100%)', color: 'white', padding: '10px 20px', borderRadius: '8px', border: 'none', fontWeight: 'bold', cursor: emailLoading[i] ? 'not-allowed' : 'pointer' }}
                            >
                              {emailLoading[i] ? '⏳ Drafting...' : '🪄 Generate Email Draft'}
                            </button>
                          </div>

                          {emailDraft[i] && (
                            <div style={{ background: 'rgba(15, 23, 42, 0.4)', padding: '20px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.05)', marginTop: '20px' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                                <strong style={{ color: '#a5b4fc', fontSize: '0.9rem' }}>Generated Draft:</strong>
                                <button 
                                  onClick={() => { navigator.clipboard.writeText(emailDraft[i]); alert('Email draft copied to clipboard!'); }}
                                  style={{ background: 'rgba(99, 102, 241, 0.1)', border: '1px solid rgba(99, 102, 241, 0.3)', color: '#a5b4fc', padding: '4px 10px', borderRadius: '6px', fontSize: '0.8rem', cursor: 'pointer', fontWeight: 'bold' }}
                                >
                                  Copy to Clipboard
                                </button>
                              </div>
                              <textarea 
                                value={emailDraft[i]} 
                                onChange={(e) => setEmailDraft({...emailDraft, [i]: e.target.value})}
                                style={{ width: '100%', background: 'rgba(0,0,0,0.2)', border: '1px solid #334155', color: '#cbd5e1', padding: '15px', borderRadius: '8px', fontSize: '0.9rem', lineHeight: '1.6', resize: 'vertical' }} 
                                rows="10" 
                              />
                            </div>
                          )}
                        </div>
                      )}

                      {((activeTabs[i] || 'Skill Gap Analysis') === 'Interviewer Guide') && (
                        <div>
                          <h4 style={{ marginBottom: '15px', fontSize: '1.1rem', color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '8px' }}>📋 Targeted Interviewer Prep Guide</h4>
                          <p style={{ fontSize: '0.9rem', color: '#94a3b8', marginBottom: '20px' }}>Generate candidate-specific interview questions with evaluation criteria and rubrics:</p>

                          <button 
                            onClick={() => handleGenerateGuide(i)}
                            disabled={guideLoading[i]}
                            style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', color: 'white', padding: '12px 24px', borderRadius: '8px', border: 'none', fontWeight: 'bold', cursor: guideLoading[i] ? 'not-allowed' : 'pointer', marginBottom: '20px' }}
                          >
                            {guideLoading[i] ? '⏳ Building Rubric...' : '📋 Build Interviewer Guide'}
                          </button>

                          {interviewerGuide[i] && interviewerGuide[i].questions && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                              {interviewerGuide[i].questions.map((q, qIdx) => (
                                <div key={qIdx} style={{ background: 'rgba(15, 23, 42, 0.4)', padding: '20px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.05)' }}>
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                                    <strong style={{ color: '#a5b4fc', fontSize: '1rem' }}>Question {qIdx + 1}</strong>
                                    <span style={{ fontSize: '0.75rem', background: q.type === 'Technical' ? 'rgba(56, 189, 248, 0.15)' : 'rgba(168, 85, 247, 0.15)', color: q.type === 'Technical' ? '#38bdf8' : '#c084fc', padding: '3px 8px', borderRadius: '4px', fontWeight: 'bold' }}>{q.type}</span>
                                  </div>
                                  <p style={{ fontSize: '1rem', color: '#cbd5e1', fontWeight: '500', marginBottom: '15px', lineHeight: '1.5' }}>{q.question}</p>
                                  <div style={{ background: 'rgba(0,0,0,0.15)', padding: '12px 15px', borderRadius: '8px', borderLeft: '3px solid #10b981' }}>
                                    <span style={{ fontSize: '0.8rem', color: '#10b981', fontWeight: 'bold', display: 'block', textTransform: 'uppercase', marginBottom: '5px' }}>Evaluation Rubric:</span>
                                    <p style={{ margin: 0, fontSize: '0.85rem', color: '#94a3b8', lineHeight: '1.5' }}>{q.ideal_answer}</p>
                                  </div>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                    </div>
                  )}
                </div>
              ))}
            </div>
          </>
        )}
      </div>

    </div>
  );
}
