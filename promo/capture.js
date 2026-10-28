// 使い方: npm i puppeteer-core したフォルダで node capture.js <demo.html> <out.mp4> [fps]（Chrome と ffmpeg が必要）
const puppeteer = require('puppeteer-core');
const { spawn } = require('child_process');
const path = require('path');
(async () => {
  const [html, out, fpsArg] = process.argv.slice(2);
  const fps = +(fpsArg || 30);
  const browser = await puppeteer.launch({ executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless: true, args: ['--force-device-scale-factor=1'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  await page.goto(require('url').pathToFileURL(path.resolve(html)).href + '?capture', { waitUntil: 'networkidle0' });
  await page.evaluate(() => document.fonts.ready);
  const fontsOk = await page.evaluate(() => [document.fonts.check('40px "Shippori Mincho"'), document.fonts.check('40px "Cormorant Garamond"')]);
  console.log('fonts', fontsOk);
  const dur = await page.evaluate(() => window.DURATION);
  const ff = spawn('ffmpeg', ['-y', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', '-preset', 'slow', '-movflags', '+faststart', out], { stdio: ['pipe', 'ignore', 'inherit'] });
  const n = Math.round(dur * fps);
  for (let i = 0; i < n; i++) {
    await page.evaluate(t => window.render(t), i / fps);
    const buf = await page.screenshot({ type: 'png' });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
  console.log('frames', n);
})();
