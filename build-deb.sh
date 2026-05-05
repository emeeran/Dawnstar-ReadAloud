#!/bin/bash
# Build .deb package for Dawnstar ReadAloud
set -e

PKG_NAME="dawnstar-readaloud"
VERSION="1.1.0"
ARCH=$(dpkg --print-architecture)
BUILD_DIR="build"
DEST="$BUILD_DIR/$PKG_NAME-$VERSION-$ARCH"
OUTPUT_FILE="${PKG_NAME}_${VERSION}_${ARCH}.deb"

# Clean previous build
rm -rf "$BUILD_DIR"

# Create build structure
mkdir -p "$DEST/DEBIAN"
mkdir -p "$DEST/usr/bin"
mkdir -p "$DEST/usr/lib/systemd/user"
mkdir -p "$DEST/usr/share/doc/$PKG_NAME"
mkdir -p "$DEST/usr/share/man/man1"
mkdir -p "$DEST/usr/lib/$PKG_NAME/core"
mkdir -p "$DEST/usr/lib/$PKG_NAME/ttsd"
mkdir -p "$DEST/usr/share/applications"

# Copy DEBIAN control files
cp debian/control "$DEST/DEBIAN/"
cp debian/conffiles "$DEST/DEBIAN/"
cp debian/postinst "$DEST/DEBIAN/"
chmod 755 "$DEST/DEBIAN/postinst"
cp debian/prerm "$DEST/DEBIAN/"
chmod 755 "$DEST/DEBIAN/prerm"

# Copy executable scripts
cp tts "$DEST/usr/bin/"
cp ttsc "$DEST/usr/bin/"
cp speak_from_cursor.sh "$DEST/usr/bin/tts-speak"
cp stop_speaking.sh "$DEST/usr/bin/tts-stop"
chmod 755 "$DEST/usr/bin/"*

# Copy systemd service
cp systemd/tts-daemon.service "$DEST/usr/lib/systemd/user/"

# Copy man pages
cp tts.1 "$DEST/usr/share/man/man1/"
cp ttsc.1 "$DEST/usr/share/man/man1/"
cp ttsd.1 "$DEST/usr/share/man/man1/"

# Copy documentation
cp README.md "$DEST/usr/share/doc/$PKG_NAME/"
cp USER_MANUAL.md "$DEST/usr/share/doc/$PKG_NAME/"

# Copy Python package
cp app.py config.py configure.py "$DEST/usr/lib/$PKG_NAME/"
cp -r core "$DEST/usr/lib/$PKG_NAME/"
cp -r ttsd "$DEST/usr/lib/$PKG_NAME/"

# Build the deb package
echo "Building $OUTPUT_FILE..."
fakeroot dpkg-deb --build "$DEST" "$OUTPUT_FILE"

echo "Package built successfully: $OUTPUT_FILE"
echo "Install with: sudo dpkg -i $OUTPUT_FILE"
