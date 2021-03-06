mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(patsubst %/,%,$(dir $(mkfile_path)))
PYTHONPATH=$(current_dir)
SETUP_SCRIPT=${PYTHONPATH}/setup.py
VERSION=$(shell git describe --abbrev=0 --tags $(git rev-list --tags --skip=0 --max-count=1))
LAST_VERSION=$(shell git describe --abbrev=0 --tags $(git rev-list --tags --skip=1 --max-count=1))

.SILENT:
#	cleans any built artifact from the project tree
clean:
	[ -f ${PYTHONPATH}/installed_files.txt ] && rm -f ${PYTHONPATH}/installed_files.txt && echo "	install log - removed" || echo "	OK: no install log"
	[ -f ${PYTHONPATH}/tags ] && rm ${PYTHONPATH}/tags && echo "	tags file - removed" || echo "	OK: no tags file"
	[ -f ${PYTHONPATH}/pocoy-*.tar.gz ] && rm ${PYTHONPATH}/pocoy-*.tar.gz && echo "	build artifact - removed" || echo "	OK: no dist tar"
	[ -f ${PYTHONPATH}/MANIFEST ] && rm ${PYTHONPATH}/MANIFEST && echo "	MANIFEST - removed" || echo "	OK: no MANIFEST"
	[ -d ${PYTHONPATH}/build ] && rm -rf ${PYTHONPATH}/build && echo "	build directory - removed" || echo "	OK: no build dir"
	[ -d ${PYTHONPATH}/deb_dist ] && rm -r ${PYTHONPATH}/deb_dist && echo "	build dependency dirs - removed" || echo "	OK: no dist deb dir"
	[ -d ${PYTHONPATH}/dist ] && rm -r ${PYTHONPATH}/dist && echo "	source package dir - removed" || echo "	OK: no dist dir"
	echo "	OK: package files are gone"
#	install locally
manual:
	sed "s/VERSION/$(VERSION)/" pocoy.1 > pocoy.1~
	gzip -c pocoy.1~ > data/pocoy.1.gz
	rm pocoy.1~
	echo "	OK: documentation updated and compressed to pocoy.1.gz"
test:
	python3 -m unittest discover -v
install:
	python3 ${SETUP_SCRIPT} install --record $(PYTHONPATH)/installed_files.txt 1>/dev/null
	echo "	OK: pocoy files installed"
	(command -v gtk-update-icon-cache && gtk-update-icon-cache -f --include-image-data /usr/share/icons/hicolor ) || echo 'skiping icon update'
	echo "	SUCCESS: pocoy installed"
uninstall:
	cat $(PYTHONPATH)/installed_files.txt | xargs rm -rf ; rm -f $(PYTHONPATH)/installed_files.txt
#	create .deb so it can be distributed manually
binaries:
	$(info Packing binaries for version ${VERSION}, after: ${LAST_VERSION})
	python3 ${SETUP_SCRIPT} --command-packages=stdeb.command bdist_deb 1>/dev/null && echo "Binaries packaged"
#	assemble source files in a .tar.gz so it can be uploaded to a repository
sources:
	$(info Packing version ${VERSION}, after: ${LAST_VERSION})
	python3 ${SETUP_SCRIPT} --command-packages=stdeb.command sdist_dsc --forced-upstream-version ${VERSION} 1>/dev/null
	echo "New version is built"
	CHANGES=$$(git log develop --oneline  --reverse --not ${LAST_VERSION}) \
	&& echo "$$CHANGES" >> deb_dist/pocoy_${VERSION}-1_source.changes
	echo "	SUCCESS: changes file is up to date, the package is ready to be signed/published"
#	publishes the sources package to pedrosans Ubuntu PPA
publish:
	debsign -pgpg2 ${PYTHONPATH}/deb_dist/pocoy_${VERSION}-1_source.changes && echo "Signed"
	cd ${PYTHONPATH}/deb_dist && dput ppa:pedrosans/pocoy pocoy_${VERSION}-1_source.changes && echo "Published"
dependencies:
	# arch
	(command -v pacman  && pacman -S libwnck3 gobject-introspection-runtime libappindicator-gtk3 python-pyxdg python-dbus python-setproctitle python-xlib libx11) || echo 'skiping arch setup'
	# binaries / sources
	(command -v apt-get && apt-get install python3-distutils python3-stdeb -y 1>/dev/null) || echo 'skiping deb setup'
	# install
	(command -v apt-get && apt-get install -y gir1.2-gtk-3.0 gir1.2-wnck-3.0 gir1.2-appindicator3-0.1 gir1.2-notify-0.7 python3-xdg python3-dbus python3-setproctitle python3-xlib libx11-6 1>/dev/null) || echo 'skiping deb setup'
	# publish
	(command -v apt-get && apt-get install devscripts gnupg2 -y 1>/dev/null) || echo 'skiping deb setup'
	echo "	OK: pocoy dependencies"
