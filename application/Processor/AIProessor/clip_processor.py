from PIL import ImageFile
from transformers import CLIPProcessor, CLIPModel
from .image_to_text_abstract import ImageToTextBase
import logging
from logging import Logger


class ClipProcessor(ImageToTextBase):

    __model_name = "geolocal/StreetCLIP"
    __model: CLIPModel = None
    __processor: CLIPProcessor = None
    __logger: Logger = logging.getLogger(__file__)

    def __init__(self, device: str) -> None:
        self.__model = CLIPModel.from_pretrained(self.__model_name)
        self.__processor = CLIPProcessor.from_pretrained(self.__model_name)

    def process(self, image: ImageFile, level:int) -> list[str]:
        self.__logger.info("Processing clip processor")
        inputs = self.__processor(images=image, return_tensors="pt", padding=True)

        outputs = self.__model(**inputs)
        self.__logger.info(f"OUTPUT [{outputs}]")
        # this is the image-text similarity score
        logits_per_image = outputs.logits_per_image
        # we can take the softmax to get the label probabilities
        probs = logits_per_image.softmax(dim=1)
        return []

    def get_name(self):
        return "clip_processor"
