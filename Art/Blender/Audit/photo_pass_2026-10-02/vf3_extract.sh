#!/bin/bash
# 3 fps frames offset by 1/6 s from the old ~1 fps keyframes (never the same instants), long side <= 1920 px.
S=$1; OUT=$S/vf3; mkdir -p $OUT
: > $OUT/manifest.tsv
while read -r v; do
  stem=$(basename "$v" .mp4); base=${stem%_4k30}
  src="$S/refv/$v"
  alt=$(ls $S/refv2/*${base#*_PXL_}*_1080.mp4 $S/refv2/*${base}*_1080.mp4 2>/dev/null | head -1)
  case "$stem" in *_4k30) [ -n "$alt" ] && src="$alt";; esac
  d=$OUT/$base; mkdir -p "$d"
  nice -n 10 ffmpeg -nostdin -v error -threads 2 -ss 0.1667 -i "$src" -vf "fps=3,scale='if(gt(iw,ih),min(1920,iw),-2)':'if(gt(iw,ih),-2,min(1920,ih))'" -q:v 3 "$d/f_%04d.jpg" -y
  n=$(ls "$d" | wc -l)
  printf "%s\t%s\t%s\n" "$base" "$n" "$src" >> $OUT/manifest.tsv
  echo "$base $n"
done < $S/video_all.txt
echo VF3DONE
