#!/bin/bash
# duckmix.sh <bed.wav> <vo.wav> <video> <out.mp4> : music bed ducked under the voiceover, -14 LUFS
set -e
ffmpeg -y -loglevel error -i "$1" -i "$2" -i "$3" -filter_complex \
 "[0:a]aresample=48000,aformat=channel_layouts=stereo[bed];[1:a]aresample=48000,aformat=channel_layouts=stereo,volume=1.7,asplit[v1][v2];\
  [bed][v1]sidechaincompress=threshold=0.02:ratio=10:attack=15:release=400:makeup=1[duck];\
  [duck][v2]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,volume=-1.2dB,aresample=48000[a]" \
 -map 2:v -map "[a]" -c:v copy -c:a aac -b:a 192k -movflags +faststart -shortest "$4"
