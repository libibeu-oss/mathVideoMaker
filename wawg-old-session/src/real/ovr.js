const {chromium}=require('playwright');const path=require('path');
(async()=>{const [,,html,out,a,b]=process.argv;const br=await chromium.launch();const p=await br.newPage({viewport:{width:1080,height:1920}});
await p.goto('file://'+path.resolve(html));await p.evaluate(()=>window.READY);
for(let i=+a;i<+b;i++){await p.evaluate(t=>R(t),i/30);await p.screenshot({path:`${out}/${String(i).padStart(4,'0')}.png`,omitBackground:true})}
await br.close()})();
