DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

_export_sizes() {
	NAMEDIFF=$1
	for SIZE in 16 48 256 ; do
		inkscape -z -e $DIR/$SIZE'x'$SIZE/poco$NAMEDIFF.png -w $SIZE -h $SIZE $DIR/poco$NAMEDIFF.svg
		# inkscape -z -e $DIR/$SIZE'x'$SIZE/poco-dark.png -w $SIZE -h $SIZE $DIR/$MODEL.svg
		convert $DIR/$SIZE'x'$SIZE/poco$NAMEDIFF.png -channel RGB -negate $DIR/$SIZE'x'$SIZE/poco$NAMEDIFF-light.png
	done
}

_export_sizes ""

for LETTER in "T" "C" "M" ; do
	SVG_NAME_DIFF="-$LETTER"
	LETTER_SVG=$DIR/poco$SVG_NAME_DIFF.svg
	cp $DIR/poco-layout.svg $LETTER_SVG
	sed -i "s/X<\/tspan/$LETTER<\/tspan/" $LETTER_SVG
	_export_sizes $SVG_NAME_DIFF
	rm $LETTER_SVG
done

sudo update-icon-caches /usr/share/icons/*
