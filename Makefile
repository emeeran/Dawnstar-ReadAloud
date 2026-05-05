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
	cat debian/control $(BUILD_DIR)/DEBIAN/
	cp debian/conffiles $(BUILD_DIR)/DEBIAN/
	cp debian/postinst $(BUILD_DIR)/DEBIAN/
	chmod 755 $(BUILD_DIR)/DEBIAN/postinst
	cp debian/prerm $(BUILD_DIR)/DEBIAN/
	chmod 755 $(BUILD_DIR)/DEBIAN/prerm
