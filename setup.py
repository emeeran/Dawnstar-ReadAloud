#!/usr/bin/env python3
"""Setup script for deb packaging compatibility."""

from setuptools import setup, find_packages

setup(
    name="dawnstar-readaloud",
    version="1.1.0",
    description="Enhanced Text-to-Speech Application with neural voices",
    author="Dawnstar ReadAloud Contributors",
    packages=find_packages(exclude=["tests*", "trash2review*"]),
    python_requires=">=3.12",
    install_requires=[
        "gtts>=2.5.4",
        "edge-tts>=6.1.9",
        "ebooklib>=0.18",
        "beautifulsoup4>=4.12.0",
        "pyyaml>=6.0",
        "pyperclip>=1.8.2",
        "pypdf>=6.7.1",
    ],
    entry_points={
        "console_scripts": [
            "tts=app:main",
            "ttsd=ttsd.__main__:main",
        ],
    },
    package_data={
        "core": ["py.typed"],
    },
    include_package_data=True,
    zip_safe=False,
)
