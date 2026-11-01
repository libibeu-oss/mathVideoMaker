// render ad5 (ad2 with a transparent stage) at given ad2 times -> RGBA PNGs
const {chromium}=require('playwright');const path=require('path');
(async()=>{const [,,html,out,...pairs]=process.argv;const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.goto('file://'+path.resolve(html));await p.evaluate(()=>window.READY);
for(const pr of pairs){const [i,t]=pr.split(':');await p.evaluate(t=>R(t),+t);await p.screenshot({path:`${out}/${i}.png`,omitBackground:true})}
await b.close()})();
