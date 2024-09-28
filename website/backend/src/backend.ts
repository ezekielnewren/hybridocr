import * as vision from '@google-cloud/vision';
import {MongoClient, MongoClientOptions} from "mongodb";
import {Request, Response} from "express";

// const fs = require("fs");
import fs from "fs";
import * as net from "net";

export interface HybridocrConfigExpress {
    sessionSecret: string
    port: bigint
}

export interface HybridocrConfigMongodb {
    uri: string
    username: string
    password: string
    dbname: string
}

export interface HybridocrConfig {
    express: HybridocrConfigExpress
    mongodb: HybridocrConfigMongodb
}

export async function getConfig(): Promise<HybridocrConfig> {
    const x = process.env.HYBRIDOCR_CONFIG_FILE;
    if (!x) throw Error("HYBRIDOCR_CONFIG_FILE not defined");
    const raw = fs.readFileSync(x);
    return JSON.parse(raw.toString());
}


export function renderit(config: any, req: Request, res: Response, view: string, options?: object, callback?: (err: Error, html: string) => void): void {
    let target = req.headers.host;
    if (!target) {
      target = req.hostname
    }
    let opt = {production: false, gtag_id: null};
    if (options) {
        // @ts-ignore
        opt = options;
    }
    opt.production = ["hybridocr.com", "www.hybridocr.com"].includes(target);
    opt.gtag_id = config.express.gtag_id;
    return res.render(view, opt, callback);
}

export async function performOcr(client: vision.ImageAnnotatorClient, base64Image: string): Promise<any> {
    const [result] = await client.textDetection({ image: { content: base64Image } });
    return result;
}


export async function socketWillClose(socket: net.Socket, timeout: number = 5000): Promise<void> {
  return new Promise((resolve) => {
    const forceCloseTimeout = setTimeout(() => {
      if (!socket.destroyed) {
        socket.destroy();
      }
      resolve();
    }, timeout);

    socket.once('close', () => {
      clearTimeout(forceCloseTimeout);
      resolve();
    });
  });
}


export async function openDatabase(): Promise<MongoClient> {
    const config = await getConfig();

    const opt: MongoClientOptions = {
        ssl: true,
        auth: {
            username: config.mongodb.username,
            password: config.mongodb.password,
        }
    };

    return new MongoClient(config.mongodb.uri, opt);
}

