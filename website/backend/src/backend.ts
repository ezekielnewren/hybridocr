import * as vision from '@google-cloud/vision';
import {MongoClient, MongoClientOptions} from "mongodb";

// const fs = require("fs");
import fs from "fs";

export interface HybridocrConfigExpress {
    sessionSecret: string
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


export async function performOcr(client: vision.ImageAnnotatorClient, base64Image: string): Promise<any> {
    const [result] = await client.textDetection({ image: { content: base64Image } });
    return result;
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

    const client = new MongoClient(config.mongodb.uri, opt);
    client.db(config.mongodb.dbname);
    return client;
}

