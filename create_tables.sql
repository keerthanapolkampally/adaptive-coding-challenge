CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE solved_challenges (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    challenge_id UUID DEFAULT gen_random_uuid(),
    topic VARCHAR(100),
    difficulty VARCHAR(20),
    language VARCHAR(50),
    status VARCHAR(20), -- Solved/Failed/In Progress
    submitted_at TIMESTAMP DEFAULT NOW()
);