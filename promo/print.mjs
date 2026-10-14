// print do anúncio-demo para o vídeo promocional (página real, servida por HTTP local)
import puppeteer from 'puppeteer-core';
const [url, out] = process.argv.slice(2);
const b = await puppeteer.launch({ executablePath: process.env.CHROME, args: ['--no-sandbox'] });
const p = await b.newPage();
await p.setViewport({ width: 1280, height: 900, deviceScaleFactor: 1.5 });
await p.goto(url, { waitUntil: 'networkidle0' });
await p.screenshot({ path: out });
await b.close();
