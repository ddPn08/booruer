from setuptools import setup

setup(
    name="booruer",
    version="0.0.1",
    description="booru dataset utils",
    author="ddPn08",
    packages=["booruer"],
    install_requires=[
        "fire",
        "requests",
        "tqdm",
        "transformers",
        "pydantic",
        "onnxruntime",
        "numpy",
        "pandas",
        "opencv-contrib-python",

    ],
    entry_points={
        "console_scripts": [
            "booruer=booruer.core:main",
        ]
    },
)