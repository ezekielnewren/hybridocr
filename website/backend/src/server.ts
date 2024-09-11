import express from 'express';

import { greet } from 'common';

const message = greet('Backend');
console.log(message);


const app = express();
const port = 8000;

app.get('/', (req, res) => {
  res.send('Hello from the backend!');
});

app.listen(port, () => {
  console.log(`Backend listening at http://localhost:${port}`);
});
