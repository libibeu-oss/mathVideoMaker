// ad6: Apple-style 40s spot. Custom layer for black/question cards and real footage; app shots come from ad2.
const CUSTOM=[[0,10],[24,30],[34,36]];
const cx=$(`<div class="fill" style="z-index:205;display:none;background:#000">
  <img class="fx" style="position:absolute;inset:0;width:1080px;height:1920px;object-fit:cover;opacity:0">
  <div class="vig fill" style="background:linear-gradient(180deg,rgba(0,0,0,.35),rgba(0,0,0,0) 30%,rgba(0,0,0,0) 55%,rgba(0,0,0,.75))"></div>
  <div class="q" style="position:absolute;left:0;right:0;top:860px;text-align:center;direction:rtl;font-weight:800;font-size:124px;letter-spacing:-1px;opacity:0">לאן הולכים<span style="color:#ff3fd0">?</span></div>
  <div class="cb" style="position:absolute;right:120px;top:1180px;max-width:640px;padding:30px 40px;border-radius:44px 44px 12px 44px;background:linear-gradient(135deg,#d93fd0,#8a3cff);font-size:56px;font-weight:700;direction:rtl;box-shadow:0 20px 60px rgba(0,0,0,.5);opacity:0">מה עושים הערב?</div>
  <div class="ic" style="position:absolute;left:50%;top:50%;width:300px;height:300px;margin:-150px 0 0 -150px;border-radius:68px;overflow:hidden;opacity:0;box-shadow:0 0 120px rgba(255,63,208,.45)"><img src="logo_card.png" style="width:300px;height:300px;object-fit:cover"></div>
  <div class="sup" style="position:absolute;left:0;right:0;bottom:430px;text-align:center;direction:rtl;font-weight:800;font-size:110px;opacity:0;text-shadow:0 6px 40px rgba(0,0,0,.7)">הערב הזה<span style="color:#ff3fd0">.</span></div>
</div>`);
stage.appendChild(cx);
const fx=cx.querySelector('.fx'),vig=cx.querySelector('.vig'),qq=cx.querySelector('.q'),cb=cx.querySelector('.cb'),ic=cx.querySelector('.ic'),sup=cx.querySelector('.sup');
const ctp=$(`<div class="tap" style="z-index:210"></div>`);cx.appendChild(ctp);ctp.style.left='540px';ctp.style.top='960px';
const fade=(t,a,b,c,d)=>Math.min(eo(P(t,a,b)),1-P(t,c,d));
function customAt(t){
  const on=CUSTOM.some(([a,b])=>t>=a&&t<b);cx.style.display=on?'block':'none';if(!on)return false;
  // footage
  let src=null,o=0,sc=1;
  if(t>=3&&t<7){src=`clip/${String(Math.min(300,Math.floor((t-3)*30)+1)).padStart(4,'0')}.jpg`;o=fade(t,3,3.4,6.6,7);sc=lerp(1.08,1.0,P(t,3,7))}
  else if(t>=24&&t<27){src=`clip2/${String(154+Math.min(41,Math.floor((t-24)*14))).padStart(4,'0')}.jpg`;o=1;sc=lerp(1.0,1.06,P(t,24,27))}
  else if(t>=27&&t<30){src=`clip2/${String(196+Math.min(29,Math.floor((t-27)*10))).padStart(4,'0')}.jpg`;o=1-P(t,29.75,30);sc=lerp(1.04,1.1,P(t,27,30))}
  if(src&&!fx.src.endsWith(src)){fx.src=src;pending.push(fx.decode().catch(()=>{}))}
  fx.style.opacity=src?o:0;fx.style.transform=`scale(${sc})`;vig.style.opacity=src?1:0;
  // the question on black
  const qo=t<3?fade(t,.6,1.4,2.55,2.95):(t>=34?eo(P(t,34.25,34.75)):0);
  qq.style.opacity=qo;qq.style.transform=`translateY(${(1-eo(P(t,t<3?.6:34.25,t<3?1.4:34.75)))*24}px)`;
  const co=fade(t,4.8,5.15,6.5,6.9);cb.style.opacity=co;cb.style.transform=`translateY(${(1-eo(P(t,4.8,5.15)))*40}px) scale(${lerp(.9,1,eo(P(t,4.8,5.15)))})`;
  // app icon: appears, gets tapped, then opens toward the camera
  if(t>=7&&t<10){const a=eo(P(t,7.4,8.0)),z=Math.pow(P(t,9.3,10),2);ic.style.opacity=a*(1-P(t,9.75,10));ic.style.transform=`scale(${lerp(.8,1,a)*(1-.06*Math.sin(P(t,8.8,9.05)*Math.PI))+z*5})`}else ic.style.opacity=0;
  tapAnim(ctp,t,8.85);
  sup.style.opacity=fade(t,27.3,27.7,29.4,29.8);sup.style.transform=`translateY(${(1-eo(P(t,27.3,27.7)))*30}px)`;
  return true;
}
