"""Reader for old Stata .dta files (formats 105-115) that pandas refuses (e.g. format 110, 'Written by R.').

Layout (Stata dta documentation, formats 110/111/113-115): 109-byte header, typlist (1 byte per variable),
varlist (33 bytes), srtlist (2 bytes x (nvar + 1)), fmtlist (12 bytes, 49 from 114), lbllist (33 bytes),
variable labels (81 bytes), expansion fields (5-byte type/length records ending with type 0), then fixed-width rows.
Type codes: formats 111+: 1-244 strN, 251 byte, 252 int, 253 long, 254 float, 255 double;
formats <= 110: 127 + N for strN, ASCII b/i/l/f/d for numerics.
"""
import struct

import numpy as np
import pandas as pd

NUM = {251: ('b', 1), 252: ('h', 2), 253: ('i', 4), 254: ('f', 4), 255: ('d', 8)}
OLD_NUM = {ord('b'): 251, ord('i'): 252, ord('l'): 253, ord('f'): 254, ord('d'): 255}


def read_old_dta(path):
    b = open(path, 'rb').read()
    fmt = b[0]
    assert 105 <= fmt <= 115, f'format {fmt} is not an old-format dta'
    bo = '<' if b[1] == 2 else '>'
    nvar = struct.unpack(bo + 'H', b[4:6])[0]
    nobs = struct.unpack(bo + 'I', b[6:10])[0]
    pos = 10 + 81 + 18
    typ = list(b[pos:pos + nvar]); pos += nvar
    if fmt <= 110:   # old type codes -> 111+ codes
        typ = [t - 127 if t > 127 else OLD_NUM[t] for t in typ]
    names = [b[pos + 33 * i:pos + 33 * (i + 1)].split(b'\0')[0].decode('latin-1') for i in range(nvar)]
    pos += 33 * nvar + 2 * (nvar + 1)
    pos += (49 if fmt >= 114 else 12) * nvar
    pos += 33 * nvar + 81 * nvar
    while True:                                   # expansion fields
        t, n = b[pos], struct.unpack(bo + 'I', b[pos + 1:pos + 5])[0]
        pos += 5
        if t == 0 and n == 0:
            break
        pos += n
    widths = [t if t <= 244 else NUM[t][1] for t in typ]
    rw = sum(widths)
    assert len(b) - pos >= rw * nobs, 'data block shorter than declared rows'
    data = {}
    rows = np.frombuffer(b[pos:pos + rw * nobs], dtype=np.uint8).reshape(nobs, rw)
    start = 0
    for name, t, w in zip(names, typ, widths):
        chunk = rows[:, start:start + w]
        if t <= 244:
            data[name] = [bytes(r).split(b'\0')[0].decode('latin-1') for r in chunk]
        else:
            data[name] = np.frombuffer(chunk.tobytes(), dtype=np.dtype(bo + NUM[t][0]))
        start += w
    meta = {'format': fmt, 'nvar': nvar, 'nobs': nobs, 'types': typ, 'data_offset': pos, 'row_width': rw,
            'trailing_bytes': len(b) - pos - rw * nobs,
            'data_label': b[10:91].split(b'\0')[0].decode('latin-1')}
    return pd.DataFrame(data), meta


def read_any_dta(path):
    """pandas for formats it supports, the reader above for the rest."""
    fmt = open(path, 'rb').read(1)[0]
    if 105 <= fmt <= 115 and fmt not in (111, 113, 114, 115):
        return read_old_dta(path)
    df = pd.read_stata(path, convert_categoricals=False)
    return df, {'format': fmt if fmt < 200 else 'xml (117+)', 'nobs': len(df), 'nvar': df.shape[1]}
