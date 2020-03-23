DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

_export_sizes() {
	NAMEDIFF=$1
	for SIZE in 16 48 96 256 ; do
		mkdir -p $DIR/$SIZE'x'$SIZE
		inkscape -z -e $DIR/$SIZE'x'$SIZE/procris$NAMEDIFF.png -w $SIZE -h $SIZE $DIR/procris$NAMEDIFF.svg 1>/dev/null
		# inkscape -z -e $DIR/$SIZE'x'$SIZE/procris-dark.png -w $SIZE -h $SIZE $DIR/$MODEL.svg
		convert $DIR/$SIZE'x'$SIZE/procris$NAMEDIFF.png -channel RGB -negate $DIR/$SIZE'x'$SIZE/procris$NAMEDIFF-light.png 1>/dev/null
	done
}

_export_sizes ""

for LETTER in "T" "M" "C" "B" ; do
	SVG_NAME_DIFF="-$LETTER"
	LETTER_SVG=$DIR/procris$SVG_NAME_DIFF.svg
	cp $DIR/procris-layout.svg $LETTER_SVG
	sed -i "s/X<\/tspan/$LETTER<\/tspan/" $LETTER_SVG
	_export_sizes $SVG_NAME_DIFF
	rm $LETTER_SVG
done

echo "	SUCESS: directories and icons were generated."
