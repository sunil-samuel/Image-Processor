from transformers import AutoProcessor, AutoModelForCausalLM
from PIL import ImageFile

import logging, torch
from logging import Logger
from .image_to_text_abstract import ImageToTextBase


class AutomodelLLM(ImageToTextBase):
    __logger: Logger = logging.getLogger(__file__)
    __model_name = "microsoft/Florence-2-large"

    def __init__(self, device: str) -> None:

        # attn_implementation (`str`, *optional*):
        # The attention implementation to use in the model
        # (if relevant). Can be any of `"eager"` (manual
        # implementation of the attention), `"sdpa"`
        # (using [`F.scaled_dot_product_attention`](https://pytorch.org/docs/master/generated/torch.nn.functional.scaled_dot_product_attention.html)),
        # `"flash_attention_2"` (using [Dao-AILab/flash-attention](https://github.com/Dao-AILab/flash-attention)), or
        # `"flash_attention_3"` (using [Dao-AILab/flash-attention/hopper](https://github.com/Dao-AILab/flash-attention/tree/main/hopper)).
        # By default, if available, SDPA will be used for torch>=2.1.1.
        # The default is otherwise the manual `"eager"` implementation.
        self.__model = (
            AutoModelForCausalLM.from_pretrained(
                self.__model_name,
                trust_remote_code=True,
                attn_implementation="eager",
                torch_dtype="auto",
            )
            .eval()
            .cuda()
        )
        self.__processor = AutoProcessor.from_pretrained(
            self.__model_name, trust_remote_code=True
        )

        self.__prompt = "<DETAILED_CAPTION>"

    def process(self, image: ImageFile) -> list[str]:
        inputs = self.__processor(
            text=self.__prompt, images=image, return_tensors="pt"
        ).to("cuda", torch.float16)

        generated_ids = self.__model.generate(
            input_ids=inputs["input_ids"].cuda(),
            pixel_values=inputs["pixel_values"].cuda(),
            max_new_tokens=1024,
            early_stopping=False,
            do_sample=False,
            num_beams=3,
        )
        generated_text = self.__processor.batch_decode(
            generated_ids, skip_special_tokens=False
        )[0]
        parsed_answer = self.__processor.post_process_generation(
            generated_text, task=self.__prompt, image_size=(image.width, image.height)
        )
        text: str = parsed_answer["<DETAILED_CAPTION>"]
        self.__logger.debug(
            f"automodel_llm generated text [{generated_text}] -> parsed answer [{parsed_answer}] -> text [{text}]"
        )
        return [text]

    def get_name(self):
        return "automodel_llm"
