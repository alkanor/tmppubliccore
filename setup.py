from setuptools import setup, find_packages


setup(
    name="core",
    version="0.0.1",
    author="Alka",
    description=("Some core package for future"),
    license="MIT",
    #packages=['core'],
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
    ],
)
