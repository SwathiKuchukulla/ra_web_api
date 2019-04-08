from setuptools import find_packages, setup


setup(
    name='Risk Adjustment Scoring API',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'flask',
        'rascore@git+https://github.com/SwathiKuchukulla/ra_score.git',
        'jsonschema',
        'httpie',
        'ldap3'
    ],
)
