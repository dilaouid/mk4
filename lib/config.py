import os
import configparser
from pathlib import Path
from typing import Dict

DEFAULT_CONFIG = {
    "FFMPEG": {
        "ENCODER": "libx264",
        "CRF": "23"
    },
    "FONT": {
        "Size": "24",
        "Name": "Arial"
    }
}

class Config:
    def __init__(self):
        self.config_file = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "config.ini"
        # Rendre ConfigParser insensible à la casse
        self.config = configparser.ConfigParser(interpolation=None)
        # Cette option rend le parser insensible à la casse des clés
        self.config.optionxform = str
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from file or create default if not exists"""
        if self.config_file.exists():
            self.config.read(self.config_file)
            # Convertir les clés en majuscules pour correspondre à l'utilisation dans le code
            for section in self.config.sections():
                for key in list(self.config[section].keys()):
                    if key.upper() != key:
                        value = self.config[section][key]
                        self.config[section][key.upper()] = value
        else:
            # Set default config
            for section, options in DEFAULT_CONFIG.items():
                self.config[section] = options
            self.save_config()

    def save_config(self) -> None:
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            self.config.write(f)

    def get_config(self) -> Dict[str, Dict[str, str]]:
        """Get config as dictionary"""
        config_dict = {}
        for section in self.config.sections():
            config_dict[section] = dict(self.config[section])
        return config_dict

    def update_config(self, section: str, key: str, value: str) -> None:
        """Update a specific config value"""
        if section not in self.config:
            self.config[section] = {}
        # Stocker la clé en majuscules pour cohérence
        self.config[section][key.upper()] = value
        self.save_config()

    def update_section(self, section: str, data: Dict[str, str]) -> None:
        """Update an entire section"""
        if section not in self.config:
            self.config[section] = {}
        for key, value in data.items():
            # Stocker la clé en majuscules pour cohérence
            self.config[section][key.upper()] = value
        self.save_config()

# Initialize global config instance
config_manager = Config()
config = config_manager.get_config()

# Helper function to access config with default values
def get_config_value(section, key, default=None):
    """Get a config value with a default fallback"""
    try:
        # Essayer avec la clé originale
        value = config.get(section, {}).get(key)
        if value is not None:
            return value
        
        # Essayer avec la clé en majuscules
        value = config.get(section, {}).get(key.upper())
        if value is not None:
            return value
        
        # Essayer avec la clé en minuscules
        value = config.get(section, {}).get(key.lower())
        if value is not None:
            return value
        
        return default
    except:
        return default

# Make sure we have at least the default values if something goes wrong
if not config or not config.get('FFMPEG') or not config.get('FONT'):
    print("Warning: Config not properly loaded, using defaults")
    config = DEFAULT_CONFIG