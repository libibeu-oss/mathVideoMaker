const {chromium}=require('playwright');const {spawn}=require('child_process');const path=require('path');
(async()=>{
  const [,,html,mode,out,...ts]=process.argv;
  const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
  p.on('pageerror',e=>console.error('PAGEERR',e.message));p.on('console',m=>{if(m.type()==='error')console.error('CONSOLE',m.text())});
  await p.goto('file://'+path.resolve(html));await p.evaluate(()=>window.READY);
  if(mode==='stills'){for(const t of ts){await p.evaluate(t=>R(t),+t);await p.screenshot({path:`${out}/f_${t}.jpg`,type:'jpeg',quality:85})}}
  else{const fps=30,dur=+ts[0];const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate',''+fps,'-c:v','mjpeg','-i','-','-c:v','libx264','-preset','medium','-crf','17','-pix_fmt','yuv420p',out],{stdio:['pipe','inherit','inherit']});
    const st=+(ts[1]||0);for(let i=0;i<dur*fps;i++){await p.evaluate(t=>R(t),st+i/fps);const buf=await p.screenshot({type:'jpeg',quality:93});if(!ff.stdin.write(buf))await new Promise(r=>ff.stdin.once('drain',r));if(i%150===0)console.log('frame',i)}
    ff.stdin.end();await new Promise(r=>ff.on('close',r))}
  await b.close()})();
