import express from 'express';
import {getConfig, openDatabase} from "./backend";

async function main(): Promise<bigint> {
  const config = await getConfig();
  console.log("read config");
  const port = config.express.port;
  const dbClient = await openDatabase();
  console.log("connected to the mongodb cluster");
  const db = dbClient.db(config.mongodb.dbname);
  console.log("switched to the database");
  const colLog = db.collection("log");
  const result = await colLog.insertOne({boot: Date.now()/1000});
  if (result) {
    console.log("inserted a document");
  } else {
    console.log("unable to insert document into database");
    return 1n;
  }


  const app = express();
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

  return 0n;
}

main().finally();
console.log("done");
