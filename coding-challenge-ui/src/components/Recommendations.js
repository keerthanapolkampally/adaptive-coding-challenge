import React, { useState, useEffect } from "react";
import axios from "axios";

const Recommendations = () => {
  const [recommendations, setRecommendations] = useState([]);
  const [selectedChallenge, setSelectedChallenge] = useState(null);
  const [solution, setSolution] = useState("");
  const [language, setLanguage] = useState("python");
  const [submissionFeedback, setSubmissionFeedback] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const fetchRecommendations = async () => {
      try {
        const token = localStorage.getItem("access_token");
        const response = await axios.get("http://127.0.0.1:8000/api/recommend-challenges", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setRecommendations(response.data.recommendations);
      } catch (error) {
        console.error("Failed to fetch recommendations:", error);
      }
    };
    fetchRecommendations();
  }, []);

  const selectChallenge = async (challengeId) => {
    setIsLoading(true);
    console.log("Selecting Challenge ID:", challengeId);
    try {
      const token = localStorage.getItem("access_token");
      const response = await axios.post(
        "http://127.0.0.1:8000/api/select-recommended-challenge",
        { challenge_id: challengeId },
        { headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" } }
      );
      console.log("Response from select challenge:", response.data);
  
      // Set selected challenge details
      setSelectedChallenge({
        id: response.data.challenge.id,
        title: response.data.challenge.title,
        description: response.data.challenge.description,
        from_database: response.data.challenge.from_database || false,
      });
    } catch (error) {
      console.error("Failed to select challenge:", error.response?.data || error.message);
      alert("Failed to select the challenge. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };
  
  const submitSolution = async (e) => {
    e.preventDefault();
    if (!selectedChallenge) {
      alert("Please select a challenge before submitting a solution.");
      return;
    }
    console.log("Submit Payload:", {
      challenge_id: selectedChallenge?.id,
      solution,
      language,
    });
    try {
      const token = localStorage.getItem("access_token");
      const response = await axios.post(
        "http://127.0.0.1:8000/api/submit-solution",
        {
          challenge_id: selectedChallenge.id,
          solution,
          language,
          is_llm_generated: selectedChallenge?.from_database === false,
        },
        { headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" } }
      );
      console.log("Submit Response:", response.data);
      setSubmissionFeedback(response.data.feedback);
    } catch (error) {
      console.error("Error submitting solution:", error.response?.data || error.message);
      setSubmissionFeedback("Failed to submit the solution. Please try again.");
    }
  };
  
  return (
    <div>
      <h2>Recommended Challenges</h2>
      <ul>
        {recommendations.map((challenge) => (
          <li key={challenge.id}>
            <h3>{challenge.title}</h3>
            <p>{challenge.description}</p>
            <button onClick={() => selectChallenge(challenge.id)}>Select Challenge</button>
          </li>
        ))}
      </ul>
      {selectedChallenge && (
        <div>
          <h3>Selected Challenge:</h3>
          <h4>{selectedChallenge.title}</h4>
          <p>{selectedChallenge.description}</p>
          <form onSubmit={submitSolution}>
            <label htmlFor="language">Language:</label>
            <select id="language" value={language} onChange={(e) => setLanguage(e.target.value)}>
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
              <option value="java">Java</option>
              <option value="cpp">C++</option>
            </select>
            <textarea
              value={solution}
              onChange={(e) => setSolution(e.target.value)}
              rows="5"
              cols="50"
              placeholder="Write your solution here..."
            />
            <button type="submit">Submit Solution</button>
            {submissionFeedback && <p>{submissionFeedback}</p>}
          </form>
        </div>
      )}
      {isLoading && <p>Loading...</p>}
    </div>
  );
};

export default Recommendations;
