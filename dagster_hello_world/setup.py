from setuptools import find_packages, setup

setup(
    name="dagster_hello_world",
    packages=find_packages(exclude=["dagster_hello_world_tests"]),
    install_requires=[
        "dagster",
        "dagster-cloud"
    ],
    extras_require={"dev": ["dagit", "pytest"]},
)
