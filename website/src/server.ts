// import * as express from 'express';
import express from "express";
import path from 'path';

const app = express();

// Set the view engine to EJS
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

app.get('/', (req, res) => {
  // Data processed in TypeScript
  const data = {
    title: 'Hello, EJS with TypeScript!',
    items: ['item1', 'item2', 'item3']
  };

  // Pass data to the EJS template
  res.render('index', data);
});

const listen_port = 5000;

app.listen(listen_port, () => {
    console.log("Server is running on on http://localhost:"+listen_port);
});
