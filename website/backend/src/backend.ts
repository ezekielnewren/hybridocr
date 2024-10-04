import * as vision from '@google-cloud/vision';
import {MongoClient, MongoClientOptions} from "mongodb";
import {Request, Response, NextFunction} from "express";
import { RedisClientType, createClient } from 'redis';

// const fs = require("fs");
import fs from "fs";
import * as net from "net";

export interface HybridocrConfigExpress {
    sessionSecret: string
    gtag_id: string
    production: boolean
    port: bigint
}

export interface HybridocrConfigMongodb {
    uri: string
    username: string
    password: string
    dbname: string
}

export interface HybridocrConfigRedis {
    node: {host: string, port: number}[]
    auth: any
}

export interface HybridocrConfig {
    express: HybridocrConfigExpress
    mongodb: HybridocrConfigMongodb
    redis: HybridocrConfigRedis
    docker_prefix: string
}

export async function getConfig(): Promise<HybridocrConfig> {
    const x = process.env.HYBRIDOCR_CONFIG_FILE;
    if (!x) throw Error("HYBRIDOCR_CONFIG_FILE not defined");
    const raw = fs.readFileSync(x);
    let config: HybridocrConfig = JSON.parse(raw.toString());
    if (!config.express.production) {
        config.express.production = false;
    }
    return config;
}


export function renderit(config: any, req: Request, res: Response, view: string, options?: object, callback?: (err: Error, html: string) => void): void {
    let opt = {production: false, gtag_id: null};
    if (options) {
        // @ts-ignore
        opt = options;
    }
    opt.production = config.express.production;
    opt.gtag_id = config.express.gtag_id;
    return res.render(view, opt, callback);
}

export async function performOcr(client: vision.ImageAnnotatorClient, base64Image: string): Promise<any> {
    const [result] = await client.textDetection({image: {content: base64Image}});
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


export async function openDatabase(config: HybridocrConfig): Promise<MongoClient> {
    const opt: MongoClientOptions = {
        ssl: true,
        auth: {
            username: config.mongodb.username,
            password: config.mongodb.password,
        }
    };

    return new MongoClient(config.mongodb.uri, opt);
}

export async function openRedis(config: HybridocrConfig): Promise<RedisClientType> {
    // @ts-ignore
    const client = new createClient({
        password: config.redis.auth.password,
        socket: {
            host: config.redis.node[0].host,
            port: config.redis.node[0].port
        }
    });
    await client.connect();
    return client;
}

// import express, { Request, Response, NextFunction } from 'express';

export class Session {
    public static readonly ID = "SESSIONID";

    store: RedisClientType


    constructor(_store: RedisClientType) {
        this.store = _store;
    }

    public call = async (req: Request, res: Response, next: NextFunction)=> {
        console.log(req.cookies);

        const id = req.cookies[Session.ID];

        if (!id || !await this.store.exists(Session.ID)) {
            await this.store.set(Session.ID, "");

        }

        next();
    }
}

