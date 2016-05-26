from distutils.core import setup

setup(
    name='islurm',
    version='0.1.0',
    author='Nick Artin',
    packages=['islurm'],
    scripts=['scripts/pyslurm'],
    url='https://github.com/trungnt13/islurm',
    license='MIT',
    description='Launching SLURM jobs',
    long_description=open('README.rst').read(),
    install_requires=['pyyaml']
)
