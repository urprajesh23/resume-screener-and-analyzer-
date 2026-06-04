import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function StudentPortal({ onExit }) {
  const [activeTool, setActiveTool] = useState('resume-builder');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');
  
  // Form States
  const [rbData, setRbData] = useState({ name: '', job_title: '', experience: '' });
  const [ccData, setCcData] = useState({ current_role: '', current_skills: '', target_role: '', target_jd: '' });
  const [jsData, setJsData] = useState({ skills: '', role: '', work_type: 'Work from home', country: '', state: '', locations: '' });
  const [clData, setClData] = useState({ name: '', resume_text: '', jd_text: '' });
  const [atsData, setAtsData] = useState({ resume_text: '', jd_text: '' });
  const [miData, setMiData] = useState({ resume_text: '', jd_text: '' });
  const [piData, setPiData] = useState({ skill: '', level: 'Complete Beginner' });

  const tools = [
    { id: 'resume-builder', icon: '📄', name: 'AI Resume Builder' },
    { id: 'career-coach', icon: '📈', name: 'Career Enhancer' },
    { id: 'job-search', icon: '🔍', name: 'Live Job Search' },
    { id: 'cover-letter', icon: '✉️', name: 'AI Cover Letter' },
    { id: 'ats-booster', icon: '⚡', name: 'ATS Score Booster' },
    { id: 'mock-interview', icon: '🎤', name: 'Mock Interview Prep' },
    { id: 'project-idea', icon: '🏗️', name: 'Project Idea Generator' },
  ];

  const handleFileUpload = async (e, setTextField, currentText) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch('http://localhost:8000/api/student/parse-resume', {
        method: 'POST',
        body: formData
      });
      const data = await response.json();
      if (response.ok) {
        setTextField(currentText ? data.text + '\n\n' + currentText : data.text);
      } else {
        alert("Error parsing file: " + data.detail);
      }
    } catch (error) {
      console.error(error);
      alert("Error connecting to backend for file parsing.");
    }
  };

  const submitToAPI = async (endpoint, payload, resultKey) => {
    setLoading(true);
    setResult('');
    try {
      const response = await fetch(`http://localhost:8000/api/student/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await response.json();
      if (response.ok) {
        if (Array.isArray(data[resultKey]) && data[resultKey].length > 0 && typeof data[resultKey][0] === 'string') {
          setResult(data[resultKey].join(', '));
        } else {
          setResult(data[resultKey]);
        }
      } else {
        setResult('Error: ' + data.detail);
      }
    } catch (error) {
      console.error(error);
      setResult('Error connecting to backend.');
    }
    setLoading(false);
  };

  const handleDownload = () => {
    const resumeEl = document.getElementById('resume-print-area');
    if (!resumeEl) return;

    // Create a temporary container for printing to prevent main layout offsets
    const printContainer = document.createElement('div');
    printContainer.id = 'print-container-temp';
    printContainer.className = 'print-container-temp';
    printContainer.innerHTML = resumeEl.innerHTML;

    // Append to body and mark printing state
    document.body.appendChild(printContainer);
    document.body.classList.add('printing-active');

    const originalTitle = document.title;
    try {
      const parsed = JSON.parse(result);
      if (parsed.name) {
        document.title = `${parsed.name.replace(/\s+/g, '_')}_Resume`;
      }
    } catch (e) {}

    window.print();

    // Restore original title and remove temp container
    document.title = originalTitle;
    document.body.removeChild(printContainer);
    document.body.classList.remove('printing-active');
  };

  return (
    <div style={{ padding: '40px' }}>
      <button className="btn-danger-modern" onClick={onExit} style={{ marginBottom: '20px' }}>
        🚪 Exit Student Session
      </button>
      <h1 className="gradient-text">🎓 ProCareer Student Tools</h1>
      
      <div style={{ display: 'flex', gap: '40px', marginTop: '40px', flexWrap: 'wrap' }}>
        {/* Sidebar */}
        <div style={{ width: '350px' }} className="card">
          <h3>Select a Tool</h3>
          <ul className="sidebar-nav">
            {tools.map(tool => (
              <li 
                key={tool.id} 
                className={`sidebar-tab ${activeTool === tool.id ? 'active' : ''}`}
                onClick={() => { setActiveTool(tool.id); setResult(''); }}
              >
                <span style={{ fontSize: '1.5rem' }}>{tool.icon}</span>
                {tool.name}
              </li>
            ))}
          </ul>
        </div>
        
        {/* Main Content Area */}
        <div style={{ flex: 1, minWidth: '400px' }} className="card">
          {activeTool === 'resume-builder' && (
            <>
              <h2>Automated ATS Resume Builder</h2>
              <label>Full Name</label>
              <input type="text" value={rbData.name} onChange={e => setRbData({...rbData, name: e.target.value})} placeholder="John Doe" />
              <label>Target Job Title</label>
              <input type="text" value={rbData.job_title} onChange={e => setRbData({...rbData, job_title: e.target.value})} placeholder="e.g. Software Engineer" />
              <label>Past Experience & Projects</label>
              <textarea value={rbData.experience} onChange={e => setRbData({...rbData, experience: e.target.value})} rows="5" placeholder="Describe your previous roles..."></textarea>
              
              <button className="btn-modern" onClick={() => submitToAPI('build-resume', { ...rbData, email: 'N/A', phone: 'N/A', education: 'N/A', job_desc: 'Standard Context' }, 'resume_text')} disabled={loading} style={{ marginTop: '20px', width: '100%' }}>
                {loading ? '⏳ Generating...' : '✨ Generate ATS-Optimized Resume'}
              </button>
            </>
          )}

          {activeTool === 'career-coach' && (
            <>
              <h2>📈 Career Enhancer & Market Trends</h2>
              <label>Current Role</label>
              <input type="text" value={ccData.current_role} onChange={e => setCcData({...ccData, current_role: e.target.value})} placeholder="e.g. Junior Developer" />
              <label>Current Skills</label>
              <input type="text" value={ccData.current_skills} onChange={e => setCcData({...ccData, current_skills: e.target.value})} placeholder="e.g. HTML, CSS, JavaScript" />
              <label>Target Dream Role</label>
              <input type="text" value={ccData.target_role} onChange={e => setCcData({...ccData, target_role: e.target.value})} placeholder="e.g. Senior Frontend Engineer" />
              <label>Target Job Description</label>
              <textarea value={ccData.target_jd} onChange={e => setCcData({...ccData, target_jd: e.target.value})} rows="4" placeholder="Paste the ideal job description here..."></textarea>
              
              <button className="btn-modern" onClick={() => submitToAPI('career-coach', ccData, 'report')} disabled={loading} style={{ marginTop: '20px', width: '100%' }}>
                {loading ? '⏳ Analyzing...' : '📈 Generate Coaching Report'}
              </button>
            </>
          )}

          {activeTool === 'job-search' && (
            <>
              <h2>🔍 Live Job Search Matcher</h2>
              <label>Your Skills (comma separated)</label>
              <input type="text" value={jsData.skills} onChange={e => setJsData({...jsData, skills: e.target.value})} placeholder="e.g. Python, SQL, React" />
              <label>Target Role Looking For</label>
              <input type="text" value={jsData.role} onChange={e => setJsData({...jsData, role: e.target.value})} placeholder="e.g. Data Engineer" />
              <label>Work Type</label>
              <select value={jsData.work_type} onChange={e => setJsData({...jsData, work_type: e.target.value})}>
                <option>Work from home</option>
                <option>Offline / On-site</option>
                <option>Hybrid</option>
              </select>
              <label>Country</label>
              <input type="text" value={jsData.country} onChange={e => setJsData({...jsData, country: e.target.value})} placeholder="e.g. United States" />
              <label>State</label>
              <input type="text" value={jsData.state} onChange={e => setJsData({...jsData, state: e.target.value})} placeholder="e.g. California" />
              <label>Preferred Locations (comma separated to add more)</label>
              <input type="text" value={jsData.locations} onChange={e => setJsData({...jsData, locations: e.target.value})} placeholder="e.g. San Francisco, San Jose" />
              
              <button className="btn-modern" onClick={() => submitToAPI('job-search', jsData, 'jobs')} disabled={loading} style={{ marginTop: '20px', width: '100%' }}>
                {loading ? '⏳ Searching...' : '🔍 Find Recommended Jobs'}
              </button>
            </>
          )}

          {activeTool === 'cover-letter' && (
            <>
              <h2>✉️ AI Cover Letter Generator</h2>
              <label>Upload Resume (PDF/DOCX/TXT/Image)</label>
              <input type="file" accept=".pdf,.docx,.txt,.png,.jpg,.jpeg" onChange={e => handleFileUpload(e, text => setClData({...clData, resume_text: text}), clData.resume_text)} />
              
              <label>Your Name</label>
              <input type="text" value={clData.name} onChange={e => setClData({...clData, name: e.target.value})} placeholder="John Doe" />
              <label>Resume Summary (Or Upload Above)</label>
              <textarea value={clData.resume_text} onChange={e => setClData({...clData, resume_text: e.target.value})} rows="4" placeholder="Paste text or let upload fill this..."></textarea>
              <label>Target Job Description</label>
              <textarea value={clData.jd_text} onChange={e => setClData({...clData, jd_text: e.target.value})} rows="4" placeholder="Paste Job Description here..."></textarea>
              
              <button className="btn-modern" onClick={() => submitToAPI('cover-letter', clData, 'cover_letter')} disabled={loading} style={{ marginTop: '20px', width: '100%' }}>
                {loading ? '⏳ Drafting...' : '✉️ Generate Cover Letter'}
              </button>
            </>
          )}

          {activeTool === 'ats-booster' && (
            <>
              <h2>⚡ ATS Resume Score Booster</h2>
              <label>Upload Resume</label>
              <input type="file" accept=".pdf,.docx,.txt,.png,.jpg,.jpeg" onChange={e => handleFileUpload(e, text => setAtsData({...atsData, resume_text: text}), atsData.resume_text)} />
              <label>Current Resume Text</label>
              <textarea value={atsData.resume_text} onChange={e => setAtsData({...atsData, resume_text: e.target.value})} rows="4" placeholder="Paste text or let upload fill this..."></textarea>
              <label>Target Job Description</label>
              <textarea value={atsData.jd_text} onChange={e => setAtsData({...atsData, jd_text: e.target.value})} rows="4" placeholder="Paste Job Description here..."></textarea>
              
              <button className="btn-modern" onClick={() => submitToAPI('ats-booster', atsData, 'report')} disabled={loading} style={{ marginTop: '20px', width: '100%' }}>
                {loading ? '⏳ Analyzing...' : '⚡ Boost ATS Score'}
              </button>
            </>
          )}

          {activeTool === 'mock-interview' && (
            <>
              <h2>🎤 AI Mock Interview Prep</h2>
              <label>Upload Resume</label>
              <input type="file" accept=".pdf,.docx,.txt,.png,.jpg,.jpeg" onChange={e => handleFileUpload(e, text => setMiData({...miData, resume_text: text}), miData.resume_text)} />
              <label>Resume Text</label>
              <textarea value={miData.resume_text} onChange={e => setMiData({...miData, resume_text: e.target.value})} rows="4" placeholder="Paste text or let upload fill this..."></textarea>
              <label>Target Job Description</label>
              <textarea value={miData.jd_text} onChange={e => setMiData({...miData, jd_text: e.target.value})} rows="4" placeholder="Paste Job Description here..."></textarea>
              
              <button className="btn-modern" onClick={() => submitToAPI('interview-prep', miData, 'questions')} disabled={loading} style={{ marginTop: '20px', width: '100%' }}>
                {loading ? '⏳ Preparing...' : '🎤 Generate Custom Questions'}
              </button>
            </>
          )}

          {activeTool === 'project-idea' && (
            <>
              <h2>🏗️ Project Idea Generator</h2>
              <label>Target Skill to Learn (e.g. AWS, React)</label>
              <input type="text" value={piData.skill} onChange={e => setPiData({...piData, skill: e.target.value})} placeholder="e.g. AWS" />
              <label>Your Current Level</label>
              <select value={piData.level} onChange={e => setPiData({...piData, level: e.target.value})}>
                <option>Complete Beginner</option>
                <option>Some Knowledge</option>
                <option>Intermediate</option>
              </select>
              
              <button className="btn-modern" onClick={() => submitToAPI('project-idea', piData, 'blueprint')} disabled={loading} style={{ marginTop: '20px', width: '100%' }}>
                {loading ? '⏳ Generating...' : '🏗️ Get Project Blueprint'}
              </button>
            </>
          )}

          {/* Results Display */}
          {result && (
            <div style={{ marginTop: '30px' }}>
              {activeTool === 'resume-builder' ? (
                (() => {
                  try {
                    // Try parsing the JSON
                    const parsed = JSON.parse(result);
                    return (
                      <div id="resume-print-area" className="resume-container" style={{ background: '#1a1d2e', padding: '40px', borderRadius: '16px', border: '1px solid rgba(99, 102, 241, 0.2)', boxShadow: '0 10px 30px rgba(0,0,0,0.5)', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
                        <div className="resume-header" style={{ borderBottom: '2px solid rgba(255,255,255,0.05)', paddingBottom: '20px', marginBottom: '25px', textAlign: 'center' }}>
                          <h1 className="resume-name" style={{ fontSize: '28px', color: 'white', margin: '0 0 10px 0', fontWeight: '800' }}>{parsed.name || 'Unknown Name'}</h1>
                          <div className="resume-contact" style={{ display: 'flex', justifyContent: 'center', gap: '15px', color: '#94a3b8', fontSize: '14px' }}>
                            <span>{parsed.email || 'No Email'}</span>
                            <span style={{ color: '#475569' }}>•</span>
                            <span>{parsed.phone || 'No Phone'}</span>
                            <span style={{ color: '#475569' }}>•</span>
                            <span>{parsed.linkedin || 'No LinkedIn'}</span>
                          </div>
                        </div>

                        {parsed.summary && (
                          <div className="resume-section" style={{ marginBottom: '30px' }}>
                            <div className="resume-section-header" style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px' }}>
                              <div className="resume-section-bar" style={{ width: '3px', height: '16px', background: '#6366f1' }}></div>
                              <h3 className="resume-section-title" style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px', color: '#a5b4fc', margin: 0 }}>Professional Summary</h3>
                              <div className="resume-section-divider" style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.05)' }}></div>
                            </div>
                            <p className="resume-summary-text" style={{ fontStyle: 'italic', color: '#cbd5e1', lineHeight: '1.7', margin: 0, padding: '0 10px' }}>{parsed.summary}</p>
                          </div>
                        )}

                        {parsed.skills && Object.keys(parsed.skills).length > 0 && (
                          <div className="resume-section" style={{ marginBottom: '30px' }}>
                            <div className="resume-section-header" style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px' }}>
                              <div className="resume-section-bar" style={{ width: '3px', height: '16px', background: '#6366f1' }}></div>
                              <h3 className="resume-section-title" style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px', color: '#a5b4fc', margin: 0 }}>Core Competencies</h3>
                              <div className="resume-section-divider" style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.05)' }}></div>
                            </div>
                            <div className="resume-skills-list" style={{ display: 'flex', flexDirection: 'column', gap: '10px', padding: '0 10px' }}>
                              {Object.entries(parsed.skills).map(([cat, skillsArr]) => (
                                skillsArr && skillsArr.length > 0 && (
                                  <div key={cat} className="resume-skills-row" style={{ display: 'flex', alignItems: 'flex-start', gap: '15px', flexWrap: 'wrap' }}>
                                    <strong className="resume-skills-category" style={{ color: '#94a3b8', fontSize: '13px', textTransform: 'capitalize', width: '120px', flexShrink: 0 }}>{cat}:</strong>
                                    <div className="resume-skills-tags" style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                                      {skillsArr.map((skill, i) => (
                                        <span key={i} className="resume-skill-badge" style={{ background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.3)', color: '#a5b4fc', padding: '4px 10px', borderRadius: '20px', fontSize: '12px' }}>{skill}</span>
                                      ))}
                                    </div>
                                  </div>
                                )
                              ))}
                            </div>
                          </div>
                        )}

                        {parsed.projects && parsed.projects.length > 0 && (
                          <div className="resume-section" style={{ marginBottom: '30px' }}>
                            <div className="resume-section-header" style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px' }}>
                              <div className="resume-section-bar" style={{ width: '3px', height: '16px', background: '#6366f1' }}></div>
                              <h3 className="resume-section-title" style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px', color: '#a5b4fc', margin: 0 }}>Professional Experience</h3>
                              <div className="resume-section-divider" style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.05)' }}></div>
                            </div>
                            <div className="resume-projects-list" style={{ display: 'flex', flexDirection: 'column', gap: '15px', padding: '0 10px' }}>
                              {parsed.projects.map((proj, i) => (
                                <div key={i} className="resume-project-card" style={{ background: '#1e2235', padding: '20px', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.03)' }}>
                                  <div className="resume-project-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                                    <div>
                                      <h4 className="resume-project-title" style={{ margin: '0 0 8px 0', color: '#e2e8f0', fontSize: '16px' }}>{proj.name}</h4>
                                      {proj.tech && <span className="resume-project-tech" style={{ background: 'rgba(14, 165, 233, 0.1)', color: '#0ea5e9', padding: '3px 8px', borderRadius: '4px', fontSize: '11px', border: '1px solid rgba(14, 165, 233, 0.2)' }}>{proj.tech}</span>}
                                    </div>
                                    <span className="resume-project-year" style={{ color: '#64748b', fontSize: '13px', background: 'rgba(255,255,255,0.05)', padding: '4px 10px', borderRadius: '15px' }}>{proj.year}</span>
                                  </div>
                                  <ul className="resume-project-bullets" style={{ margin: '15px 0 0 0', padding: 0, listStyle: 'none' }}>
                                    {proj.bullets && proj.bullets.map((bullet, j) => (
                                      <li key={j} className="resume-project-bullet" style={{ position: 'relative', paddingLeft: '15px', color: '#cbd5e1', fontSize: '14px', marginBottom: '8px', lineHeight: '1.5' }}>
                                        <span className="resume-project-bullet-dot" style={{ position: 'absolute', left: 0, top: '8px', width: '5px', height: '5px', borderRadius: '50%', background: '#6366f1' }}></span>
                                        {bullet}
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}

                        <div className="resume-education-certifications" style={{ display: 'flex', gap: '30px' }}>
                          {parsed.education && parsed.education.length > 0 && (
                            <div className="resume-education-section" style={{ flex: 1 }}>
                              <div className="resume-section-header" style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px' }}>
                                <div className="resume-section-bar" style={{ width: '3px', height: '16px', background: '#6366f1' }}></div>
                                <h3 className="resume-section-title" style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px', color: '#a5b4fc', margin: 0 }}>Education</h3>
                                <div className="resume-section-divider" style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.05)' }}></div>
                              </div>
                              <div className="resume-education-list" style={{ padding: '0 10px' }}>
                                {parsed.education.map((edu, i) => (
                                  <div key={i} className="resume-education-item" style={{ marginBottom: '10px' }}>
                                    <div className="resume-education-degree" style={{ fontWeight: 'bold', color: '#e2e8f0', fontSize: '14px' }}>{edu.degree}</div>
                                    <div className="resume-education-details" style={{ color: '#94a3b8', fontSize: '13px' }}>{edu.institution} <span style={{ margin: '0 5px' }}>•</span> {edu.year}</div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {parsed.certifications && parsed.certifications.length > 0 && (
                            <div className="resume-certs-section" style={{ flex: 1 }}>
                              <div className="resume-section-header" style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px' }}>
                                <div className="resume-section-bar" style={{ width: '3px', height: '16px', background: '#6366f1' }}></div>
                                <h3 className="resume-section-title" style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '1px', color: '#a5b4fc', margin: 0 }}>Certifications</h3>
                                <div className="resume-section-divider" style={{ flex: 1, height: '1px', background: 'rgba(255,255,255,0.05)' }}></div>
                              </div>
                              <ul className="resume-certs-list" style={{ padding: '0 10px', margin: 0, listStyle: 'none' }}>
                                {parsed.certifications.map((cert, i) => (
                                  <li key={i} className="resume-cert-item" style={{ color: '#cbd5e1', fontSize: '14px', marginBottom: '5px' }}>• {cert}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>

                        <button className="no-print" style={{ marginTop: '30px', width: '100%', padding: '15px', background: 'linear-gradient(to right, #4f46e5, #7c3aed)', color: 'white', border: 'none', borderRadius: '10px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '10px', fontSize: '16px' }} onClick={handleDownload}>
                          <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" /></svg>
                          Download Resume
                        </button>
                      </div>
                    );
                  } catch (e) {
                    return (
                      <div style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', padding: '20px', borderRadius: '12px', color: '#fca5a5' }}>
                        <h3 style={{ margin: '0 0 10px 0' }}>⚠️ AI Generation Error</h3>
                        <p style={{ margin: 0 }}>The AI returned an invalid response format. Please try generating again.</p>
                        <pre style={{ marginTop: '15px', fontSize: '12px', overflowX: 'auto', background: 'rgba(0,0,0,0.2)', padding: '10px', borderRadius: '6px' }}>{result}</pre>
                      </div>
                    );
                  }
                })()
              ) : activeTool === 'job-search' && Array.isArray(result) ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  {result.map((job, idx) => (
                    <div key={idx} style={{ background: 'rgba(30, 41, 59, 0.7)', borderRadius: '12px', padding: '24px', border: '1px solid rgba(255,255,255,0.1)', display: 'flex', flexDirection: 'column', gap: '15px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                          <h3 style={{ margin: '0 0 8px 0', color: '#e2e8f0', fontSize: '20px' }}>{job.title}</h3>
                          <div style={{ color: '#94a3b8', fontSize: '14px', display: 'flex', gap: '10px', alignItems: 'center', flexWrap: 'wrap' }}>
                            <span style={{ color: '#38bdf8' }}>🏢 {job.company}</span>
                            <span>•</span>
                            <span>📍 {job.location}</span>
                            <span>•</span>
                            <span style={{ background: 'rgba(56, 189, 248, 0.1)', color: '#38bdf8', padding: '2px 8px', borderRadius: '10px', fontSize: '12px' }}>{job.work_type}</span>
                          </div>
                        </div>
                      </div>
                      <div style={{ background: 'rgba(0,0,0,0.2)', padding: '15px', borderRadius: '8px', color: '#cbd5e1', fontSize: '14px', borderLeft: '3px solid #8b5cf6' }}>
                        <strong>✨ Why you match: </strong> {job.match_reason}
                      </div>
                      {job.search_url && (
                        <div style={{ marginTop: '5px' }}>
                          <a href={job.search_url} target="_blank" rel="noopener noreferrer" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', background: 'linear-gradient(to right, #4f46e5, #7c3aed)', color: 'white', padding: '10px 20px', borderRadius: '8px', textDecoration: 'none', fontWeight: 'bold', fontSize: '14px', transition: 'opacity 0.2s' }} onMouseOver={e => e.currentTarget.style.opacity = 0.9} onMouseOut={e => e.currentTarget.style.opacity = 1}>
                            Apply on {job.platform || 'LinkedIn'} <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                          </a>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ padding: '30px', background: 'rgba(15, 23, 42, 0.6)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px', lineHeight: '1.7', color: '#f8fafc', fontSize: '15px' }}>
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    components={{
                      table: ({node, ...props}) => <div style={{overflowX: 'auto'}}><table style={{width: '100%', borderCollapse: 'collapse', margin: '20px 0', fontSize: '14px'}} {...props} /></div>,
                      th: ({node, ...props}) => <th style={{background: 'rgba(30, 41, 59, 0.8)', padding: '14px', borderBottom: '2px solid #475569', textAlign: 'left', color: '#c4b5fd'}} {...props} />,
                      td: ({node, ...props}) => <td style={{padding: '14px', borderBottom: '1px solid rgba(51, 65, 85, 0.5)'}} {...props} />,
                      h1: ({node, ...props}) => <h1 style={{color: '#a78bfa', borderBottom: '2px solid rgba(124, 58, 237, 0.5)', paddingBottom: '10px', marginTop: '28px', marginBottom: '16px'}} {...props} />,
                      h2: ({node, ...props}) => <h2 style={{color: '#a78bfa', borderBottom: '1px solid rgba(124, 58, 237, 0.3)', paddingBottom: '8px', marginTop: '24px', marginBottom: '14px'}} {...props} />,
                      h3: ({node, ...props}) => <h3 style={{color: '#818cf8', marginTop: '20px', marginBottom: '12px'}} {...props} />,
                      h4: ({node, ...props}) => <h4 style={{color: '#94a3b8', marginTop: '16px', marginBottom: '10px'}} {...props} />,
                      ul: ({node, ...props}) => <ul style={{paddingLeft: '24px', marginBottom: '16px'}} {...props} />,
                      ol: ({node, ...props}) => <ol style={{paddingLeft: '24px', marginBottom: '16px'}} {...props} />,
                      li: ({node, ...props}) => <li style={{marginBottom: '6px'}} {...props} />,
                      p: ({node, ...props}) => <p style={{marginBottom: '16px'}} {...props} />,
                      a: ({node, ...props}) => <a style={{color: '#38bdf8', textDecoration: 'none'}} {...props} />,
                      strong: ({node, ...props}) => <strong style={{color: '#e2e8f0', fontWeight: '700'}} {...props} />,
                      hr: ({node, ...props}) => <hr style={{border: 'none', borderTop: '1px solid rgba(51, 65, 85, 0.6)', margin: '24px 0'}} {...props} />
                    }}
                  >
                    {result}
                  </ReactMarkdown>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
