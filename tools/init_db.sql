-- PostgreSQL Database Initialization Script

CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active'
);

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id),
    role VARCHAR(20) NOT NULL, -- user, assistant, system
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- AI Agent metadata
    tokens_used INTEGER,
    model_used VARCHAR(50),
    validation_score FLOAT,
    is_hallucination BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS agent_actions (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id),
    action_type VARCHAR(50) NOT NULL, -- propose, critique, judge, execute
    content TEXT,
    source_node VARCHAR(100), -- GPU/Arc/CPU node identifier
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_messages_session ON messages(session_id);
CREATE INDEX idx_messages_created ON messages(created_at DESC);
CREATE INDEX idx_sessions_user ON sessions(user_id);

-- Insert initial admin session if needed
INSERT INTO sessions (user_id, status) 
SELECT 'system_admin', 'active' 
WHERE NOT EXISTS (
    SELECT 1 FROM sessions WHERE user_id = 'system_admin'
);