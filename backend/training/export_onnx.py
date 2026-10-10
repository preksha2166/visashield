"""Export the fine-tuned classifier and the RAG embedder to int8 ONNX for the lite runtime.

The lite runtime (no PyTorch) runs in ~300 MB of RAM, so VisaShield fits on small free
hosts such as Render's 512 MB instances. Usage (needs torch, run once after training):

    python -m training.export_onnx
"""
import app  # noqa: F401  (torch before scikit-learn on Windows)

import shutil

import torch
from onnxruntime.quantization import QuantType, quantize_dynamic
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer

from app import config

OUT = config.ONNX_DIR


class _Logits(torch.nn.Module):
    def __init__(self, m):
        super().__init__()
        self.m = m

    def forward(self, input_ids, attention_mask):
        return self.m(input_ids=input_ids, attention_mask=attention_mask).logits


class _Hidden(torch.nn.Module):
    def __init__(self, m):
        super().__init__()
        self.m = m

    def forward(self, input_ids, attention_mask, token_type_ids):
        return self.m(input_ids=input_ids, attention_mask=attention_mask, token_type_ids=token_type_ids).last_hidden_state


def export(module, inputs: dict, out_name: str, output_name: str, op_types=None):
    fp32 = OUT / f"{out_name}.fp32.onnx"
    axes = {k: {0: "batch", 1: "seq"} for k in inputs}
    axes[output_name] = {0: "batch"} if output_name == "logits" else {0: "batch", 1: "seq"}
    torch.onnx.export(
        module.eval(), tuple(inputs.values()), str(fp32), input_names=list(inputs), output_names=[output_name],
        dynamic_axes=axes, opset_version=17, dynamo=False,
    )
    # Per-channel 8-bit. op_types=["MatMul"] keeps the embedding table in fp32 (more accurate, but
    # the classifier would then exceed GitHub's 100 MB file limit, so it quantizes everything).
    # Unsigned weights (U8U8): the default signed weights (U8S8) saturate on x86 CPUs without
    # VNNI, which made the classifier output near-constant probabilities on Render's servers
    # while it worked on VNNI laptops.
    quantize_dynamic(str(fp32), str(OUT / f"{out_name}.onnx"), weight_type=QuantType.QUInt8, per_channel=True, op_types_to_quantize=op_types)
    fp32.unlink()
    print(f"wrote {OUT / f'{out_name}.onnx'} ({(OUT / f'{out_name}.onnx').stat().st_size / 1e6:.1f} MB)")


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    tok = AutoTokenizer.from_pretrained(config.CLASSIFIER_DIR)
    clf = AutoModelForSequenceClassification.from_pretrained(config.CLASSIFIER_DIR)
    enc = tok(["example text"], return_tensors="pt")
    export(_Logits(clf), {"input_ids": enc["input_ids"], "attention_mask": enc["attention_mask"]}, "classifier", "logits")
    shutil.copy(config.CLASSIFIER_DIR / "tokenizer.json", OUT / "classifier_tokenizer.json")
    (OUT / "classifier_labels.txt").write_text("\n".join(clf.config.id2label[i] for i in range(len(clf.config.id2label))), encoding="utf-8")

    etok = AutoTokenizer.from_pretrained(config.EMBED_MODEL)
    emb = AutoModel.from_pretrained(config.EMBED_MODEL)
    enc = etok(["example text"], return_tensors="pt")
    export(_Hidden(emb), {k: enc[k] for k in ("input_ids", "attention_mask", "token_type_ids")}, "embedder", "last_hidden_state", op_types=["MatMul"])
    etok.backend_tokenizer.save(str(OUT / "embedder_tokenizer.json"))


if __name__ == "__main__":
    main()
