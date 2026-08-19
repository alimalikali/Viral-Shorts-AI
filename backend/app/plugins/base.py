from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAIPlugin(ABC):
    """
    Abstract Base Class for all AI model plugins.
    Allows hot-swapping or expanding moment detection, reframing, or caption styling.
    """
    
    @property
    @abstractmethod
    def plugin_name(self) -> str:
        """Returns the unique identifier of the plugin."""
        pass
        
    @property
    @abstractmethod
    def plugin_type(self) -> str:
        """Returns the category of plugin, e.g., 'moment_scoring', 'audio_enhancement', 'caption_effects'."""
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """Load weights, check hardware compatibility, and setup cache."""
        pass

    @abstractmethod
    def execute(self, video_path: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the main AI workload.
        :param video_path: Path to target file.
        :param context: Dictionary containing pipeline outputs (transcripts, scene cuts, audio peaks).
        :return: Execution results dictionary.
        """
        pass
