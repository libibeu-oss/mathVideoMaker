// ad4: group-chat scenes ("מה עושים הערב?") over the ad2 timeline
const CHAT_IN=[[0,13.5],[21.5,26.9]];
const chatEl=$(`<div class="fill" style="z-index:205;display:none;background:#0b0418">
  <div class="cbg photo-bg" style="filter:blur(16px) brightness(.45) saturate(1.2)"></div>
  <div class="fill" style="background:radial-gradient(80% 60% at 50% 40%,rgba(162,75,255,.25),rgba(11,4,24,.7))"></div>
  <div class="phone" style="top:120px"><div class="scr" style="background:linear-gradient(180deg,#1b0c38,#120726)">
    <div class="island"></div>
    <div style="position:absolute;top:70px;left:0;right:0;height:96px;display:flex;align-items:center;gap:14px;padding:0 26px;background:rgba(36,18,72,.95);border-bottom:1px solid rgba(255,255,255,.08);z-index:20">
      <div style="width:62px;height:62px;border-radius:50%;background:linear-gradient(135deg,#ff4fd8,#a24bff);display:grid;place-items:center;font-size:30px">🎉</div>
      <div><div style="font-size:28px;font-weight:700">הערב יוצאים</div><div style="font-size:20px;color:#c4b3e6">נועה, איתי, מאיה</div></div></div>
    <div class="msgs" style="position:absolute;top:170px;bottom:100px;left:0;right:0;display:flex;flex-direction:column;justify-content:flex-end;gap:14px;padding:0 20px;overflow:hidden"></div>
    <div style="position:absolute;bottom:22px;left:20px;right:20px;height:64px;border-radius:32px;background:#2a1550;display:flex;align-items:center;padding:0 24px;color:#8f7bb8;font-size:22px">הודעה</div>
  </div></div></div>`);
stage.appendChild(chatEl);
const cbg=chatEl.querySelector('.cbg'),msgs=chatEl.querySelector('.msgs'),cphone=chatEl.querySelector('.phone');
const WHO={'נועה':['#ff7ae0',1],'איתי':['#33d6ff',0],'מאיה':['#ffb340',0]};
function wave(seed){const r=rng(seed);let s='';for(let i=0;i<26;i++){const h=8+r()*30;s+=`<i style="display:inline-block;width:5px;height:${h}px;margin:0 2px;border-radius:3px;background:currentColor;vertical-align:middle"></i>`}return s}
const M=[];
function msg(t0,who,html,{voice=null,typing=true}={}){
  const [col,mine]=WHO[who];
  const el=$(`<div style="display:flex;flex-direction:column;align-items:${mine?'flex-end':'flex-start'};display:none">
    <div class="bub" style="max-width:400px;padding:14px 18px;border-radius:24px;${mine?'border-bottom-left-radius:6px;background:linear-gradient(135deg,#d93fd0,#8a3cff)':'border-bottom-right-radius:6px;background:#2d1858'};box-shadow:0 6px 18px rgba(0,0,0,.3)">
      ${mine?'':`<div style="font-size:19px;font-weight:700;color:${col};margin-bottom:4px">${who}</div>`}${html}</div></div>`);
  msgs.appendChild(el);const tp=typing&&!mine?$(`<div style="align-self:flex-start;display:none;padding:14px 22px;border-radius:24px;background:#2d1858;font-size:30px;letter-spacing:4px;color:#c4b3e6">•••</div>`):null;
  if(tp)msgs.insertBefore(tp,el);
  M.push({t0,el,tp,voice});return el}
function voiceNote(seed,dur,text){return `<div class="vn" style="display:flex;align-items:center;gap:12px;direction:ltr"><span style="font-size:26px">▶</span><span class="wv" style="position:relative;color:rgba(255,255,255,.35);white-space:nowrap">${wave(seed)}<span class="wvp" style="position:absolute;inset:0;color:#fff;overflow:hidden;white-space:nowrap;width:0">${wave(seed)}</span></span><span style="font-size:18px;opacity:.8">0:0${Math.ceil(dur)}</span></div><div style="font-size:24px;line-height:1.35;margin-top:8px;opacity:.95">${text}</div>`}
// voice lines: [start, duration] match vo/vo_chat.wav
msg(0.3,'נועה',voiceNote(1,3.4,'חבר׳ה, מה עושים הערב? אני מתה לצאת.'),{voice:[0.4,3.39]});
msg(3.9,'איתי',voiceNote(2,4.4,'אין כלום. בדקתי בכל מקום, הכול או מלא או מת.'),{voice:[4.0,4.37]});
msg(8.5,'מאיה',voiceNote(3,2.4,'אנחנו רוצים מסיבה, לא עוד ערב על הספה!'),{voice:[8.6,2.36]});
msg(11.1,'נועה',voiceNote(4,2.2,'רגע... תורידו WAWG'),{voice:[11.2,2.15]});
const link=msg(12.1,'נועה',`<div style="width:340px;border-radius:16px;overflow:hidden;background:#140a2a"><img src="logo_card.png" style="width:340px;height:200px;object-fit:cover;display:block"><div style="padding:10px 14px"><div style="font-size:22px;font-weight:700">WAWG · לאן הולכים?</div><div style="font-size:18px;color:#c4b3e6;direction:ltr;text-align:right">wawg.live</div></div></div>`,{typing:false});
const ctap=$(`<div class="tap" style="z-index:70"></div>`);cphone.querySelector('.scr').appendChild(ctap);
msg(21.6,'איתי',voiceNote(5,3.9,'וואו, Neon Bloom הערב! לקחתי כרטיס.')+`<div style="margin-top:10px;width:330px;border-radius:16px;overflow:hidden;background:#fff;color:#1d0b3d;direction:rtl"><div style="height:110px;background:url(img/09_dbd71b1f.webp) center/cover"></div><div style="display:flex;justify-content:space-between;align-items:center;padding:10px 14px"><div><b style="font-size:20px;direction:ltr;display:block;text-align:right">Neon Bloom</b><span style="font-size:16px;color:#6b5a90">כרטיס כניסה · הערב 23:00</span></div><canvas class="mq" width="70" height="70"></canvas></div></div>`,{voice:[21.7,3.83]});
qr(msgs.querySelector('.mq'),99,21);
msg(25.55,'מאיה',`<div style="font-size:30px;font-weight:700">אני בפנים! 🙌</div>`,{voice:[25.6,.68],typing:false});
msg(26.25,'נועה',`<div style="font-size:30px;font-weight:700">גם אני! 💃</div>`,{voice:[26.3,.5],typing:false});
function chatAt(t){
  const on=CHAT_IN.some(([a,b])=>t>=a&&t<b);chatEl.style.display=on?'block':'none';if(!on)return;
  const fi=Math.min(299,Math.floor((t<13.5?t:2.4)*30))+1;cbg.style.backgroundImage=`url(clip/${String(fi).padStart(4,'0')}.jpg)`;
  const seg2=t>=21.5;cphone.style.transform=`scale(${seg2?lerp(1.04,1,eo(P(t,21.5,22))):lerp(.97,1.01,P(t,0,13.5))})`;
  chatEl.style.opacity=seg2?eo(P(t,21.5,21.7)):1;
  for(const m of M){const vis=t>=m.t0;m.el.style.display=vis?'flex':'none';
    if(m.tp)m.tp.style.display=(t>=m.t0-.7&&t<m.t0)?'block':'none';
    if(vis){const k=eo(P(t,m.t0,m.t0+.25));m.el.style.opacity=k;m.el.style.transform=`translateY(${(1-k)*30}px) scale(${lerp(.92,1,k)})`}
    if(m.voice){const p=m.el.querySelector('.wvp');if(p)p.style.width=(cl((t-m.voice[0])/m.voice[1])*100)+'%'}}
  const r=link.querySelector('img').getBoundingClientRect(),s=cphone.querySelector('.scr').getBoundingClientRect(),sc=s.width/540;
  ctap.style.left=((r.left+r.width/2-s.left)/sc)+'px';ctap.style.top=((r.top+r.height/2-s.top)/sc)+'px';tapAnim(ctap,t,13.15);
}
