mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
current_dir := $(patsubst %/,%,$(dir $(mkfile_path)))
PYTHONPATH=$(current_dir)
SETUP_SCRIPT=${PYTHONPATH}/setup.py
VERSION=$(shell git describe --abbrev=0 --tags $(git rev-list --tags --skip=0 --max-count=1))
LAST_VERSION=$(shell git describe --abbrev=0 --tags $(git rev-list --tags --skip=1 --max-count=1))

.SILENT:
#	cleans any built artifact from the project tree
delete:
	[ -f ${PYTHONPATH}/installed_files.txt ] && rm -f ${PYTHONPATH}/installed_files.txt && echo "	install log - removed" || echo "	OK: no install log"
	[ -f ${PYTHONPATH}/tags ] && rm ${PYTHONPATH}/tags && echo "	tags file - removed" || echo "	OK: no tags file"
	[ -f ${PYTHONPATH}/vimwn-*.tar.gz ] && rm ${PYTHONPATH}/vimwn-*.tar.gz && echo "	build artifact - removed" || echo "	OK: no dist tar"
	[ -d ${PYTHONPATH}/build ] && sudo rm -rf ${PYTHONPATH}/build && echo "	build directory - removed" || echo "	OK: no build dir"
	[ -d ${PYTHONPATH}/deb_dist ] && rm -r ${PYTHONPATH}/deb_dist && echo "	build dependency dirs - removed" || echo "	OK: no dist deb dir"
	[ -d ${PYTHONPATH}/dist ] && rm -r ${PYTHONPATH}/dist && echo "	source package dir - removed" || echo "	OK: no dist dir"
	echo "	OK: package files are gone"
#	installs locally
install: delete
	sudo apt-get install -y python3 gir1.2-gtk-3.0 gir1.2-wnck-3.0 gir1.2-appindicator3-0.1 libwnck-3-0 python3-gi-cairo python3-xdg python3-dbus python3-setproctitle python3-xlib 1>/dev/null
	sudo apt-get install -y python3-distutils 1>/dev/null
	echo "	OK: vimwn dependencies"
	sudo ${SETUP_SCRIPT} install --record $(PYTHONPATH)/installed_files.txt 1>/dev/null
	echo "	OK: vimwn files installed"
	sudo update-icon-caches /usr/share/icons/* 1>/dev/null && echo "	OK: icons cache updated" || echo "	WARN: failed to update icons cache"
	echo "	SUCCESS: vimwn installed"
uninstall:
	sudo cat $(PYTHONPATH)/installed_files.txt | sudo  xargs rm -rf ; rm -f $(PYTHONPATH)/installed_files.txt
#	create .deb so it can be distributed manually
binaries: delete
	$(info Packing binaries for version ${VERSION}, after: ${LAST_VERSION})
	python3 ${SETUP_SCRIPT} --command-packages=stdeb.command bdist_deb 1>/dev/null && echo "Binaries packaged"
#	assemble source files in a .tar.gz so it can be uploaded to a repository
sources: delete
	$(info Packing version ${VERSION}, after: ${LAST_VERSION})
	sudo apt-get install python3-distutils python3-stdeb -y 1>/dev/null
	python3 ${SETUP_SCRIPT} --command-packages=stdeb.command sdist_dsc --forced-upstream-version ${VERSION} 1>/dev/null
	echo "New version is built"
	CHANGES=$$(git log develop --oneline  --reverse --not ${LAST_VERSION}) \
	&& echo "$$CHANGES" >> deb_dist/vimwn_${VERSION}-1_source.changes
	echo "	SUCCESS: changes file is up to date, the package is ready to be signed/published"
#	publishes the sources package to pedrosans Ubuntu PPA
publish:
	sudo apt-get install devscripts gnupg2 -y 1>/dev/null
	debsign -pgpg2 ${PYTHONPATH}/deb_dist/vimwn_${VERSION}-1_source.changes && echo "Signed"
	cd ${PYTHONPATH}/deb_dist && dput ppa:pedrosans/vimwn vimwn_${VERSION}-1_source.changes && echo "Published"
