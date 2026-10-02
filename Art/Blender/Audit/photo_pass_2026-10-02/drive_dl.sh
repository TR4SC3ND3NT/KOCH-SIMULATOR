#!/bin/bash
# Downloads the 12 re-encoded videos from the owner's shared Drive folder (public link).
D=$1
while read -r id name; do
  [ -s "$D/$name" ] && continue
  for i in 1 2 3; do
    curl -sSL --fail -o "$D/$name.part" "https://drive.usercontent.google.com/download?id=$id&export=download&confirm=t" && mv "$D/$name.part" "$D/$name" && break
    sleep $((i*5))
  done
  echo "done $name $(stat -c %s "$D/$name" 2>/dev/null)"
done <<'LIST'
1Vwh7L-xhWkS38qrK72Xz53pV9EfwpREk PXL_20260924_074805359_1080.mp4
1xkKPPREYUcEFxhQyjE1qLARdf8qKCCkA PXL_20260924_070704360_1080.mp4
1cqleeK4wN9dz6UHMvwOMAnANjQfgnY2g PXL_20260925_012327726_1080.mp4
1_2vEwhuTpU8eG7dyLkxJMgsSE2mPtFx9 006_PXL_20261001_041821243_1080.mp4
1TAai0s879iOtXQj1U516SpgwBHjGObT0 PXL_20260925_012547860_1080.mp4
1_AJxtPL29WUvH-3PBmEqBOxSoI518Fc1 PXL_20260924_070309303_1080.mp4
1HCZjSDtR20zCMCINCQOf_5w_thtKqoFM PXL_20260924_070410255_1080.mp4
1BbkWcFDiS876V8sMHSMBhLkhqgfKHDqZ 250_PXL_20260930_112953497_1080.mp4
15ptjD0PZOB3cteaJ4XyLGFaoDJs9Qt9u PXL_20260924_061757320_1080.mp4
1CWSDmOzsroh2lkD4Xs6egBaPBuNzez-F PXL_20260922_150544065_1080.mp4
1VGq0Vgi8esDAO7oxL74BerBmtD0OnBj1 PXL_20260924_065653194_1080.mp4
1PNg9HZy6FTW1FpV-OsAD4nEkhH07kUjd PXL_20260922_145101161_1080.mp4
LIST
echo ALLDONE
