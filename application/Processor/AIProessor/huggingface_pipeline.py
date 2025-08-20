from transformers import pipeline
from PIL import ImageFile

import logging
from logging import Logger
from .image_to_text_abstract import ImageToTextBase


class HuggingFacePipeline(ImageToTextBase):
    """
    # Image to Text

    Image to text models output a text from a given image. Image captioning
    or optical character recognition can be considered as the most common
    applications of image to text.

    * **platform** : HuggingFace
    * **url** : https://huggingface.co/tasks/image-to-text
    """

    __model_names = {
        "vit-gpt2-coco-en": "ydshieh/vit-gpt2-coco-en",
        "blip-image-captioning-base": "Salesforce/blip-image-captioning-base",
    }

    __pipelines: dict[str, pipeline] = {}
    __logger: Logger = logging.getLogger(__file__)
    __task = "image-to-text"

    def __init__(self, device: str) -> None:
        for key, value in self.__model_names.items():
            self.__pipelines[key] = pipeline(
                task=self.__task, model=value, device=device
            )

    def process(self, image: ImageFile, level: int) -> list[str]:
        rval: list[str | list] = []

        try:
            for key in self.__model_names:
                pipe: pipeline = self.__pipelines[key]

                captioner = pipe(image)
                text = str(captioner[0]["generated_text"]).strip()
                self.__logger.info(f"Generated text for [{key}] => [{text}]")
                rval.append(text)
            return rval
        except ValueError as error:
            self.__logger.warning(f"Input image error {error}")
            return rval
        except Exception as e:
            self.__logger.warning(
                f"Exception in generating image-to-text filename [{e}]."
            )

    def get_name(self):
        return "huggingface_pipeline"
