import { useState } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  // Same-domain API base. Leave empty to call /qa directly.
  const API_URL = import.meta.env.VITE_API_URL || ''

  const handleAsk = async () => {
    if (!question.trim()) {
      alert('Please enter a question')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await axios.post(`${API_URL}/qa`, {
        question: question
      })
      setResult(response.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Something went wrong')
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      handleAsk()
    }
  }

  return (
    <div className="app">
      <div className="container">
        {/* Header */}
        <header className="header">
          <h1>🧠 Intelligent QA System</h1>
          <p>Enhanced with Query Planning & Decomposition</p>
        </header>

        {/* Input Section */}
        <div className="card">
          <div className="input-section">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask a complex question..."
              disabled={loading}
              className="question-input"
            />
            <button
              onClick={handleAsk}
              disabled={loading}
              className="ask-button"
            >
              {loading ? 'Thinking...' : 'Ask Question'}
            </button>
          </div>

          {/* Loading State */}
          {loading && (
            <div className="loading">
              <div className="spinner"></div>
              <p>Analyzing your question and searching for answers...</p>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="error">
              <strong>Error:</strong> {error}
              <p style={{ fontSize: '0.9em', marginTop: '10px' }}>
                Make sure the backend is running at {API_URL}
              </p>
            </div>
          )}

          {/* Results */}
          {result && !loading && (
            <>
              {/* Search Plan */}
              {result.plan && (
                <div className="result-section">
                  <div className="section-title">
                    <span className="section-icon">📋</span>
                    <span>Search Strategy</span>
                    <span className="badge">Planning</span>
                  </div>
                  <div className="plan-box">
                    {result.plan}
                  </div>
                </div>
              )}

              {/* Sub-questions */}
              {result.sub_questions && result.sub_questions.length > 0 && (
                <div className="result-section">
                  <div className="section-title">
                    <span className="section-icon">🔍</span>
                    <span>Sub-Questions Generated</span>
                    <span className="badge">{result.sub_questions.length}</span>
                  </div>
                  <ul className="sub-questions-list">
                    {result.sub_questions.map((sq, index) => (
                      <li key={index}>{sq}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Answer */}
              {result.answer && (
                <div className="result-section">
                  <div className="section-title">
                    <span className="section-icon">💡</span>
                    <span>Answer</span>
                    <span className="badge">Final</span>
                  </div>
                  <div className="answer-box">
                    {result.answer}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Example Questions */}
        <div className="card examples">
          <p>
            <strong>Try asking:</strong> "What are the advantages of vector databases and how do they handle scalability?"
          </p>
        </div>
      </div>
    </div>
  )
}

export default App