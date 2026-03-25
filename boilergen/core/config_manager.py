import os
import configparser
import appdirs
import shutil
from pathlib import Path
from typing import Tuple, Optional
from git import Repo, InvalidGitRepositoryError

class ConfigManager:
    """Handles project configuration and template directory resolution."""
    
    def __init__(self, app_name: str = "boilergen"):
        self.app_name = app_name
        self.config_dir = Path(appdirs.user_config_dir(app_name))
        self.config_file = self.config_dir / "boilergen.config"
        self.config = configparser.ConfigParser()
        self._ensure_config_exists()
        self.config.read(str(self.config_file))

    def _ensure_config_exists(self):
        """Creates default config file if it doesn't exist."""
        if not self.config_file.exists():
            self.config.add_section("TEMPLATES")
            self.config.set("TEMPLATES", "TemplateLocation", "")
            self.config.set("TEMPLATES", "TemplateRepository", "")
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w") as f:
                self.config.write(f)

    def resolve_template_dir(self, default_dir: str, ui=None) -> Path:
        """
        Resolves the template directory from config or git repository.
        
        Args:
            default_dir: Default directory to use if not configured.
            ui: UI object for logging.
        """
        template_dir_str = self.config["TEMPLATES"].get("TemplateLocation", "")
        repository_url = self.config["TEMPLATES"].get("TemplateRepository", "")

        if not template_dir_str and repository_url:
            if ui: ui.warning("Cloning templates from repository...")
            
            local_clone_path = Path.cwd() / "cloned_templates"
            if not local_clone_path.exists():
                Repo.clone_from(repository_url, str(local_clone_path))
            else:
                try:
                    Repo(str(local_clone_path))
                except InvalidGitRepositoryError:
                    shutil.rmtree(local_clone_path)
                    Repo.clone_from(url=repository_url, to_path=str(local_clone_path))
            
            template_dir = local_clone_path / "templates"
        else:
            base = Path(template_dir_str) if template_dir_str else Path(default_dir)
            template_dir = base / "templates"

        return template_dir

    def get_config_path(self) -> Path:
        return self.config_file
