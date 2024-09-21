import express from 'express';
import {openDatabase} from "./backend";

const app = express();
const port = 8000;
const db = openDatabase();

app.set('view engine', 'ejs');

app.get('/', (req, res) => {
  res.render('index', {});
});

app.listen(port, () => {
  console.log(`Backend listening at http://localhost:${port}`);
});
