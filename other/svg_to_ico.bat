magick convert -size 16x16 -background transparent -depth 8 icon.svg tmp/16.png
magick convert -size 24x24 -background transparent -depth 8 icon.svg tmp/24.png
magick convert -size 32x32 -background transparent -depth 8 icon.svg tmp/32.png
magick convert -size 48x48 -background transparent -depth 8 icon.svg tmp/48.png
magick convert -size 64x64 -background transparent -depth 8 icon.svg tmp/64.png
magick convert -size 96x96 -background transparent -depth 8 icon.svg tmp/96.png
magick convert -size 128x128 -background transparent -depth 8 icon.svg tmp/128.png
magick convert -size 256x256 -background transparent -depth 8 icon.svg tmp/256.png
magick convert tmp/16.png tmp/24.png tmp/32.png tmp/48.png tmp/64.png tmp/96.png tmp/128.png tmp/256.png logo.ico