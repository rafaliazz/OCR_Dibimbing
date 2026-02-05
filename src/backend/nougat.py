from pathlib import Path
import time
import torch
from PIL import Image
from transformers import AutoProcessor, VisionEncoderDecoderModel

MODEL_NAME = "facebook/nougat-small"


class NougatOCR:
    def __init__(self, device: str | None = None):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"

        self.device = device

        self.processor = AutoProcessor.from_pretrained(
            MODEL_NAME,
            use_fast=False,
            trust_remote_code=True,
        )

        self.model = VisionEncoderDecoderModel.from_pretrained(
            MODEL_NAME,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        ).to(device)

        self.model.eval()

    @torch.inference_mode()
    def run(self, image_path: str | Path):
        image = Image.open(image_path).convert("RGB")

        start = time.time()

        inputs = self.processor(
            images=image,
            return_tensors="pt",
        ).to(self.device)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=1024,
        )

        text = self.processor.batch_decode(
            outputs,
            skip_special_tokens=True,
        )[0]

        elapsed = time.time() - start

        return {
            "text": text.strip(),
            "time": elapsed,
        }


# CLI test
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)

    args = parser.parse_args()

    ocr = NougatOCR()
    out = ocr.run(args.image)

    print("Time:", out["time"])
    print(out["text"])
