import React, { useState } from 'react';
import axios from 'axios';

const SubmitSolution = () => {
  const [solution, setSolution] = useState('');
  const [feedback, setFeedback] = useState('');
  const [language, setLanguage] = useState('python'); // Default language

  const submitSolution = async () => {
    try {
      const response = await axios.post('http://127.0.0.1:8000/api/submit-solution', {
        solution,
        language, // Include language in the payload
      });
      if (response.data && response.data.feedback) {
        setFeedback(response.data.feedback);
      } else {
        throw new Error('Unexpected response structure from backend.');
      }
    } catch (error) {
      console.error('Error submitting solution:', error);
      alert('Failed to submit solution. Please ensure the backend is running and accessible.');
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>Submit Your Solution</h2>
      <textarea
        value={solution}
        onChange={(e) => setSolution(e.target.value)}
        placeholder="Paste your solution code here"
        style={{ width: '100%', height: '150px' }}
      />
      <br />
      <label htmlFor="language-select">Select Language:</label>
      <select
        id="language-select"
        value={language}
        onChange={(e) => setLanguage(e.target.value)}
        style={{ margin: '10px', padding: '5px' }}
      >
        <option value="python">Python</option>
        <option value="javascript">JavaScript</option>
        <option value="java">Java</option>
        <option value="c++">C++</option>
        <option value="c">C</option>
      </select>
      <br />
      <button onClick={submitSolution}>Submit Solution</button>
      {feedback && (
        <div>
          <h3>Feedback:</h3>
          <pre>{feedback}</pre>
        </div>
      )}
    </div>
  );
};

export default SubmitSolution;