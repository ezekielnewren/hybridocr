import express from 'express';
import {renderit, getConfig, openDatabase, socketWillClose} from "./backend";
import {MongoClient} from "mongodb";
import * as net from "net";

let server: any;
let dbClient: MongoClient;

async function main(): Promise<bigint> {
  // read in the config
  const config = await getConfig();
  console.log("read config");
  const port = config.express.port;

  // open the database
  dbClient = await openDatabase();
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
  app.set('trust proxy', true);
  app.use(express.json());
  app.set('view engine', 'ejs');

  app.get('/', (req, res) => {
    renderit(config, req, res, 'index');
  });

  app.get('/register', (req, res) => {
    renderit(config, req, res, 'register');
  });

  app.get('/about', (req, res) => {
    renderit(config, req, res, 'about');
  });

  app.get('/liveness', (req, res) => {
    res.status(200).send('Alive');
  });

  app.get('/readiness', (req, res) => {
    res.status(200).send('Ready');
  });

  app.post('/save-email', async (req, res) => {
    const body = req.body;
    body.timestamp = Date.now()/1000;
    const colAnalytics = db.collection("analytics");
    const result = await colAnalytics.insertOne(body);
    res.send('{"result": "ok"}');
  })

  // start the server
  server = app.listen(port, () => {
    console.log(`Backend listening at http://localhost:${port}`);
  });

  // track active connections
  let connections = new Set<net.Socket>();

  server.on('connection', (socket: net.Socket) => {
    connections.add(socket);

    socket.on('close', () => {
      connections.delete(socket);
    });
  });

  // wait for the server to close
  await new Promise<void>((resolve, reject) => {
    const shutdown = async () => {
      server.close();
      let waitingPool = new Array<Promise<void>>();
      for (let socket of connections) {
        waitingPool.push(socketWillClose(socket, 5000));
      }
      await Promise.all<void>(waitingPool);
      await dbClient.close();
      resolve();
    };

    process.on('SIGINT', shutdown);
    process.on('SIGTERM', shutdown);
  });

  return 0n;
}

main().finally(() => {
  console.log("bye");
});

