#!/bin/bash
set -e
S=$(dirname "$0"); O=/home/user/wawg; mkdir -p $O
# 40s master: music + UI sfx, normalized to -14 LUFS for social
ffmpeg -y -loglevel error -i $S/video_40.mp4 -i $S/music.wav -i $S/sfx.wav -filter_complex \
 "[1:a]volume=1.0[m];[2:a]volume=0.8[s];[m][s]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,volume=-1.4dB,aresample=48000[a]" \
 -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -movflags +faststart -t 40 $O/WAWG_ad_v2_40s.mp4
# 15s cut: artists (12-15.5), ticket+payment (16-20.5), discounts (21-24), finale (36-40)
ffmpeg -y -loglevel error -i $O/WAWG_ad_v2_40s.mp4 -filter_complex \
 "[0:v]trim=12:15.5,setpts=PTS-STARTPTS[v1];[0:a]atrim=12:15.5,asetpts=PTS-STARTPTS,afade=t=out:st=3.47:d=0.03[a1];\
  [0:v]trim=16:20.5,setpts=PTS-STARTPTS[v2];[0:a]atrim=16:20.5,asetpts=PTS-STARTPTS,afade=t=out:st=4.47:d=0.03[a2];\
  [0:v]trim=21:24,setpts=PTS-STARTPTS[v3];[0:a]atrim=21:24,asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st=2.97:d=0.03[a3];\
  [0:v]trim=36:40,setpts=PTS-STARTPTS[v4];[0:a]atrim=36:40,asetpts=PTS-STARTPTS,afade=t=in:d=0.02[a4];\
  [v1][a1][v2][a2][v3][a3][v4][a4]concat=n=4:v=1:a=1[v][a]" \
 -map "[v]" -map "[a]" -c:v libx264 -crf 18 -preset medium -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart $O/WAWG_ad_v2_15s.mp4
ls -la $O
