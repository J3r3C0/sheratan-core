#!/usr/bin/env python3
# Reed–Solomon (n,k) over GF(256), pure Python, no external deps.
# - Systematic generator: [ I_k ; V_{(n-k)×k} ] with Vandermonde on distinct alphas.
# - Encode: split data into k equal-sized shards per block; compute (n-k) parity shards.
# - Decode: from any k shards, invert the corresponding k×k submatrix to recover original k data shards.
#
# NOTE: Optimized for clarity; not cryptographic; fine for MB–GB with chunking.

from pathlib import Path

PRIM = 0x11d  # x^8 + x^4 + x^3 + x^2 + 1 (AES-style)

# --- GF(256) tables ---
alog = [0]*512
logt = [0]*256

def _init_tables():
    x = 1
    for i in range(0,255):
        alog[i] = x
        logt[x] = i
        x <<= 1
        if x & 0x100:
            x ^= PRIM
    for i in range(255,512):
        alog[i] = alog[i-255]

_init_tables()

def gf_add(a,b): return a ^ b
def gf_sub(a,b): return a ^ b
def gf_mul(a,b):
    if a==0 or b==0: return 0
    return alog[(logt[a] + logt[b]) % 255]
def gf_inv(a):
    if a==0: raise ZeroDivisionError()
    return alog[255 - logt[a]]
def gf_div(a,b):
    if b==0: raise ZeroDivisionError()
    if a==0: return 0
    return alog[(logt[a] - logt[b]) % 255]

def gf_mat_mul(A,B):
    # A: r×m, B: m×c -> r×c
    r = len(A); m = len(A[0]); c = len(B[0])
    out = [[0]*c for _ in range(r)]
    for i in range(r):
        Ai = A[i]
        for k in range(m):
            aik = Ai[k]
            if aik==0: continue
            Bk = B[k]
            for j in range(c):
                out[i][j] ^= gf_mul(aik, Bk[j])
    return out

def gf_mat_inv(M):
    n = len(M); assert n==len(M[0])
    A = [row[:] for row in M]
    I = [[1 if i==j else 0 for j in range(n)] for i in range(n)]
    # Gauss-Jordan
    for col in range(n):
        # find pivot
        piv = None
        for r in range(col,n):
            if A[r][col]!=0: piv=r; break
        if piv is None:
            raise ValueError("singular matrix")
        if piv!=col:
            A[col],A[piv] = A[piv],A[col]
            I[col],I[piv] = I[piv],I[col]
        inv_p = gf_inv(A[col][col])
        # normalize row
        for j in range(n):
            A[col][j] = gf_mul(A[col][j], inv_p)
            I[col][j] = gf_mul(I[col][j], inv_p)
        # eliminate others
        for r in range(n):
            if r==col: continue
            f = A[r][col]
            if f==0: continue
            for j in range(n):
                A[r][j] ^= gf_mul(f, A[col][j])
                I[r][j] ^= gf_mul(f, I[col][j])
    return I

def vandermonde(rows, cols, start=1):
    # rows × cols matrix with a_i^{j}, a_i distinct non-zero
    # choose a_i = start + i (mod 255, mapped via alog?), simpler: use powers of primitive element: a_i = alog[i+1]
    M = [[0]*cols for _ in range(rows)]
    for i in range(rows):
        a = alog[(i+1) % 255]  # distinct base
        val = 1
        for j in range(cols):
            M[i][j] = val
            val = gf_mul(val, a)
    return M

def chunk_bytes(data: bytes, k: int, shard_size: int):
    # pad to k*shard_size
    total = len(data)
    block = k * shard_size
    pad = (block - (total % block)) % block
    data2 = data + (b"\x00"*pad)
    return data2, total, pad

def encode(data: bytes, k: int=12, n: int=20, shard_size: int=1024*64):
    assert 0 < k < n <= 255
    # Systematic generator: [I_k ; V_(n-k)×k]
    V = vandermonde(n-k, k)
    # split into blocks of k * shard_size
    data2, total, pad = chunk_bytes(data, k, shard_size)
    shards = []  # list of bytearrays for n shards (concatenated across blocks)
    for _ in range(n):
        shards.append(bytearray())
    # process blocks
    for off in range(0, len(data2), k*shard_size):
        # k data shards for this block
        dblock = [bytearray(data2[off + i*shard_size: off + (i+1)*shard_size]) for i in range(k)]
        # append to first k outputs (systematic)
        for i in range(k):
            shards[i].extend(dblock[i])
        # compute parity shards
        # For each parity row r in V, compute linear combo of k data shards
        for r in range(n-k):
            out = bytearray(shard_size)
            row = V[r]
            for i in range(k):
                coef = row[i]
                if coef==0: continue
                db = dblock[i]
                if coef==1:
                    for j in range(shard_size): out[j] ^= db[j]
                else:
                    for j in range(shard_size): out[j] ^= gf_mul(coef, db[j])
            shards[k + r].extend(out)
    # metadata
    meta = {
        "k": k, "n": n, "shard_size": shard_size,
        "orig_len": total, "pad": pad,
        "systematic": True,
        "parity_matrix": [[c for c in row] for row in V],  # for decoder
    }
    return [bytes(s) for s in shards], meta

def decode(shard_payloads, shard_indices, meta):
    # shard_payloads: list of bytes for available shards (length >= k)
    # shard_indices: which shard index (0..n-1) for each payload
    k = meta["k"]; n = meta["n"]; size = meta["shard_size"]
    assert len(shard_payloads) == len(shard_indices)
    assert len(shard_payloads) >= k
    V = meta["parity_matrix"]  # (n-k)×k
    # Build generator rows for the provided indices
    # For systematic: rows 0..k-1 are identity; rows k..n-1 are V rows
    A = []
    for idx in shard_indices:
        if idx < k:
            row = [0]*k; row[idx] = 1
        else:
            row = V[idx - k][:]
        A.append(row)
    # Invert top-k rows of A that correspond to the first k provided shards
    # We need exactly k rows to form a square matrix; take the first k.
    A_k = A[:k]
    invA = gf_mat_inv(A_k)
    # Prepare Y matrix (k × bytes) from first k shard payloads
    # We'll reconstruct k data shards by: D = invA * Y
    y = [bytearray(shard_payloads[i][:]) for i in range(k)]
    # multiply in GF for each byte position
    out_data = [bytearray(len(y[0])) for _ in range(k)]
    for j in range(len(y[0])):
        col = [y_i[j] for y_i in y]  # length k
        # compute invA * col
        for r in range(k):
            acc = 0
            row = invA[r]
            for c in range(k):
                if row[c]==0: continue
                if row[c]==1:
                    acc ^= col[c]
                else:
                    acc ^= gf_mul(row[c], col[c])
            out_data[r][j] = acc
    # Now out_data are the original k data shards (concatenated across blocks)
    # Trim to original length
    data_concat = b"".join(bytes(b) for b in out_data)
    total = meta["orig_len"]
    return data_concat[:total]
