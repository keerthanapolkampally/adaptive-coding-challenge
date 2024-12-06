CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS challenges (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    topic VARCHAR(100) NOT NULL,
    difficulty VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS solved_challenges (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    challenge_id UUID REFERENCES challenges(id) ON DELETE CASCADE,
    language VARCHAR(50),
    status VARCHAR(20), -- Solved/Failed/In Progress
    feedback TEXT,
    submitted_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS test_cases (
    id SERIAL PRIMARY KEY,
    challenge_id UUID REFERENCES challenges(id) ON DELETE CASCADE,
    input JSON NOT NULL,
    output JSON NOT NULL
);

CREATE TABLE IF NOT EXISTS solutions (
    id SERIAL PRIMARY KEY,
    challenge_id UUID REFERENCES challenges(id) ON DELETE CASCADE,
    solution TEXT NOT NULL
);

ALTER TABLE users
ADD COLUMN IF NOT EXISTS last_login TIMESTAMP DEFAULT NULL;

ALTER TABLE challenges ADD COLUMN metadata JSON DEFAULT '{}';
ALTER TABLE challenges ADD COLUMN folder_name VARCHAR(255) DEFAULT '';
ALTER TABLE challenges ADD COLUMN embedding FLOAT[];

ALTER TABLE solved_challenges
DROP COLUMN id;

ALTER TABLE solved_challenges
ADD COLUMN id UUID PRIMARY KEY DEFAULT gen_random_uuid();
