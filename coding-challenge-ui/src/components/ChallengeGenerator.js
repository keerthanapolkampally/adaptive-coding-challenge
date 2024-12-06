import React, { useState } from "react";
import axios from "axios";

const ChallengeGenerator = () => {
  const [topic, setTopic] = useState("");
  const [difficulty, setDifficulty] = useState("medium");
  const [challenge, setChallenge] = useState(null);
  const [solution, setSolution] = useState("");
  const [language, setLanguage] = useState("python");
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState(""); // Store feedback for display

  const generateChallenge = async () => {
    if (!topic.trim()) {
      setFeedback("Please enter a valid topic.");
      return;
    }

    setIsLoading(true);
    try {
      const token = localStorage.getItem("access_token");
      const response = await axios.post(
        "http://127.0.0.1:8000/api/generate-challenge",
        { topic, difficulty },
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );
      console.log("Generated Challenge Response:", response.data);
      setChallenge(response.data);
      setFeedback(""); // Clear feedback when generating a new challenge
    } catch (error) {
      console.error("Error generating challenge:", error);
      setFeedback("Failed to generate challenge. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSolutionSubmit = async () => {
    if (!challenge || !challenge.id) {
      setFeedback("No valid challenge to submit. Please generate a challenge first.");
      return;
    }

    if (!solution.trim()) {
      setFeedback("Please provide a solution before submitting.");
      return;
    }

    setIsSubmitting(true);
    try {
      const token = localStorage.getItem("access_token");
      const response = await axios.post(
        "http://127.0.0.1:8000/api/submit-solution",
        {
          challenge_id: challenge.id,
          solution,
          language,
        },
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );
      setFeedback(response.data.feedback); // Display feedback from backend
    } catch (error) {
      console.error("Error submitting solution:", error);
      setFeedback("Failed to submit the solution. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div>
      <h2>Generate and Solve a Challenge</h2>
      
      {/* Topic Selection */}
      <label htmlFor="topic">Select Topic:</label>
      <input
        id="topic"
        type="text"
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
        placeholder="Enter topic (e.g., Arrays, Graphs)"
      />
      <br />

      {/* Difficulty Selection */}
      <label htmlFor="difficulty">Select Difficulty:</label>
      <select
        id="difficulty"
        value={difficulty}
        onChange={(e) => setDifficulty(e.target.value)}
      >
        <option value="easy">Easy</option>
        <option value="medium">Medium</option>
        <option value="hard">Hard</option>
      </select>
      <br />

      {/* Generate Challenge Button */}
      <button onClick={generateChallenge} disabled={isLoading}>
        {isLoading ? "Generating..." : "Generate Challenge"}
      </button>

      {/* Generated Challenge and Solution Submission */}
      {challenge && (
        <div>
          <h3>{challenge.title || "No Title Available"}</h3>
          <p>{challenge.description || "No Description Available"}</p>

          {/* Solution Language Selection */}
          <div>
            <label htmlFor="language">Language:</label>
            <select
              id="language"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
              <option value="java">Java</option>
              <option value="cpp">C++</option>
            </select>
          </div>

          {/* Solution Input */}
          <div>
            <label htmlFor="solution">Your Solution:</label>
            <textarea
              id="solution"
              value={solution}
              onChange={(e) => setSolution(e.target.value)}
              rows="10"
              cols="50"
              placeholder="Write your solution here..."
            ></textarea>
          </div>

          {/* Submit Solution Button */}
          <button onClick={handleSolutionSubmit} disabled={isSubmitting}>
            {isSubmitting ? "Submitting..." : "Submit Solution"}
          </button>
        </div>
      )}

      {/* Feedback Section */}
      {feedback && (
        <div style={{ marginTop: "20px", color: "blue" }}>
          <h4>Feedback:</h4>
          <p>{feedback}</p>
        </div>
      )}
    </div>
  );
};

export default ChallengeGenerator;
