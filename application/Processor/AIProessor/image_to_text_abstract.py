from abc import ABC, abstractmethod
from PIL import ImageFile


class ImageToTextBase(ABC):

    @abstractmethod
    def process(self, image: ImageFile, level: int) -> list[str]:
        pass

    @abstractmethod
    def get_name(self) -> str:
        pass
