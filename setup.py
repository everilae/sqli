from setuptools import setup

setup(
    name="sqli",
    version="0.1",
    description="Simple SQL injection checker",
    author="Ilja Everilä",
    author_email="saarni@gmail.com",
    url="https://github.com/everilae/sqli",
    packages=["sqli"],
    requires=[
        "astunparse",
        "requests",
    ],
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
    scripts=["scripts/so-checker.py"],
)
