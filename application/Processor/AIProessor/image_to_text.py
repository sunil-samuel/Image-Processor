from PIL import Image, ImageFile

import torch, logging
from logging import Logger

from .huggingface_pipeline import HuggingFacePipeline
from .clip_processor import ClipProcessor
from .automodel_llm import AutomodelLLM
from .image_to_text_abstract import ImageToTextBase


class ImageToText:
    __textToImageProcessors: list[ImageToTextBase] = []

    __logger: Logger = logging.getLogger(__file__)

    def __init__(self) -> None:
        device = "cpu"
        if torch.cuda.is_available():
            device = "cuda"
        # For Apple Silicon
        elif torch.backends.mps.is_available():
            device = "mps"
        self.__logger.info(f"Using device: [{device}]")

        self.__textToImageProcessors.append(HuggingFacePipeline(device))
        self.__textToImageProcessors.append(ClipProcessor(device))
        self.__textToImageProcessors.append(AutomodelLLM(device))

    def process(self, filepath: str, level:str) -> list[str]:
        self.__logger.info(f"{__name__} - prompt [{filepath}]")
        rval: list[any] = []
        try:
            image: ImageFile = Image.open(filepath)
            for processor in self.__textToImageProcessors:
                try:
                    rval.append(processor.process(image, level))
                except Exception as e:
                    self.__logger.warning(
                        f"Error processing [{processor.get_name()}]. [{e}]"
                    )
            self.__logger.info(f"ImageToText rval is [{rval}]")
            return list(self.__flatten(rval))
        except Exception as e:
            self.__logger.warning(
                f"Exception in generating image-to-text filename [{filepath}] [{e}]."
            )
            return []

    def __flatten(self, data: list[any]):
        for item in data:
            if isinstance(item, list):
                yield from self.__flatten(item)
            else:
                yield item
