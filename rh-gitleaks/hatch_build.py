from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from pathlib import Path
import re

class CustomHook(BuildHookInterface):
    def initialize(self, version, build_data):
        if self.target_name == "sdist":
            self.create_spec(build_data)

    def create_spec(self, build_data):
        specin = Path('rh-gitleaks.spec.in')
        spec = Path('rh-gitleaks.spec')

        with specin.open() as infh, spec.open("w") as outfh:
            for line in infh:
                line = line.replace("@VERSION@", self.metadata.version)
                outfh.write(line)
        
        build_data['force_include'][spec.absolute().as_posix()] = 'rh-gitleaks.spec'
