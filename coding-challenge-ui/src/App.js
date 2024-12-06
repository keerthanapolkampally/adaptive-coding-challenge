import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import Register from "./components/Register";
import Login from "./components/Login";
import ChallengeGenerator from "./components/ChallengeGenerator";
import SubmitSolution from "./components/SolutionEvaluator";
import ProtectedRoute from "./components/ProtectedRoute"; // Import the new ProtectedRoute component
import Profile from "./components/Profile";
import Recommendations from "./components/Recommendations";
import "./App.css";

const App = () => {
  // const isAuthenticated = !!localStorage.getItem("access_token"); // Check if user is logged in

  // const handleLogout = () => {
  //   localStorage.removeItem("access_token"); // Remove token from storage
  //   window.location.href = "/login"; // Redirect to login page
  // };
  return (
    <Router>
      <div className="app-container">
        <header className="navbar">
          <h1 className="app-title">Adaptive Coding Challenge Generator</h1>
          <nav>
            <ul className="nav-links">
              <li>
                <Link to="/register" className="nav-link">Register</Link>
              </li>
              <li>
                <Link to="/login" className="nav-link">Login</Link>
              </li>
              <li>
                <Link to="/generate-challenge" className="nav-link">Generate Challenge</Link>
              </li>
              <li>
                    <Link to="/recommendations" className="nav-link">Recommendations</Link>
              </li>
              <li>
                <Link to="/profile" className="nav-link">Profile</Link>
              </li>
              {/* <li>
                    <button onClick={handleLogout} className="nav-link logout-btn">Logout</button>
              </li> */}
            </ul>
          </nav>
        </header>
        <main className="main-content">
          <Routes>
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
            {/* Protect these routes */}
            <Route
              path="/generate-challenge"
              element={
                <ProtectedRoute>
                  <ChallengeGenerator />
                </ProtectedRoute>
              }
            />
            <Route
              path="/recommendations"
              element={
                <ProtectedRoute>
                  <Recommendations />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <Profile />
                </ProtectedRoute>
              }
            />
          </Routes>
        </main>
      </div>
    </Router>
  );
};

export default App;
