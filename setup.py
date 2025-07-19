from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="fp-mqtt-broker",
    version="0.1.0",
    packages=find_packages(),
    author="Rodrigo",
    author_email="rodser4@gmail.com",
    description="A flexible MQTT broker package for IoT services with optional message handlers",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "paho-mqtt>=1.6.1",
    ],
    extras_require={
        "dev": [
            "pytest>=8.4.1",
            "pytest-mock>=3.14.1", 
            "coverage>=7.9.1",
            "pytest-cov>=6.2.1"
        ]
    },
    python_requires=">=3.8"
)