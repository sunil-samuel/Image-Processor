from abc import ABC, abstractmethod


class ImageToTextBase(ABC):
    
    @abstractmethod
    def process(self, device:str) -> list[str]:
        pass
    
    @abstractmethod
    def get_name(self)->str:
        pass