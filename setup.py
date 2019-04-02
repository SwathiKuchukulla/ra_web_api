from setuptools import find_packages, setup


setup(
    name='Risk Adjustment Scoring API',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'jsonschema',
        'httpie',
        'ldap3'
    ],
)
