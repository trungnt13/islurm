from distutils.core import setup

setup(
    name='pyslurm',
    version='0.1.0',
    author='Nick Artin',
    packages=['pyslurm'],
    scripts=['scripts/slurm'],
    url='https://github.com/trungnt13/pyslurm',
    license='MIT',
    description='Launching SLURM jobs',
    long_description=open('README.rst').read(),
    install_requires=['pyyaml']
)
