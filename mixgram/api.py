import os
import tempfile
import subprocess
from typing import List
from PIL import Image
import numpy as np

from .utils import (
    bytes_to_base36,
    base36_to_bytes,
    compress_bytes,
    decompress_bytes,
)
from .palette import PALETTE_RGB

# -------------------------------------------------------------------
# CONSTANTES
# -------------------------------------------------------------------

W = H = 512
CHUNK_CAP = W * H  # 262144 chars por frame
DELIM = "."        # delimitador seguro

# -------------------------------------------------------------------
# SPLIT TEXT IN CHUNKS DE FORMA INTELIGENTE
# -------------------------------------------------------------------

def split_text_smartly(text, payload_per_frame):
    chunks = []
    start = 0
    while start < len(text):
        end = start + payload_per_frame
        
        # Se o final do chunk ultrapassar o final do texto, apenas pegue o resto
        if end >= len(text):
            # NÃO use .strip() aqui, pois queremos preservar espaços e \n no chunk final
            chunks.append(text[start:]) 
            break
            
        search_area_start = max(start, end - int(payload_per_frame * 0.2))
        chunk_end = end # Fallback padrão se nada for encontrado

        # 1. Tentar encontrar o último retorno de carro (\n)
        last_cr_index = text.rfind('\n', search_area_start, end)
        if last_cr_index != -1:
            chunk_end = last_cr_index + 1 # Inclui o \n no chunk

        # 2. Se não encontrou \n, tentar encontrar o último ponto final (.)
        else:
            last_dot_index = text.rfind('.', search_area_start, end)
            if last_dot_index != -1:
                # Inclui o ponto e qualquer espaço após ele se for o caso
                chunk_end = last_dot_index + 1
                # Lógica extra: verificar se há espaço após o ponto
                if chunk_end < len(text) and text[chunk_end] == ' ':
                    chunk_end += 1

            # 3. Se não encontrou \n nem ., tentar encontrar o último espaço em branco
            else:
                last_space_index = text.rfind(' ', search_area_start, end)
                if last_space_index != -1:
                    chunk_end = last_space_index + 1 # Inclui o espaço no chunk
                # Caso contrário (4), chunk_end permanece 'end' (quebra forçada)

        # Adiciona o chunk à lista e atualiza o início para a próxima iteração
        # Removendo o .strip() daqui
        chunks.append(text[start:chunk_end]) 
        start = chunk_end
        
        # Pular espaços extras ou retornos de carro no INÍCIO do próximo chunk
        while start < len(text) and text[start].isspace():
            start += 1
            
    # Certifique-se de que a lista final não contenha strings vazias se a entrada tiver muito espaço no final
    return [chunk for chunk in chunks if chunk]

# -------------------------------------------------------------------
# EMBEDDINGS
# -------------------------------------------------------------------

def compute_embeddings(chunks: List[str], model_name='all-MiniLM-L6-v2'):
    try:
        from sentence_transformers import SentenceTransformer
    except Exception:
        raise RuntimeError("Instale sentence-transformers para embeddings")

    model = SentenceTransformer(model_name)
    embs = model.encode(chunks, show_progress_bar=False)

    # converte lista de floats -> bytes compactados -> base36
    out = []
    import struct

    for vec in embs:
        raw = b"".join(struct.pack("!f", f) for f in vec)
        comp = compress_bytes(raw)
        b36 = bytes_to_base36(comp)
        out.append(b36)

    return out


# -------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------

def _string_to_image(s: str):
    """Converte string (caracteres da palette) para imagem RGB 256x256"""
    arr = np.zeros((H, W, 3), dtype=np.uint8)

    for p, ch in enumerate(s):
        x = p % W
        y = p // W
        rgb = PALETTE_RGB.get(ch, (0, 0, 0))
        arr[y, x] = rgb

    return Image.fromarray(arr, "RGB")


def _image_to_string(img: Image.Image):
    img = img.convert("RGB")
    pix = img.load()
    chars = []

    for p in range(CHUNK_CAP):
        x = p % W
        y = p // W
        rgb = pix[x, y]

        # busca direta
        ch = None
        for k, v in PALETTE_RGB.items():
            if v == rgb:
                ch = k
                break

        # fallback: busca pelo mais próximo
        if ch is None:
            best = None
            bestd = None
            for kk, vv in PALETTE_RGB.items():
                d = (rgb[0] - vv[0]) * 2 + (rgb[1] - vv[1]) * 2 + (rgb[2] - vv[2]) ** 2
                if bestd is None or d < bestd:
                    best = kk
                    bestd = d
            ch = best

        chars.append(ch)

    return "".join(chars)


# -------------------------------------------------------------------
# ENCODE
# -------------------------------------------------------------------

def encode_video(text: str, output_mkv: str, model_name='all-MiniLM-L6-v2', key: bytes = None):
    if key is not None and len(key) != 32:
        raise ValueError("key must be 32 bytes")

    payload_per_frame = 512 # número aproximado de chars por chunk
    chunks = split_text_smartly(text, payload_per_frame)

    # embeddings -> b36
    embeddings_b36 = compute_embeddings(chunks, model_name=model_name)

    # -------------------------------------------------------------------
    # FRAMES 0..N: texto + embedding
    # -------------------------------------------------------------------

    tmpdir = tempfile.mkdtemp(prefix="mixgram_")
    pngs = []

    parts = [str(len(chunks))]
    for txt, emb_b36 in zip(chunks, embeddings_b36):
        comp_txt = bytes_to_base36(compress_bytes(txt.encode("utf-8")))
        parts.append(comp_txt)
        parts.append(emb_b36)

    # String contínua delimitada (ex: "N.{txt1}.{emb1}.{txt2}.{emb2}...")
    full_payload = DELIM.join(parts)

    # Corta a string em blocos de CHUNK_CAP caracteres (cada bloco = 1 frame)
    # Preenche o último com '0' até CHUNK_CAP
    num_frames = (len(full_payload) + CHUNK_CAP - 1) // CHUNK_CAP

    for frame_idx in range(num_frames):
        start = frame_idx * CHUNK_CAP
        end = start + CHUNK_CAP
        slice_str = full_payload[start:end]
        if len(slice_str) < CHUNK_CAP:
            slice_str = slice_str.ljust(CHUNK_CAP, ";")

        # converte slice -> imagem e salva
        img = _string_to_image(slice_str)
        path = os.path.join(tmpdir, f"frame_{frame_idx:06d}.png")
        img.save(path)
        pngs.append(path)

    # -------------------------------------------------------------------
    # FFmpeg
    # -------------------------------------------------------------------

    cmd = [
        "ffmpeg",
        "-y",
        "-framerate", "60",
        "-i", os.path.join(tmpdir, "frame_%06d.png"),
        "-c:v", "png",
        "-pix_fmt", "rgb24",
        output_mkv
    ]

    subprocess.check_call(cmd)

    return {
        "output": output_mkv,
        "tmpdir": tmpdir,
        "frames": len(pngs)
    }


# -------------------------------------------------------------------
# DECODE
# -------------------------------------------------------------------

def decode_video(input_mkv: str, key: bytes = None):
    tmpdir = tempfile.mkdtemp(prefix="mixgram_decode_")

    # Extrai frames
    subprocess.check_call([
        "ffmpeg", "-y", "-i", input_mkv,
        os.path.join(tmpdir, "frame_%06d.png")
    ])

    files = sorted(
        os.path.join(tmpdir, f)
        for f in os.listdir(tmpdir)
        if f.startswith("frame_")
    )

    if not files:
        raise RuntimeError("Nenhum frame encontrado.")

    # -------------------------------------------------------------------
    # Lê frame 0
    # -------------------------------------------------------------------

    full_payload = "".join([_image_to_string(Image.open(p)) for p in files])  # sem .rstrip aqui
    full_payload = full_payload.rstrip(";")  # remove padding do último frame
    parts = full_payload.split(DELIM)

    num_chunks = int(parts[0])
    cursor = 1

    textos = []
    embeddings = []

    import struct

    for _ in range(num_chunks):
        comp_txt_b36 = parts[cursor]
        comp_emb_b36 = parts[cursor + 1]
        cursor += 2

        # decode texto
        txt_bytes = decompress_bytes(base36_to_bytes(comp_txt_b36))
        txt = txt_bytes.decode("utf-8")
        textos.append(txt)

        # decode embedding
        emb_comp = base36_to_bytes(comp_emb_b36)
        emb_raw = decompress_bytes(emb_comp)

        # converte floats
        vec = []
        for i in range(0, len(emb_raw), 4):
            (f,) = struct.unpack("!f", emb_raw[i:i + 4])
            vec.append(f)

        embeddings.append(vec)

    # junta o texto completo
    final_text = "".join(textos)

    return {
        "text": final_text,
        "chunks": textos,
        "embeddings": embeddings,
        "frames": len(files)
    }