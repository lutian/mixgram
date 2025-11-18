import os
from mixgram.api import encode_video, decode_video
import hashlib
import torch


# ---------------------------
# 1. Key de exemplo  (opcional)
# ---------------------------
key = hashlib.sha256(b'minha-senha-secreta').digest()

# ---------------------------
# 2. Texto de entrada
# ---------------------------
file_path = "examples/demo_mixgram.txt" 

with open(file_path, 'r') as file:
    texto = file.read()

print("\n=== TEXTO ORIGINAL ===\n")
print(texto)


# ---------------------------
# 3. Rodar o encoder
# ---------------------------
print("\n=== ENCODEANDO PARA VÍDEO ===\n")

saida_video = "examples/demo_mixgram.mkv"

result = encode_video(
    text=texto,
    output_mkv=saida_video,
    model_name="all-MiniLM-L6-v2",  # funciona com chunks
    key=key  # sem criptografia para o demo
)

print("Vídeo gerado:", result["output"])
print("Frames usados:", result["frames"])
print("Pasta temporária:", result["tmpdir"])


# ---------------------------
# 4. Decodificar o vídeo
# ---------------------------
print("\n=== DECODIFICANDO O VÍDEO ===\n")

decoded = decode_video(saida_video, key=key)

texto_recuperado = decoded["text"]

embeddings = decoded["embeddings"]  # lista de embeddings por chunk (se solicitado)

chunks = decoded["chunks"]  # lista de chunks de texto (se solicitado)

print("\n=== TEXTO RECUPERADO ===\n")
print(texto_recuperado)

print("\n=== embeddings RECUPERADO ===\n")
print(embeddings[0:1])  # mostra só os 2 primeiros

print("\n=== chunks RECUPERADO ===\n")
print(chunks[0:1])  # mostra só os 2 primeiros

# ---------------------------
# 5. Definir y codificar el texto de consulta
# ---------------------------
from sentence_transformers import SentenceTransformer, util
model = SentenceTransformer('all-MiniLM-L6-v2')
query = "O que é mixgram?"
query_embedding = model.encode(query, convert_to_tensor=True)

corpus_embeddings = torch.tensor(embeddings)

hits = util.semantic_search(query_embedding, corpus_embeddings, top_k=2)

hits = hits[0]  # resultados para a primeira query

# Mostrar los resultados
print("Consulta:", query)
print("Resultados de búsqueda semántica:")
for hit in hits:
    corpus_id = hit['corpus_id']
    score = hit['score']
    #print(f"\Embeddings: {corpus_embeddings[corpus_id]}")
    print(f"\nTexto: {chunks[corpus_id]}")
    print(f"Acuracidade: {score:.4f}")

# ---------------------------
# 6. Validar round-trip
# ---------------------------
print("\n=== VERIFICANDO ===")

if texto == texto_recuperado:
    print("✔ OK! Texto recuperado perfeitamente!")
else:
    print("❌ Erro: textos diferentes!")
    print("Diferença detectada.")
