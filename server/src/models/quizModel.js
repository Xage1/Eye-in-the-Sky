const db = require('../config/db');

const getAllQuizzes = async () => {
    const res = await db.query('SELECT * FROM quizzes');
    return res.rows;
};

const addQuiz = async (quiz) => {
    const { question, options, answer } = quiz;
    const res = await db.query(
    'INSERT INTO quizzes (question, options, answer) VALUES ($1, $2, $3) RETURNING *',
    [question, options, answer]
  );
  return res.rows[0];
};

module.exports = { getAllQuizzes, addQuiz };