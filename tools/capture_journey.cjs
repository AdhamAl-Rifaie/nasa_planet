const { chromium } = require('C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1112-737-0_26.1112.737.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules/playwright');
const fs = require('node:fs');
const path = require('node:path');
(async () => {
  const browser = await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
  const context = await browser.newContext({viewport:{width:390,height:844},deviceScaleFactor:1,recordVideo:{dir:'../journey-video',size:{width:390,height:844}}});
  const page = await context.newPage();
  await page.goto('http://127.0.0.1:4173/');
  await page.locator('.scroll-journey').waitFor({state:'attached',timeout:15000});
  await page.addStyleTag({content:'html { scroll-behavior:auto !important }'});
  for (const [selector,delay] of [['.region-visual',220],['.window-visual',30],['.receipt-visual',30]]) {
    await page.evaluate(({selector,delay}) => {const el=document.querySelector(selector);scrollTo({top:el.getBoundingClientRect().top+scrollY-innerHeight*.58+delay,behavior:'instant'});},{selector,delay});
    await page.waitForTimeout(1550);
  }
  const video=page.video();
  await context.close();
  const output=path.resolve('../journey-mobile-demo.webm');
  fs.copyFileSync(await video.path(),output);
  await browser.close();
  console.log(output);
})().catch(e=>{console.error(e);process.exit(1)});
