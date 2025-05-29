const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');
const { Pool } = require('pg');
const quizRoutes = require('./routes/quizRoutes');


// Load environment variables
dotenv.config();

const app = express();
const PORT = process.env.PORT || 5000;

//Middleware
app.use(cors());
app.use(express.json());

//Test Route
app.get('/', (req, res) => {
    res.send('Astronomy API is running....');
});

// Import routes
app.use('/api/quizzes', quizRoutes);

// Start Server
app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});