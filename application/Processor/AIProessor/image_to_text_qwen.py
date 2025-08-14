import logging, torch
from logging import Logger
from transformers import (
    AutoModelForCausalLM,
    AutoProcessor,
    Qwen2_5_VLForConditionalGeneration,
)
from typing import Any
from PIL import Image


class ImageToText:
    """
    # Image to Text

    Image to text models output a text from a given image. Image captioning
    or optical character recognition can be considered as the most common
    applications of image to text.

    * **platform** : HuggingFace
    * **url** : https://huggingface.co/tasks/image-to-text
    """

    __model_id: str = "Qwen/Qwen2.5-VL-7B-Instruct"
    __logger: Logger = logging.getLogger(__file__)
    __device: str = "cuda" if torch.cuda.is_available() else "cpu"
    __model: Any = None
    __processor: Any = None
    __gen_kwargs = {"max_new_tokens": 1024, "do_sample": False}
    __prompt: str = (
        f"Describe this image in as much detail as possible. What is happening?"
        f"Who is there?  What colors do you see?  What is the mood of the people?"
    )
    __messages: list[dict[str, Any]] = None

    def __init__(self) -> None:
        self.__logger.info(f"Using device [{self.__device}]")

        # ---- Load the model and processor from Hugging Face
        # Using torch_dtype="auto" enables mixed-precision (bfloat16) for efficiency
        # device_map="auto" will automatically place the model on the available GPU.
        # trust_remote_code - required for custom model architectures
        self.__model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            self.__model_id,
            torch_dtype="auto",
            device_map="auto",
        )
        self.__processor = AutoProcessor.from_pretrained(self.__model_id)
        self.__logger.info(f"The prompt is [{self.__prompt}]")
        self.__logger.info("Model and processor loaded successfully.")

    def process(self, filepath: str) -> str:

        # ---- Prepare the inputs (image and text prompt)
        self.__logger.info(f"Generating text-to-image for file [{filepath}]")

        # ---- Load image
        image = Image.open(filepath)

        # The model expects the input in a specific conversational format.
        self.__messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": image},
                    {"type": "text", "text": self.__prompt},
                ],
            }
        ]

        # ---- Process the inputs using the processor. This handles tokenizing the text
        # and preparing the image tensor.
        text = self.__processor.apply_chat_template(
            self.__messages,
            add_generation_prompt=True,
            tokenize=False,
            return_tensors="pt",
        )
        inputs = self.__processor(text=[text], images=[image], padding=True, return_tensors="pt")
        inputs = inputs.to("cuda")
        # ---- Generate the text output
        self.__logger.info("Generating text...")
        generated_ids = self.__model.generate(**inputs, **self.__gen_kwargs)

        # The generated IDs include the input prompt, so we remove them
        generated_ids = [
            output_ids[len(input_ids) :]
            for input_ids, output_ids in zip(inputs.input_ids, generated_ids)
        ]

        # Step 5: Decode the generated tokens into a string
        response = self.__processor.batch_decode(
            generated_ids, skip_special_tokens=True
        )[0]

        return response.strip()
