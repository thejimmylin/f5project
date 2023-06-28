import setuptools

from pathlib import Path

base_dir = Path(__file__).parent.resolve()
long_description = (base_dir / "README.md").read_text(encoding="utf-8")

setuptools.setup(
    name="f5project",
    version="0.0.5",
    install_requires=[
        "github-secret-syncer",
    ],
    author="thejimmylin",
    author_email="b00502013@gmail.com",
    description="F5 project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/thejimmylin/f5project",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
