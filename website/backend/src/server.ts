import express, { Request, Response } from 'express';
import path from 'path';

// Create an instance of express
const app = express();

// Define the port
const PORT = 8000;

// Middleware to parse incoming JSON requests
app.use(express.json());

// Simple route handler for the root URL
app.get('/', (req: Request, res: Response) => {
  res.sendFile(path.join(__dirname, "../static/index.html"))
});

// Define a route to handle another request
app.get('/api/status', (req: Request, res: Response) => {
  res.json({ message: 'Server is running!', status: 'ok' });
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
