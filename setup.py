"""Publishing package to PyPI

Use this command to "Build & Upload & Cleanup":
```python
python setup.py sdist bdist_wheel && python -m twine upload dist/* && rm -rf dist build *egg-info
```
"""

from setuptools import setup, find_packages

from pathlib import Path

base_dir = Path(__file__).parent.resolve()
long_description = (base_dir / "README.md").read_text(encoding="utf-8")

setup(
    name="f5project",
    version="0.0.24",
    install_requires=[
        "finlab==0.4.5",
        "fugle-trade==0.4.0",
        "python-dotenv==1.0.0",
        "functions-framework==3.4.0",
        "loguru==0.7.0",
        "github-secret-syncer",
    ],
    author="thejimmylin",
    author_email="b00502013@gmail.com",
    description="F5 project",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/thejimmylin/f5project",
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "f5project = f5project.console_scripts:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
)
