import React, { useState, useEffect } from "react";
import axios from "axios";

const Profile = () => {
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const token = localStorage.getItem("access_token"); // Assuming token is stored in localStorage
        const response = await axios.get("http://127.0.0.1:8000/api/user-history", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        setHistory(response.data.history);
      } catch (err) {
        setError("Failed to fetch user history. Please try again.");
      }
    };

    fetchHistory();
  }, []);

  return (
    <div style={{ padding: "20px" }}>
      <h2>User Profile</h2>
      {error && <p style={{ color: "red" }}>{error}</p>}
      <h3>Challenge History</h3>
      {history.length > 0 ? (
        <table border="1" cellPadding="10" cellSpacing="0">
          <thead>
            <tr>
              <th>Challenge ID</th>
              <th>Topic</th>
              <th>Difficulty</th>
              <th>Language</th>
              <th>Status</th>
              <th>Submitted At</th>
            </tr>
          </thead>
          <tbody>
            {history.map((challenge) => (
              <tr key={challenge.challenge_id}>
                <td>{challenge.challenge_id}</td>
                <td>{challenge.topic}</td>
                <td>{challenge.difficulty}</td>
                <td>{challenge.language}</td>
                <td>{challenge.status}</td>
                <td>{new Date(challenge.submitted_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <p>No challenges found.</p>
      )}
    </div>
  );
};

export default Profile;
