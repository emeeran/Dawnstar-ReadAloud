#!/usr/bin/make -f
# Simple Makefile for building .deb package manually

SHELL := /bin/bash
VERSION ?= 1.1.0
ARCH ?= $(shell dpkg --print-architecture)
PKG_NAME = dawnstar-readaloud_$(VERSION)_all
BUILD_DIR = build/$(PKG_NAME)

.PHONY: all clean package install

all: package

clean:
	rm -rf build

package: clean
	@echo "Building $(PKG_NAME)..."
	mkdir -p $(BUILD_DIR)/DEBIAN
	mkdir -p $(BUILD_DIR)/usr/bin
	mkdir -p $(BUILD_DIR)/usr/lib/systemd/user
	mkdir -p $(BUILD_DIR)/usr/share/doc/$(PKG_NAME)
	mkdir -p $(BUILD_DIR)/usr/share/man/man1
	mkdir -p $(BUILD_DIR)/usr/share/$(PKG_NAME)
	mkdir -p $(BUILD_DIR)/usr/lib/$(PKG_NAME)/core
	mkdir -p $(BUILD_DIR)/usr/lib/$(PKG_NAME)/ttsd
	# Copy DEBIAN control files
	cp debian/control $(BUILD_DIR)/DEBIAN/
	cp debian/conffiles $(BUILD_DIR)/DEBIAN/
	cp debian/postinst $(BUILD_DIR)/DEBIAN/
	chmod 755 $(BUILD_DIR)/DEBIAN/postinst
	cp debian/prerm $(BUILD_DIR)/DEBIAN/
	chmod 755 $(BUILD_DIR)/DEBIAN/prerm
	# Copy executable scripts
	cp tts $(BUILD_DIR)/usr/bin/
	cp ttsc $(BUILD_DIR)/usr/bin/
	cp speak_from_cursor.sh $(BUILD_DIR)/usr/bin/tts-speak
	cp stop_speaking.sh $(BUILD_DIR)/usr/bin/tts-stop
	chmod 755 $(BUILD_DIR)/usr/bin/*
	# Copy systemd service
	cp systemd/tts-daemon.service $(BUILD_DIR)/usr/lib/systemd/user/
	# Copy man pages
	cp tts.1 ttsc.1 ttsd.1 $(BUILD_DIR)/usr/share/man/man1/
	# Copy documentation
	cp README.md $(BUILD_DIR)/usr/share/doc/$(PKG_NAME)/
	cp USER_MANUAL.md $(BUILD_DIR)/usr/share/doc/$(PKG_NAME)/
	# Copy Python package
	cp app.py config.py configure.py $(BUILD_DIR)/usr/lib/$(PKG_NAME)/
	cp -r core $(BUILD_DIR)/usr/lib/$(PKG_NAME)/
	cp -r ttsd $(BUILD_DIR)/usr/lib/$(PKG_NAME)/
	# Build the deb package
	fakeroot dpkg-deb --build $(BUILD_DIR) $(BUILD_DIR).deb
	@echo "Package created: $(BUILD_DIR).deb"

install: package
	@echo "Installing $(PKG_NAME)..."
	sudo dpkg -i build/$(PKG_NAME).deb
