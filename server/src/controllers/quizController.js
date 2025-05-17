const Quiz = require('../models/quizModel');

const getQuizzes = async (req, res) => {
    try {
        const quizzes = await Quiz.getAllQuizzes();
        res.json(quizzes);
    } catch (err) {
        res.status(500).json({ error: 'Failed to fetch quizzes' });
    }
};

const createQuiz = async (req, res) => {
    try {
        const newQuiz = await Quiz.addQuiz(req.body);
        res.status(201).json(newQuiz);
    } catch (err) {
        res.status(500).json({ error: 'Failed to create a quiz' });
    }
};

module.exports = { getQuizzes, createQuiz };