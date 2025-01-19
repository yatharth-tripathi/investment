from setuptools import setup, find_packages                                                                                                                                                                                                                                                                                               
setup(                                                                                                                                                                          
    name="rsfc_core_dsls",
    version="0.1.0",
    packages=find_packages(),
    package_dir={
        "": "simulation",
        "": "core"
    },
    include_package_data=True,
    author="Torbellino Tech SL",
    author_email="juan.diez@torbellino.tech",
    description="",
    long_description=open("docs/README.md").read(),
    long_description_content_type="text/markdown",
    url="https://www.torbellino.tech/",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Copyright Torbellino Tech SL",
    ]
)