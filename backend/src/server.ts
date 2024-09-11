import express, { Request, Response } from 'express';

// Create an instance of express
const app = express();

// Define the port
const PORT = 8000;

// Middleware to parse incoming JSON requests
app.use(express.json());

// Simple route handler for the root URL
app.get('/', (req: Request, res: Response) => {
  res.send('Hello, World! This is an Express server in TypeScript.');
});

// Define a route to handle another request
app.get('/api/status', (req: Request, res: Response) => {
  res.json({ message: 'Server is running!', status: 'ok' });
});

// Start the server
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
