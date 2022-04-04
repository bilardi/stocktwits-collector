import setuptools
import stocktwits_collector

setuptools.setup(
    name="stocktwits-collector",
    version=stocktwits_collector.__version__,
    author=stocktwits_collector.__author__,
    author_email="alessandra.bilardi@gmail.com",
    description="Stocktwits collector Python package",
    long_description=open('README.rst').read(),
    long_description_content_type="text/x-rst",
    url="https://stocktwits-collector.readthedocs.io/",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    project_urls={
        "Source":"https://github.com/bilardi/stocktwits-collector",
        "Bug Reports":"https://github.com/bilardi/stocktwits-collector/issues",
        "Funding":"https://donate.pypi.org",
    },
)
