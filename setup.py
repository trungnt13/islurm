from distutils.core import setup

setup(
    name='islurm',
    version='0.1.0',
    author='Nick Artin',
    packages=[''],
    scripts=['scripts/platoon-launcher'],
    url='https://github.com/mila-udem/platoon/',
    license='MIT',
    description='Launching task and interactive task for slurm',
    long_description=open('README.rst').read(),
)
