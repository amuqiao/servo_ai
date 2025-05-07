import importlib
import pkgutil
from pathlib import Path

class ValidationConfig:
    def __init__(self):
        self.validators = {}

    def load_validators(self):
        validators_path = Path(__file__).parent.parent / 'validators'
        for _, module_name, _ in pkgutil.iter_modules([str(validators_path)]):
            module = importlib.import_module(f'validators.{module_name}')
            if hasattr(module, 'register_validators'):
                module.register_validators(self)

def register_validator(name: str, validator):
    ValidationConfig().validators[name] = validator

validation_config = ValidationConfig()