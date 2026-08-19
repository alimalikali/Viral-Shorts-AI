import importlib.util
import logging
from pathlib import Path
from typing import Dict, List
from app.config import settings
from app.plugins.base import BaseAIPlugin

logger = logging.getLogger("PluginManager")

class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, BaseAIPlugin] = {}

    def discover_and_load(self):
        """Scans the plugins directory and dynamically loads subclassed plugins."""
        plugins_dir = Path(settings.PLUGINS_DIR)
        if not plugins_dir.exists():
            return
            
        for file_path in plugins_dir.glob("*.py"):
            if file_path.name == "__init__.py" or file_path.name == "base.py":
                continue
                
            try:
                module_name = f"app.plugins.{file_path.stem}"
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    # Look for classes inheriting from BaseAIPlugin
                    for attribute_name in dir(module):
                        attribute = getattr(module, attribute_name)
                        if (
                            isinstance(attribute, type)
                            and issubclass(attribute, BaseAIPlugin)
                            and attribute is not BaseAIPlugin
                        ):
                            plugin_instance = attribute()
                            if plugin_instance.initialize():
                                self.plugins[plugin_instance.plugin_name] = plugin_instance
                                logger.info(f"Successfully loaded plugin: {plugin_instance.plugin_name} ({plugin_instance.plugin_type})")
            except Exception as e:
                logger.error(f"Failed to load plugin from {file_path.name}: {str(e)}")

    def get_plugins_by_type(self, plugin_type: str) -> List[BaseAIPlugin]:
        """Fetch all plugins of a specific type (e.g. 'moment_scoring')."""
        return [p for p in self.plugins.values() if p.plugin_type == plugin_type]

plugin_manager = PluginManager()
# Auto discover on startup
plugin_manager.discover_and_load()
