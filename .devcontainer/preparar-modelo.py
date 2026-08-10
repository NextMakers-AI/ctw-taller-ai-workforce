"""Baja el modelo de busqueda por significado al cache de la imagen.

Se ejecuta UNA vez, durante la construccion del contenedor. El alumno nunca
descarga estos 2 GB: ya vienen dentro de la imagen.

Se bajan los DOS formatos a proposito. Cual se usa depende de la maquina:
`semantica.py` intenta primero el motor de torch (SentenceTransformer, que lee
`model.safetensors`) y si falla cae al motor ONNX (`onnx/model.onnx`). En Linux
normalmente gana torch, pero el respaldo tiene que estar igual: un contenedor al
que le falte el ONNX rompe el camino de respaldo en silencio.
"""

from __future__ import annotations

import sys

from huggingface_hub import hf_hub_download

MODELO = "intfloat/multilingual-e5-base"

# Los once archivos que el proyecto llega a abrir. La lista es explicita en vez
# de un `snapshot_download` completo porque el repositorio publica ademas pesos
# en formatos que aca no se usan (PyTorch .bin, TensorFlow), y bajarlos serian
# cientos de megabytes muertos dentro de la imagen.
ARCHIVOS = [
    # Motor de torch (SentenceTransformer)
    "config.json",
    "tokenizer.json",
    "sentencepiece.bpe.model",
    "special_tokens_map.json",
    "tokenizer_config.json",
    "sentence_bert_config.json",
    "modules.json",
    "1_Pooling/config.json",
    "model.safetensors",
    # Motor de respaldo (onnxruntime)
    "onnx/model.onnx",
    "onnx/tokenizer.json",
]


def main() -> int:
    fallos: list[str] = []

    for i, archivo in enumerate(ARCHIVOS, start=1):
        try:
            ruta = hf_hub_download(MODELO, archivo)
            print(f"  [{i:2d}/{len(ARCHIVOS)}] {archivo} -> {ruta}", flush=True)
        except Exception as exc:  # noqa: BLE001 - queremos el nombre, no la traza
            fallos.append(f"{archivo}: {type(exc).__name__}")
            print(f"  [{i:2d}/{len(ARCHIVOS)}] {archivo} -> FALLO", flush=True)

    if fallos:
        # Fallar la construccion a proposito. Una imagen a la que le falta un
        # archivo del modelo se ve sana y revienta en el taller, que es el peor
        # momento posible para enterarse.
        print("\nNo se pudieron bajar estos archivos:", file=sys.stderr)
        for fallo in fallos:
            print(f"  - {fallo}", file=sys.stderr)
        return 1

    print(f"\nModelo {MODELO} completo en el cache: {len(ARCHIVOS)} archivos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
