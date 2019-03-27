from setuptools import find_packages, setup


setup(
    name='Risk Scoring API',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'jsonschema'
    ],
)
