import express from 'express';
import {openDatabase} from "./backend";

const app = express();
const port = 8000;
const db = openDatabase();

app.get('/', (req, res) => {
  res.send('Hello from the backend!');
});

app.listen(port, () => {
  console.log(`Backend listening at http://localhost:${port}`);
});
