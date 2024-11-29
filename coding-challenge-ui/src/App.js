import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import Register from "./components/Register";
import Login from "./components/Login";
import ChallengeGenerator from "./components/ChallengeGenerator";
import SubmitSolution from "./components/SolutionEvaluator";
import ProtectedRoute from "./components/ProtectedRoute"; // Import the new ProtectedRoute component
import "./App.css";

const App = () => {
  return (
    <Router>
      <div className="app-container">
        <header className="navbar">
          <h1 className="app-title">Adaptive Coding Challenge</h1>
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
                <Link to="/submit-solution" className="nav-link">Submit Solution</Link>
              </li>
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
              path="/submit-solution"
              element={
                <ProtectedRoute>
                  <SubmitSolution />
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
