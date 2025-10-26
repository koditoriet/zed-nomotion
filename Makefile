VERSION := $(shell grep 'Version:' zed-nomotion.spec | awk '{print $$2}')
FEDORA_RELEASE ?= 43
ARCH ?= x86_64

zed-nomotion-$(VERSION)-1.fc$(FEDORA_RELEASE).$(ARCH).rpm: zed-nomotion-$(VERSION)-1.fc$(FEDORA_RELEASE).src.rpm
	fedpkg --release f$(FEDORA_RELEASE) mockbuild --enable-network

zed-nomotion-$(VERSION)-1.fc$(FEDORA_RELEASE).src.rpm: zed-nomotion.spec disable-promotion-hack.patch
	spectool -g zed-nomotion.spec
	fedpkg --release f$(FEDORA_RELEASE) srpm
