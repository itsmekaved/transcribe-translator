import React, { useState } from 'react';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [selectedLanguages, setSelectedLanguages] = useState([]);
  const [enableSentiment, setEnableSentiment] = useState(false);

  const [transcript, setTranscript] = useState('');
  const [translations, setTranslations] = useState({});
  const [sentiment, setSentiment] = useState(null);
  const [performance, setPerformance] = useState({});
  const [loading, setLoading] = useState(false);

  const availableLanguages = ['HI', 'ES', 'FR', 'DE'];

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleCheckboxChange = (lang) => {
    setSelectedLanguages((prev) =>
      prev.includes(lang) ? prev.filter((l) => l !== lang) : [...prev, lang]
    );
  };

  const handleSubmit = async () => {
    if (!file || selectedLanguages.length === 0) return;

    setLoading(true);
    setTranscript('');
    setTranslations({});
    setSentiment(null);
    setPerformance({});

    const formData = new FormData();
    formData.append('audio', file);
    selectedLanguages.forEach((lang) => formData.append('languages', lang));
    formData.append('sentiment', enableSentiment);

    try {
      const response = await fetch('http://127.0.0.1:5000/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      setTranscript(data.transcript || '');
      setTranslations(data.translations || {});
      setSentiment(data.sentiment || null);
      setPerformance(data.performance || {});
    } catch (error) {
      console.error('Error:', error);
      alert('Something went wrong!');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1>Audio Transcriber & Translator</h1>

      <input
        type="file"
        accept="audio/*"
        onChange={handleFileChange}
        className="file-input"
      />
      {file && <p>{file.name}</p>}

      <div className="language-options">
        <p>Select Target Languages:</p>
        {availableLanguages.map((lang) => (
          <label key={lang}>
            <input
              type="checkbox"
              checked={selectedLanguages.includes(lang)}
              onChange={() => handleCheckboxChange(lang)}
            />
            <span>{lang}</span>
          </label>
        ))}
      </div>

      <label className="sentiment-toggle">
        <input
          type="checkbox"
          checked={enableSentiment}
          onChange={() => setEnableSentiment(!enableSentiment)}
        />
        <span>Enable Sentiment Analysis</span>
      </label>

      <button onClick={handleSubmit} disabled={loading}>
        {loading ? 'Processing...' : 'Transcribe & Translate'}
      </button>

      <div className="output">
        {transcript && (
          <>
            <h2>Transcript</h2>
            <p>{transcript}</p>
          </>
        )}

        {Object.keys(translations).length > 0 && (
          <>
            <h2>Translations</h2>
            {Object.entries(translations).map(([lang, data]) => (
              <div key={lang} className="translation-block">
                <h3>{lang.toUpperCase()}:</h3>
                {data.text && (
                  <p style={{ whiteSpace: 'pre-wrap' }}>{data.text}</p>
                )}
                {data.audio && (
                  <audio controls src={data.audio}>
                    Your browser does not support the audio element.
                  </audio>
                )}
              </div>
            ))}
          </>
        )}

        {sentiment && (
          <>
            <h2>Sentiment Analysis</h2>
            <p><strong>Polarity:</strong> {sentiment.polarity}</p>
            <p><strong>Subjectivity:</strong> {sentiment.subjectivity}</p>
            <p><strong>Rating:</strong> {sentiment.rating}</p>
          </>
        )}

        {Object.keys(performance).length > 0 && (
          <>
            <h2>Performance</h2>
            <p><strong>Speech-to-Text:</strong> {performance.speech_to_text_seconds} seconds</p>
            <p><strong>Translation:</strong> {performance.translation_seconds} seconds</p>
            <p><strong>Sentiment Analysis:</strong> {performance.sentiment_analysis_seconds} seconds</p>
          </>
        )}
      </div>
    </div>
  );
}

export default App;
