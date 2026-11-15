const { chromium } = require('C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1112-737-0_26.1112.737.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules/playwright');
(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
  for (const [name,width,height] of [['desktop',1440,900],['mobile',390,844]]) {
    const page = await browser.newPage({ viewport:{width,height},deviceScaleFactor:1,isMobile:name==='mobile',hasTouch:name==='mobile' });
    const errors=[]; page.on('pageerror',e=>errors.push(e.message));
    await page.goto('http://127.0.0.1:4173/');
    await page.waitForLoadState('networkidle');
    await page.addStyleTag({content:'html { scroll-behavior: auto !important; }'});
    await page.locator('.scroll-journey').waitFor({state:'attached',timeout:5000}).catch(async e=>{throw Error(`${name} render failed: ${errors.join('; ')}; html=${(await page.locator('body').innerText()).slice(0,100)}`)});
    for(const [section,expected] of [['story','plant'],['method','umbrella'],['sources','wave']]){
      await page.evaluate(({id}) => { const el=document.querySelector(id==='story'?'.region-visual':id==='method'?'.window-visual':'.receipt-visual'); if(el) scrollTo({top:el.getBoundingClientRect().top+scrollY-innerHeight*.58+(id==='story'?innerHeight*.25:30),behavior:'instant'}); },{id:section});
      await page.waitForTimeout(400);
      const pose=await page.locator('.scroll-journey').getAttribute('data-pose');
      if(pose!==expected) throw Error(`${name} ${section}: ${pose}, expected ${expected}; scroll=${await page.evaluate(()=>scrollY)}`);
      const opacity=await page.locator('.scroll-journey').evaluate(el=>getComputedStyle(el).opacity);
      if(Number(opacity)<.9) throw Error(`${name} ${section}: character hidden at ${await page.evaluate(() => scrollY)}, section ${await page.locator('#'+section).evaluate(el=>el.getBoundingClientRect().top+scrollY)}`);
      await page.screenshot({path:`../journey_${name}_${section}.png`});
      if(section==='sources') {
        const first=await page.locator('.scroll-journey').getAttribute('data-frame');
        await page.waitForTimeout(800);
        const second=await page.locator('.scroll-journey').getAttribute('data-frame');
        if(first===second) {
          await page.waitForTimeout(420);
          if(first===await page.locator('.scroll-journey').getAttribute('data-frame')) throw Error(`${name} wave frame did not advance`);
        }
      }
    }
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)) throw Error(`${name} horizontal overflow`);
    if(errors.length) throw Error(`${name}: ${errors.join('; ')}`);
    console.log(name,'three scroll states passed');
    if(name==='mobile') {
      await page.evaluate(()=>scrollTo(0,0));
      await page.evaluate(() => {
        const hero=document.querySelector('.hero');
        const start=new Touch({identifier:1,target:hero,clientX:130,clientY:360});
        const end=new Touch({identifier:1,target:hero,clientX:320,clientY:365});
        hero.dispatchEvent(new TouchEvent('touchstart',{bubbles:true,touches:[start],changedTouches:[start]}));
        hero.dispatchEvent(new TouchEvent('touchend',{bubbles:true,touches:[],changedTouches:[end]}));
      });
      await page.locator('.workspace-grid').waitFor({state:'visible'});
      console.log('mobile right swipe opened investigation');
    }
    await page.close();
  }
  await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
