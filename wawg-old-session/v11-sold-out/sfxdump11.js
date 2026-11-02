const {chromium}=require('playwright');const path=require('path');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
await p.goto('file://'+path.resolve('ad11.html'));await p.evaluate(()=>window.READY);
require('fs').writeFileSync('a/sfx11.json',JSON.stringify(await p.evaluate(()=>window.SFX)));await b.close()})();
