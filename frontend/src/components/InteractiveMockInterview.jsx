import React, { useState, useEffect, useRef } from 'react';

export default function InteractiveMockInterview({ questions, onComplete, onCancel }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [timeLeft, setTimeLeft] = useState(30);
  const [isRecording, setIsRecording] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [results, setResults] = useState([]);
  
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [hasFinishedRecording, setHasFinishedRecording] = useState(false);

  if (!questions || questions.length === 0) {
    return <div style={{ color: '#ef4444' }}>No questions available. Please cancel and try again.</div>;
  }

  const recognitionRef = useRef(null);
  const currentQuestion = questions[currentIndex];

  useEffect(() => {
    // Initialize Web Speech API
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = true;
      recognitionRef.current.interimResults = true;

      recognitionRef.current.onresult = (event) => {
        let currentTranscript = '';
        let currentInterim = '';
        
        for (let i = 0; i < event.results.length; i++) {
          if (event.results[i].isFinal) {
            currentTranscript += event.results[i][0].transcript + ' ';
          } else {
            currentInterim += event.results[i][0].transcript;
          }
        }
        
        setTranscript(currentTranscript);
        setInterimTranscript(currentInterim);
      };

      recognitionRef.current.onerror = (event) => {
        console.error("Speech recognition error", event.error);
      };
    } else {
      console.warn("Web Speech API is not supported in this browser.");
    }
  }, []);

  useEffect(() => {
    let timer;
    if (isRecording && timeLeft > 0) {
      timer = setInterval(() => {
        setTimeLeft((prev) => prev - 1);
      }, 1000);
    } else if (timeLeft === 0 && isRecording) {
      handleStopRecording();
    }
    return () => clearInterval(timer);
  }, [isRecording, timeLeft]);

  const handleStartRecording = () => {
    setTranscript('');
    setInterimTranscript('');
    setHasFinishedRecording(false);
    
    if (recognitionRef.current) {
      try {
        recognitionRef.current.start();
        setIsRecording(true);
        setTimeLeft(30);
      } catch (err) {
        console.error("Error starting recognition", err);
      }
    } else {
      alert("Your browser does not support speech recognition. Please use Google Chrome.");
    }
  };

  const handleStopRecording = () => {
    if (recognitionRef.current && isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
      setHasFinishedRecording(true);
    }
  };

  const handleSubmitAnswer = async () => {
    const finalTranscript = (transcript + ' ' + interimTranscript).trim();
    if (!finalTranscript) {
        alert("Please speak something before submitting.");
        return;
    }
    setEvaluating(true);
    
    try {
      const res = await fetch('http://localhost:8000/api/student/mock-interview/evaluate-transcript', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            user_transcript: finalTranscript,
            question: currentQuestion.question,
            ideal_answer: currentQuestion.ideal_answer
        })
      });
      const data = await res.json();
      
      const newResult = {
        question: currentQuestion.question,
        ideal_answer: currentQuestion.ideal_answer,
        score: data.score || 0,
        feedback: data.feedback || 'No feedback provided.',
        transcript: finalTranscript
      };
      
      const updatedResults = [...results, newResult];
      setResults(updatedResults);
      
      if (currentIndex < questions.length - 1) {
        setCurrentIndex(currentIndex + 1);
        setTimeLeft(30);
        setTranscript('');
        setInterimTranscript('');
        setHasFinishedRecording(false);
      } else {
        onComplete(updatedResults);
      }
    } catch (err) {
      console.error(err);
      alert('Error evaluating answer.');
    }
    setEvaluating(false);
  };

  const handleSkip = () => {
    if (isRecording) {
      handleStopRecording();
    }
    const skippedResult = {
      question: currentQuestion.question,
      ideal_answer: currentQuestion.ideal_answer,
      score: 0,
      feedback: 'Skipped.',
      transcript: 'Skipped without answering.'
    };
    const updatedResults = [...results, skippedResult];
    setResults(updatedResults);
    
    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setTimeLeft(30);
      setTranscript('');
      setInterimTranscript('');
      setHasFinishedRecording(false);
    } else {
      onComplete(updatedResults);
    }
  };

  return (
    <div style={{ background: '#1e2235', padding: '30px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.05)', marginTop: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <h3 style={{ margin: 0, color: '#a5b4fc' }}>Question {currentIndex + 1} of {questions.length}</h3>
        <button onClick={onCancel} style={{ background: 'transparent', border: '1px solid #ef4444', color: '#ef4444', padding: '5px 15px', borderRadius: '6px', cursor: 'pointer' }}>Cancel Interview</button>
      </div>
      
      <div style={{ background: 'rgba(0,0,0,0.2)', padding: '20px', borderRadius: '8px', marginBottom: '30px' }}>
        <h2 style={{ color: '#e2e8f0', margin: 0, lineHeight: '1.4' }}>{currentQuestion.question}</h2>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px' }}>
        {evaluating ? (
          <div style={{ color: '#38bdf8', fontWeight: 'bold' }}>⏳ Evaluating your answer...</div>
        ) : (
          <>
            <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
              <div style={{ 
                fontSize: '24px', 
                fontWeight: 'bold', 
                color: timeLeft <= 10 ? '#ef4444' : '#10b981',
                background: 'rgba(255,255,255,0.05)',
                padding: '10px 20px',
                borderRadius: '8px',
                width: '100px',
                textAlign: 'center'
              }}>
                00:{timeLeft.toString().padStart(2, '0')}
              </div>
              
              {!isRecording && !hasFinishedRecording ? (
                <button 
                  onClick={handleStartRecording}
                  style={{ background: '#ef4444', color: 'white', border: 'none', padding: '12px 24px', borderRadius: '50px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}
                >
                  <span style={{ display: 'inline-block', width: '12px', height: '12px', background: 'white', borderRadius: '50%' }}></span>
                  Start Recording
                </button>
              ) : isRecording ? (
                <button 
                  onClick={handleStopRecording}
                  style={{ background: 'transparent', color: '#ef4444', border: '2px solid #ef4444', padding: '10px 24px', borderRadius: '50px', fontWeight: 'bold', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}
                >
                  <span style={{ display: 'inline-block', width: '12px', height: '12px', background: '#ef4444', borderRadius: '2px' }}></span>
                  Stop Recording
                </button>
              ) : (
                <div style={{ display: 'flex', gap: '15px' }}>
                  <button 
                    onClick={() => { setHasFinishedRecording(false); setTranscript(''); setInterimTranscript(''); }}
                    style={{ background: 'transparent', border: '1px solid #cbd5e1', color: '#cbd5e1', padding: '10px 20px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}
                  >
                    🔄 Retake
                  </button>
                  <button 
                    onClick={handleSubmitAnswer}
                    style={{ background: 'linear-gradient(to right, #10b981, #059669)', color: 'white', border: 'none', padding: '10px 30px', borderRadius: '8px', cursor: 'pointer', fontWeight: 'bold' }}
                  >
                    ✅ Submit Answer
                  </button>
                </div>
              )}
            </div>

            <div style={{ background: 'rgba(255,255,255,0.02)', padding: '20px', borderRadius: '12px', width: '100%', minHeight: '100px', border: '1px dashed rgba(255,255,255,0.1)' }}>
                <h4 style={{ margin: '0 0 10px 0', color: '#94a3b8' }}>Live Transcript</h4>
                <div style={{ color: '#e2e8f0', fontSize: '16px', lineHeight: '1.5' }}>
                    {transcript} <span style={{ color: '#94a3b8' }}>{interimTranscript}</span>
                    {!transcript && !interimTranscript && !isRecording && !hasFinishedRecording && <span style={{ color: '#64748b', fontStyle: 'italic' }}>Click "Start Recording" and speak your answer...</span>}
                    {!transcript && !interimTranscript && isRecording && <span style={{ color: '#38bdf8', fontStyle: 'italic' }}>Listening...</span>}
                </div>
            </div>
            
            <button onClick={handleSkip} style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: '#cbd5e1', padding: '10px 20px', borderRadius: '8px', cursor: 'pointer', marginTop: '10px' }}>
              ⏭️ Skip Question
            </button>
          </>
        )}
      </div>
    </div>
  );
}

