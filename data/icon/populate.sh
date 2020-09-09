DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

_export_sizes() {
	NAMEDIFF=$1
	for SIZE in 16 48 96 256 ; do

		SCALED_DIR=$DIR/$SIZE'x'$SIZE
		SCALED_PNG=$SCALED_DIR/pocoy$NAMEDIFF-dark.png
		LIGHT_PNG=$SCALED_DIR/pocoy$NAMEDIFF-light.png
		RED_PNG=$SCALED_DIR/pocoy$NAMEDIFF-red.png

		mkdir -p $SCALED_DIR
		inkscape -z -e $SCALED_PNG -w $SIZE -h $SIZE $DIR/pocoy$NAMEDIFF.svg 1>/dev/null
		convert $SCALED_PNG -channel RGB -negate $LIGHT_PNG 1>/dev/null
		convert $SCALED_PNG -fuzz 95% -fill red -opaque 'rgb(125,125,125)' $RED_PNG

	done
}

_escape_xml() {
	echo "$1"| sed 's/\\/\\\\/' | sed 's/</\\\&lt;/' | sed 's/>/\\\&gt;/'
}

_export_sizes ""

for LETTER in 'M' 'T' 'C' '<' '>' '@' '\'; do
	ESCAPED_LETTER=$(_escape_xml $LETTER)
	SVG_NAME_DIFF="-$LETTER"
	LETTER_SVG=$DIR/pocoy$SVG_NAME_DIFF.svg
	cp $DIR/pocoy-layout.svg $LETTER_SVG
	sed -i "s/X<\/tspan/$ESCAPED_LETTER<\/tspan/" $LETTER_SVG
	_export_sizes $SVG_NAME_DIFF
	rm $LETTER_SVG
done

echo "	SUCESS: directories and icons were generated."
