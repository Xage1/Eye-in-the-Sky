const db = require('../config/db');

const getAllQuizzes = async () => {
  const res = await db.query('SELECT * FROM quizzes');
  return res.rows;
};

// Add a new quiz
const addQuiz = async (quiz) => {
  const { title, description, category, difficulty, answer } = quiz;
  const res = await db.query(
    'INSERT INTO quizzes (title, description, category, difficulty, answer) VALUES ($1, $2, $3, $4, $5) RETURNING *',
    [title, description, category, difficulty, answer]
  );
  return res.rows[0];
};

module.exports = { getAllQuizzes, addQuiz };