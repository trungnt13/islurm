from __future__ import print_function, division

import os
import math


# ======================================================================
# Const
# ======================================================================
CONFIGURE_PATH = os.path.join(os.path.expanduser('~'),
                              '.islurm')
MODULES = []
SCRIPTS = []
EMAIL = None
LOGPATH = '.'
OPTIONS = []
if os.path.exists(CONFIGURE_PATH):
    from StringIO import StringIO
    from yaml import load
    config = load(StringIO(open(CONFIGURE_PATH, 'r').read().lower()))
    if config is not None:
        if 'modules' in config or 'module' in config:
            MODULES = config['modules'] if 'modules' in config else config['module']
            MODULES = MODULES if isinstance(MODULES, (tuple, list)) else [MODULES]
        if 'scripts' in config or 'script' in config:
            SCRIPTS = config['scripts'] if 'scripts' in config else config['script']
            SCRIPTS = SCRIPTS if isinstance(SCRIPTS, (tuple, list)) else [SCRIPTS]
        if 'email' in config or 'emails' in config:
            EMAIL = config['email'] if 'email' in config else config['emails']
            EMAIL = str(EMAIL)
        if 'log' in config:
            LOGPATH = str(config['log'])
        if 'option' in config or 'options' in config:
            OPTIONS = config['option'] if 'option' in config else config['options']
            OPTIONS = OPTIONS if isinstance(OPTIONS, (tuple, list)) else [OPTIONS]

#SBATCH --exclusive
#SBATCH --constraint=snb|hsw
#SBATCH --constraint=k40|k80

#####################################
# Paramters: arch (gpu, gpulong, gputest), hour, minute, delay,
# task_name, log_path, log_path, n_node, mem, n_gpu, email,
# addition_options, modules, scripts, command
_GPU_SLURM = \
"""#!/bin/bash
# author: trungnt
#SBATCH -p %s
#SBATCH -t %02d:%02d:00
#SBATCH --begin=now+%dminute
#SBATCH -J %s
#SBATCH -o %s
#SBATCH -e %s
#SBATCH --nodes=%d
%s
%s
%s
%s
#SBATCH

module purge
%s
%s

# run your script
%s
"""


# ======================================================================
# Interactive
# ======================================================================
#srun -N 1 -p gputest -t 15 --gres=gpu:2 --exclusive --pty $SHELL -l
def irun(d=30, n=1, mem=15000):
    arch = 'gpu'
    if d <= 15:
        arch = 'gputest'
    elif d > 4320:
        arch = 'gpulong'
        mem = int(min(mem, 20000))

    maximum_gpu_per_node = 2
    for i in OPTIONS:
        if 'k80' in i:
            maximum_gpu_per_node = 4
    n_node = int(math.ceil(n / maximum_gpu_per_node))
    if n > maximum_gpu_per_node:
        n = maximum_gpu_per_node

    options = ' '.join([str(i) for i in OPTIONS])
    command = 'srun -N %d -p %s -t %d --gres=gpu:%d --mem=%d %s --pty $SHELL -l' % \
    (n_node, arch, d, n, mem, options)
    try:
        print(command)
        os.system(command)
    except:
        print('Failed to execute iteractive SLURM session.')


# ======================================================================
# SLURM creator
# ======================================================================
def run_slurm(slurm):
    if os.path.exists(slurm) and os.path.isfile(slurm):
        try:
            os.system('cat ' + slurm)
            os.system('sbatch ' + slurm)
        except:
            print('Failed to execute slurm!')
    else:
        name = 'tmp_slurm_file_with_long_name_that_cannot_exist.slurm'
        f = open(name, 'w'); f.write(slurm); f.close()
        try:
            os.system('cat ' + name)
            os.system('sbatch ' + name)
        except:
            print('Failed to execute slurm!')
        os.remove(name)


def cancel_all(username):
    ''' only work on UNIX '''
    import commands
    command = "squeue | grep -v 'grep' | grep %s | awk '{print $1}'" % username
    status, output = commands.getstatusoutput(command)
    if len(output) > 0:
        output = output.split('\n')
        os.system('scancel ' + ' '.join(output))


def create_slurm(name, duration, delay, command, nprocess=1, mem=15000,
    log_path=None, email=None, options=None, modules=None, scripts=None,
    machine='gpu'):
    """
    duration : int
        in minutes
    delay : int
        in minutes
    command : str
        main command to be executed by slurm
    nprocess : int
        number of gpu used
    mem : int
        number of MB of RAM, total memory for all cpu (in case of MPI)
    log_path : str (dir or file)
        path to save log file
    email : str
        email address to report task status
    options : str
        additional configuration for slurm task (e.g. --exclusive)
    modules : str or list(str)
        "module purge" will be executed in beginning, then "module load"
        for all given modules name (e.g ["cuda/7.5", "gcc/4.9.1"])
    scripts : str
        pre-executed scripts (e.g source activate ai)
    machine : 'gpu', 'serial', 'hugemem', 'parallel'
        architecture used for the job

    Examples
    --------
    >>> create_slurm('test_name', 1440, 30, 'run this command')

    """
    # ====== validate arguments ====== #
    n_node = 1

    hour = int(math.floor(duration / 60))
    minute = duration - hour * 60
    delay = int(delay)

    name = str(name)
    log_path = LOGPATH if log_path is None else str(log_path)
    if os.path.isdir(log_path):
        log_path = os.path.join(log_path, name + '.log')

    nprocess = int(nprocess)
    mem = int(mem)

    email = EMAIL if email is None else email
    if email is not None and len(email) > 0:
        email = \
"""#SBATCH --mail-type=BEGIN,FAIL,END # Type of email notification- BEGIN,END,FAIL,ALL
#SBATCH --mail-user=%s # Email to which notifications will be sent""" % str(email)
    else:
        email = ''

    if isinstance(command, str) or not hasattr(command, '__len__'):
        command = [command]
    command = ';'.join(command)

    options = OPTIONS if options is None else options
    if not isinstance(options, (tuple, list)):
        options = [options]
    options = "\n".join(["#SBATCH " + str(i) for i in options])

    modules = MODULES if modules is None else modules
    if not isinstance(modules, (tuple, list)):
        modules = [modules]
    modules = "\n".join(["moduel load %s" % i for i in modules])

    scripts = SCRIPTS if scripts is None else scripts
    if not isinstance(scripts, (tuple, list)):
        scripts = [scripts]
    scripts = "\n".join([str(i) for i in scripts])

    # ====== Select partition ====== #
    if 'gpu' in machine:
        arch = 'gpu'
        if duration <= 15:
            arch = 'gputest'
        elif duration > 14 * 24 * 60:
            arch = 'gpulong'
        maximum_gpu_per_node = 2
        for i in options:
            if 'k80' in i:
                maximum_gpu_per_node = 4
        n_node = int(math.ceil(nprocess / maximum_gpu_per_node))
        if nprocess > maximum_gpu_per_node:
            nprocess = maximum_gpu_per_node
        nprocess = "#SBATCH --gres=gpu:%d" % nprocess
        mem = "#SBATCH --mem=%d" % mem
    else:
        arch = machine
        n_node = int(math.ceil(nprocess / 16))
        mem = int(math.ceil(mem / nprocess))
        nprocess = "#SBATCH --ntasks=%d" % nprocess
        mem = "#SBATCH --mem-per-cpu=%d" % mem

    #####################################
    # Paramters: arch (gpu, gpulong, gputest), hour, minute, delay,
    # task_name, log_path, log_path, n_node, mem, n_gpu, email,
    # addition_options, modules, scripts, command
    slurm_text = _GPU_SLURM % (arch, hour, minute, delay,
                               name, log_path, log_path,
                               n_node, mem, nprocess, email,
                               options, modules, scripts, command)
    # remove blank lines
    slurm_text = "\n".join([i for i in slurm_text.split('\n') if len(i) > 0])
    return slurm_text
