
import sys, zlib, struct, io, re

def _tokenize(t):
    return re.findall(r"[A-Za-z_]+|[.,;!?—\-]", t)

def _pack_varints(vals):
    buf = bytearray()
    for v in vals:
        while v >= 128:
            buf.append((v & 0x7F) | 0x80)
            v >>= 7
        buf.append(v)
    return bytes(buf)

def compress_text(text):
    tokens = _tokenize(text)
    vocab = {t: i+1 for i, t in enumerate(sorted(set(tokens)))}
    ids = [vocab[t] for t in tokens]
    id_bytes = _pack_varints(ids)
    dict_bytes = b"|".join(f"{k}:{v}".encode() for k, v in sorted(vocab.items()))
    body = io.BytesIO()
    body.write(struct.pack(">I", len(dict_bytes)))
    body.write(dict_bytes)
    body.write(struct.pack(">I", len(id_bytes)))
    body.write(id_bytes)
    return zlib.compress(body.getvalue(), level=3)

text = sys.stdin.read()
compressed = compress_text(text)
sys.stdout.buffer.write(compressed)
