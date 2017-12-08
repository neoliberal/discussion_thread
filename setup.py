"""setup"""
from typing import List

from setuptools import setup, find_packages

with open("requirements.txt") as file:
    requirements: List[str] = file.read().splitlines()

setup(
    name="discussion_thread",
    description="Manages the daily discussion thread on /r/neoliberal",
    version="1.0.0",
    python_requires='>=3',
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "start_discussion_thread = discussion_thread.service:main"
        ]
    },
    include_package_data=True,
    packages=find_packages(),
    package_dir={"": "discussion_thread"},
    package_data={
        "discussion_thread": ["data/*.env", "data/*.service"]
    },
    # metadata
    author="Abhi Agarwal",
    author_email="abhi@neoliber.al",
    url="https://github.com/neoliberal/discussion_thread",
    license="MIT",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: No Input/Output (Daemon)",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    keywords="reddit neoliberal discussion_thread",
)
