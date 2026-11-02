import json,numpy as np
from scipy.io import wavfile
SR=48000;N=31*SR
def ld(p):
    sr,x=wavfile.read(p);x=x.astype(np.float32)/32768
    if x.ndim==1:x=np.stack([x,x],1)
    return x
m=ld('a/music.wav')[:N];m=np.pad(m,((0,N-len(m)),(0,0)))
t=np.arange(N)/SR
m*=np.minimum(1,t/.3)[:,None]*np.clip((31-t)/1.4,0,1)[:,None]
vo=np.zeros((N,2),np.float32);spans=[]
for k,t0 in []:
    v=ld(f'vo/{k}.wav');i=int(t0*SR);vo[i:i+len(v)]+=v;spans.append((t0,t0+len(v)/SR))
# duck envelope
g=np.ones(N,np.float32)
for a,b in spans:
    g[int((a-.12)*SR):int((b+.1)*SR)]=0
from scipy.ndimage import uniform_filter1d
g=uniform_filter1d(g,int(.15*SR))
duck=np.where(t<14.9,10**(-15/20),10**(-19.5/20)).astype(np.float32);mg=duck+(1-duck)*g
s=np.zeros((N,2),np.float32)
MAP={'pop':('ui-popup-dry',.5),'tick':('ui-tone-quick',.35),'vanish':('pop-electric',.35),'msg':('ui-message-pop',.5),'stamp':('hit-weak',.9),
     'drop':('bass-hit-futuristic',.9),'swoosh':('swoosh-quick',.6),'boom':('impact-cine-big',.55),'chime':('chime-crystal',.45),'slam':('bass-hit-short',.7),'tap':('switch-tap',.5)}
def put(x,t0,gain):
    i=int(t0*SR);x=x[:N-i];s[i:i+len(x)]+=x*gain
for e in json.load(open('a/sfx11.json')):
    if e['name'] in MAP:f,gg=MAP[e['name']];put(ld(f'a/{f}.wav'),e['t'],gg*e['g'])
put(ld('a/impact-cine-big.wav'),15.0,.35)
rng=np.random.default_rng(1)
# synthetic riser 13.0-15.0: filtered noise sweep up + rising tone
n=int(2*SR);tl=np.arange(n)/SR;nz=rng.standard_normal(n)
from scipy.signal import butter,sosfilt
out=np.zeros(n)
for j in range(20):
    a,b=j*n//20,(j+1)*n//20;fc=400+j*300
    out[a:b]=sosfilt(butter(2,[fc,fc*1.6],'band',fs=SR,output='sos'),nz)[a:b]
tone=np.sin(2*np.pi*np.cumsum(200+tl*500)/SR)*.25
r=(out*.6+tone)*(tl/2)**2*.5;put(np.stack([r,r],1),13.0,1)
# synthetic fall 9.75: descending whoosh
n=int(.9*SR);tl=np.arange(n)/SR;nz=rng.standard_normal(n)
fw=sosfilt(butter(2,900,'low',fs=SR,output='sos'),nz)*np.sin(np.pi*tl/.9)**2*.5
fw+=np.sin(2*np.pi*np.cumsum(500-tl*420)/SR)*np.exp(-tl*3)*.2

music=m*.7
mix=music+vo*1.0+s*.8
# report voice vs music during speech
for a,b in spans:
    i,j=int(a*SR),int(b*SR);rv=np.sqrt((vo[i:j]**2).mean());rm=np.sqrt((music[i:j]**2).mean())
    print(f'{a:5.1f} voice-music {20*np.log10(rv/rm):.1f} dB')
wavfile.write('a/mix11.wav',SR,(np.clip(mix,-1,1)*32767).astype(np.int16))
