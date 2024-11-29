import React, { useState } from 'react';
import axios from 'axios';

const ChallengeGenerator = () => {
  const [topic, setTopic] = useState('');
  const [difficulty, setDifficulty] = useState('easy');
  const [challenge, setChallenge] = useState('');

  const generateChallenge = async () => {
    try {
      const token = localStorage.getItem("access_token"); // Retrieve the token
      const response = await axios.post(
        "http://127.0.0.1:8000/api/generate-challenge",
        {
          topic,
          difficulty,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`, // Add the token in headers
          },
        }
      );
      setChallenge(response.data.challenge);
    } catch (error) {
      console.error("Error generating challenge:", error);
      alert("Failed to generate challenge. Please ensure the backend is running and accessible.");
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>Generate a Coding Challenge</h2>
      <label>Topic:</label>
      <input
        type="text"
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
        placeholder="Enter a topic"
      />
      <br />
      <label>Difficulty:</label>
      <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
        <option value="easy">Easy</option>
        <option value="medium">Medium</option>
        <option value="hard">Hard</option>
      </select>
      <br />
      <button onClick={generateChallenge}>Generate Challenge</button>
      {challenge && (
        <div>
          <h3>Generated Challenge:</h3>
          <pre>{challenge}</pre>
        </div>
      )}
    </div>
  );
};

export default ChallengeGenerator;
