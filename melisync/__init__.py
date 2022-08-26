# -*- coding: utf-8 -*-
from . import controllers
from . import models
"""
# Hooks
def pre_init_hook(cr):
    import subprocess
    import sys

    def install(package):
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

    print('pre_init_hook')
    install('git+ssh://git@bitbucket.org/pergadev/meli-api.git@0.0.1')
"""