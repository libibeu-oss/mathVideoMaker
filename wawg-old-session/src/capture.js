const {chromium}=require('playwright');const fs=require('fs');
const cl=(x,a=0,b=1)=>Math.min(b,Math.max(a,x)),P=(t,a,b)=>cl((t-a)/(b-a)),eio=x=>x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2;
const FPS=30;
(async()=>{const b=await chromium.launch();const c=await b.newContext({viewport:{width:390,height:844},deviceScaleFactor:2,isMobile:true,hasTouch:true,locale:'he-IL'});
const p=await c.newPage();const base='file://'+process.argv[2];const out=process.argv[3];const only=process.argv[4];
const css='.skip{display:none!important} html{scroll-behavior:auto!important} ::-webkit-scrollbar{display:none}';
async function go(h){await p.goto(base+h);await p.addStyleTag({content:css});await p.waitForTimeout(1500)}
async function rect(fn){return p.evaluate(fn)}
const rects={};
const scenes={
 s1:{dur:4,route:'',frame:async t=>({y:0})},
 s2:{dur:4,route:'',frame:async t=>({y:eio(P(t,.5,3.6))*1830})},
 s3:{dur:4,route:'',frame:async t=>t<1.15?{y:2330}:{route:'#/he/explore?genre=house',y:eio(P(t,1.7,4))*420}},
 s4:{dur:4,route:'#/he/artist/djadja',frame:async t=>({y:eio(P(t,2.2,4))*70})},
 s5:{dur:5,route:'#/he/event/neon-bloom',frame:async t=>({y:0})},
 s6:{dur:4,route:'#/he/membership',frame:async t=>({y:1000+eio(P(t,.2,3.9))*330})},
};
for(const [name,sc] of Object.entries(scenes)){ if(only&&only!==name)continue;
  fs.mkdirSync(`${out}/${name}`,{recursive:true});await go(sc.route);let cur=sc.route;
  for(let i=0;i<sc.dur*FPS;i++){const t=i/FPS;const st=await sc.frame(t);
    if(st.route&&st.route!==cur){await go(st.route);cur=st.route}
    await p.evaluate(y=>window.scrollTo(0,y),Math.round(st.y));if(i===0)await p.waitForTimeout(600);
    await p.screenshot({path:`${out}/${name}/${String(i).padStart(4,'0')}.jpg`,type:'jpeg',quality:90});
    if(name==='s3'&&i===0)rects.s3_house=await rect(()=>{const a=[...document.querySelectorAll('a')].find(e=>e.getAttribute('href')==='/he/explore?genre=house');const r=a.getBoundingClientRect();return [r.x,r.y,r.width,r.height]});
    if(name==='s4'&&i===0)rects.s4_follow=await rect(()=>{const a=[...document.querySelectorAll('button')].find(e=>e.innerText.trim()==='מעקב');const r=a.getBoundingClientRect();return [r.x,r.y,r.width,r.height]});
    if(name==='s5'&&i===0)rects.s5_tickets=await rect(()=>{const a=[...document.querySelectorAll('button')].filter(e=>e.innerText.includes('לכרטיסים')).map(e=>e.getBoundingClientRect()).filter(r=>r.width>0&&r.y>0&&r.y<844)[0];return a?[a.x,a.y,a.width,a.height]:null});
    if(name==='s6'&&i===0)rects.s6_y=await rect(()=>[...document.querySelectorAll('h3')].map(e=>[e.innerText.slice(0,20),Math.round(e.getBoundingClientRect().y)]));
  }
  console.log('done',name);
}
let old={};try{old=JSON.parse(fs.readFileSync(out+'/rects.json'))}catch(e){}
fs.writeFileSync(out+'/rects.json',JSON.stringify({...old,...rects},null,1));console.log(JSON.stringify(rects));await b.close()})();
