import React, { useState, useEffect } from "react";
import axios from "axios";

const SubmitSolution = () => {
  const [challenge, setChallenge] = useState(null); // Holds the challenge to solve
  const [solution, setSolution] = useState(""); // User's solution
  const [language, setLanguage] = useState("python"); // Selected language

  // Fetch selected challenge from local storage
  useEffect(() => {
    const fetchChallenge = async () => {
      const savedChallenge = JSON.parse(localStorage.getItem("selected_challenge"));
      if (savedChallenge) {
        setChallenge(savedChallenge); // Use selected challenge from local storage
      }
    };

    fetchChallenge(); // Call fetchChallenge when the component mounts
  }, []);

  // Submit the solution
  const handleSolutionSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem("access_token");
      const response = await axios.post(
        "http://127.0.0.1:8000/api/submit-solution",
        {
          challenge_id: challenge.id, // Use the selected challenge ID
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
      alert(response.data.feedback); // Show feedback from the backend
    } catch (error) {
      console.error("Failed to submit solution:", error);
      alert("Failed to submit the solution. Please try again.");
    }
  };

  return (
    <div>
      <h2>Submit Your Solution</h2>
      {challenge ? (
        <div>
          <h3>{challenge.title}</h3>
          <p>{challenge.description}</p>
          <form onSubmit={handleSolutionSubmit}>
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
            <button type="submit">Submit Solution</button>
          </form>
        </div>
      ) : (
        <p>Loading challenge... Please wait.</p>
      )}
    </div>
  );
};

export default SubmitSolution;
