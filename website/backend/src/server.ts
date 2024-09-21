import express from 'express';
import {getConfig, openDatabase} from "./backend";

async function main() {
  const app = express();
  const config = await getConfig();
  const port = config.express.port;
  const dbClient = await openDatabase();
  const db = dbClient.db(config.mongodb.dbname);

  app.set('view engine', 'ejs');
  app.use(express.json());

  app.get('/', (req, res) => {
    res.render('index', {});
  });

  app.post('/save-email', async (req, res) => {
    const body = req.body;
    body.timestamp = Date.now()/1000;
    const colAnalytics = db.collection("analytics");
    const result = await colAnalytics.insertOne(body);
    res.send('{"result": "ok"}');
  })

  app.listen(port, () => {
    console.log(`Backend listening at http://localhost:${port}`);
  });
}

main().finally();