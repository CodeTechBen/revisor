DROP TABLE IF EXISTS answer_history;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS answer;
DROP TABLE IF EXISTS question;
DROP TABLE IF EXISTS topic;

CREATE TABLE topic (
  topic_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  topic_name VARCHAR(32) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE question (
  question_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  topic_id INTEGER NOT NULL,
  question_text TEXT NOT NULL,
  contextual_info TEXT,
  CONSTRAINT fk_question_topic
    FOREIGN KEY (topic_id) REFERENCES topic(topic_id)
);

CREATE TABLE answer (
  answer_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  question_id INTEGER NOT NULL,
  answer_text TEXT NOT NULL,
  is_correct BOOLEAN NOT NULL DEFAULT false,
  CONSTRAINT fk_answer_question
    FOREIGN KEY (question_id) REFERENCES question(question_id)
);

CREATE TABLE users (
  user_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);


CREATE TABLE answer_history (
  answer_history_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  answer_time TIMESTAMPTZ NOT NULL DEFAULT now(),
  answer_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  CONSTRAINT fk_history_answer
    FOREIGN KEY (answer_id) REFERENCES answer(answer_id),
  CONSTRAINT fk_history_user
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE exam (
  exam_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id INTEGER NOT NULL,
  start_time TIMESTAMPTZ NOT NULL DEFAULT now(),
  end_time TIMESTAMPTZ,
  total_questions INTEGER NOT NULL,
  duration_minutes INTEGER NOT NULL,
  score_percent NUMERIC,
  CONSTRAINT fk_exam_user
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE exam_question (
  exam_question_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  exam_id INTEGER NOT NULL,
  question_id INTEGER NOT NULL,
  CONSTRAINT fk_exam_question_exam
    FOREIGN KEY (exam_id) REFERENCES exam(exam_id),
  CONSTRAINT fk_exam_question_question
    FOREIGN KEY (question_id) REFERENCES question(question_id)
);

CREATE TABLE exam_answer (
  exam_answer_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  exam_id INTEGER NOT NULL,
  question_id INTEGER NOT NULL,
  answer_id INTEGER,
  is_correct BOOLEAN,
  CONSTRAINT fk_exam_answer_exam
    FOREIGN KEY (exam_id) REFERENCES exam(exam_id)
);

-- Indexes
CREATE INDEX idx_question_topic_id ON question(topic_id);
CREATE INDEX idx_answer_question_id ON answer(question_id);
CREATE INDEX idx_answer_history_user_id ON answer_history(user_id);


-- SEED DATA
INSERT INTO topic (topic_name) VALUES
('Collibra'),
('DAMA DMBOX');