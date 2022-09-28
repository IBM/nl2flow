from setuptools import setup

VERSION = "0.0.1"
NAME = "nl2flow"
DESCRIPTION = "A PDDL interface to flow construction."
KEYWORDS = ["natural language", "automated planning"]
CLASSIFIERS = ["Intended Audience :: Science/Research"]

with open("requirements.txt", "r", encoding="utf-8") as f:
    DEPENDENCIES = f.read().strip().split("\n")

with open("requirements_dev.txt", "r", encoding="utf-8") as f:
    DEV_DEPENDENCIES = f.read().strip().split("\n")

with open("README.md", "r", encoding="utf-8") as f:
    LONG_DESCRIPTION = f.read()

setup(
    name=NAME,
    version=VERSION,
    author="Tathagata Chakraborti",
    author_email="tchakra2@ibm.com",
    license="MIT",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    keywords=KEYWORDS,
    url="https://github.ibm.com/aicl/nl2flow",
    classifiers=CLASSIFIERS,
    python_requires=">=3.7",
    install_requires=DEPENDENCIES,
    extras_require={"dev": DEV_DEPENDENCIES},
)
