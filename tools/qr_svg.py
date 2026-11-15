# Writes a QR code as a small inline SVG, standard library only (byte mode, error correction level M, versions 1 to 6).
# Used for the talk deck's link to the repo (docs/talk/slides.html). Follows ISO/IEC 18004: Reed-Solomon over GF(256)
# (0x11D), finder, timing and alignment patterns, zigzag placement, the 8 masks scored by the 4 penalty rules, and BCH
# format bits. Version information (versions 7+) is not needed for short URLs and not implemented.
# usage: python3 -I tools/qr_svg.py <text> [--dark #000] [--module 10] > out.svg
import sys

# version: (data codewords, EC codewords per block, blocks) at level M; alignment centres
SPEC = {1: (16, 10, 1), 2: (28, 16, 1), 3: (44, 26, 1), 4: (64, 18, 2), 5: (86, 24, 2), 6: (108, 16, 4)}
ALIGN = {1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30], 6: [6, 34]}

EXP, LOG = [0] * 512, [0] * 256
x = 1
for i in range(255):
    EXP[i] = x; LOG[x] = i; x <<= 1
    if x & 0x100: x ^= 0x11D
for i in range(255, 512): EXP[i] = EXP[i - 255]

def gmul(a, b): return 0 if a == 0 or b == 0 else EXP[LOG[a] + LOG[b]]

def rs_ec(data, n):
    gen = [1]
    for i in range(n):  # multiply by (x - a^i)
        gen = [a ^ gmul(b, EXP[i]) for a, b in zip(gen + [0], [0] + gen)]
    rem = [0] * n
    for d in data:
        f = d ^ rem[0]; rem = rem[1:] + [0]
        for j in range(n): rem[j] ^= gmul(gen[j + 1], f)
    return rem

def codewords(text):
    b = text.encode('utf-8')
    for v, (dc, ecn, blocks) in SPEC.items():
        if 4 + 8 + 8 * len(b) <= dc * 8: break
    else: raise SystemExit('text too long for versions 1 to 6')
    bits = '0100' + format(len(b), '08b') + ''.join(format(c, '08b') for c in b)
    bits += '0' * min(4, dc * 8 - len(bits)); bits += '0' * (-len(bits) % 8)
    data = [int(bits[i:i + 8], 2) for i in range(0, len(bits), 8)]
    pad = [0xEC, 0x11]; i = 0
    while len(data) < dc: data.append(pad[i % 2]); i += 1
    size = dc // blocks
    blks = [data[k * size:(k + 1) * size] for k in range(blocks)]   # equal block sizes for these versions at level M
    ecs = [rs_ec(bl, ecn) for bl in blks]
    out = [bl[i] for i in range(size) for bl in blks] + [e[i] for i in range(ecn) for e in ecs]
    return v, out

def build(text):
    v, cw = codewords(text)
    n = 17 + 4 * v
    m = [[None] * n for _ in range(n)]; fn = [[False] * n for _ in range(n)]
    def setf(r, c, val): m[r][c] = val; fn[r][c] = True
    for (r0, c0) in ((0, 0), (0, n - 7), (n - 7, 0)):          # finders with separators
        for r in range(-1, 8):
            for c in range(-1, 8):
                rr, cc = r0 + r, c0 + c
                if 0 <= rr < n and 0 <= cc < n:
                    d = max(abs(r - 3), abs(c - 3))
                    setf(rr, cc, d != 2 and d != 4)
    for i in range(n):                                          # timing
        if not fn[6][i]: setf(6, i, i % 2 == 0)
        if not fn[i][6]: setf(i, 6, i % 2 == 0)
    a = ALIGN[v]
    for r in a:                                                 # alignment
        for c in a:
            if fn[r][c]: continue
            for dr in range(-2, 3):
                for dc in range(-2, 3): setf(r + dr, c + dc, max(abs(dr), abs(dc)) != 1)
    for i in range(9):                                          # reserve format areas
        for (r, c) in ((8, i), (i, 8)):
            if not fn[r][c]: setf(r, c, False)
    for i in range(8):
        setf(8, n - 1 - i, False); setf(n - 1 - i, 8, False)
    setf(n - 8, 8, True)                                        # dark module
    bits = ''.join(format(c, '08b') for c in cw)
    k = 0; col = n - 1
    while col > 0:                                              # zigzag placement, two columns at a time
        if col == 6: col -= 1                                   # skip the vertical timing column
        up = ((col + 1) & 2) == 0
        rows = range(n - 1, -1, -1) if up else range(n)
        for r in rows:
            for c in (col, col - 1):
                if not fn[r][c]:
                    m[r][c] = k < len(bits) and bits[k] == '1'; k += 1
        col -= 2
    MASKS = [lambda r, c: (r + c) % 2 == 0, lambda r, c: r % 2 == 0, lambda r, c: c % 3 == 0, lambda r, c: (r + c) % 3 == 0,
             lambda r, c: (r // 2 + c // 3) % 2 == 0, lambda r, c: (r * c) % 2 + (r * c) % 3 == 0,
             lambda r, c: ((r * c) % 2 + (r * c) % 3) % 2 == 0, lambda r, c: ((r + c) % 2 + (r * c) % 3) % 2 == 0]
    def fmt_bits(mask):
        d = (0b00 << 3) | mask                                  # level M = 00
        rem = d
        for _ in range(10): rem = (rem << 1) ^ ((rem >> 9) * 0x537)
        return ((d << 10) | rem) ^ 0x5412
    def apply(mask):
        g = [[(m[r][c] ^ MASKS[mask](r, c)) if not fn[r][c] else m[r][c] for c in range(n)] for r in range(n)]
        f = fmt_bits(mask)
        bit = lambda i: (f >> i) & 1 == 1
        for i in range(6): g[i][8] = bit(i)                     # g[row][col]; first copy around the top-left finder
        g[7][8] = bit(6); g[8][8] = bit(7); g[8][7] = bit(8)
        for i in range(9, 15): g[8][14 - i] = bit(i)
        for i in range(8): g[8][n - 1 - i] = bit(i)             # second copy: top-right and bottom-left
        for i in range(8, 15): g[n - 15 + i][8] = bit(i)
        g[n - 8][8] = True
        return g
    def penalty(g):
        p = 0
        for lines in (g, list(zip(*g))):
            for line in lines:
                run = 1
                for i in range(1, n):
                    if line[i] == line[i - 1]: run += 1
                    else:
                        if run >= 5: p += run - 2
                        run = 1
                if run >= 5: p += run - 2
                s = ''.join('1' if x else '0' for x in line)
                p += 40 * (s.count('10111010000') + s.count('00001011101'))
        for r in range(n - 1):
            for c in range(n - 1):
                if g[r][c] == g[r][c + 1] == g[r + 1][c] == g[r + 1][c + 1]: p += 3
        dark = sum(map(sum, g)); p += 10 * (abs(dark * 20 - n * n * 10) // (n * n))
        return p
    return min((apply(k) for k in range(8)), key=penalty)

def svg(text, dark='#000', module=10, border=4):
    g = build(text); n = len(g); size = (n + 2 * border) * module
    path = ''.join(f'M{(c + border) * module} {(r + border) * module}h{module}v{module}h-{module}z'
                   for r in range(n) for c in range(n) if g[r][c])
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}" '
            f'role="img" aria-label="QR code: {text}" shape-rendering="crispEdges">'
            f'<rect width="{size}" height="{size}" fill="#fff"/><path d="{path}" fill="{dark}"/></svg>')

if __name__ == '__main__':
    a = sys.argv[1:]
    if not a: sys.exit('usage: qr_svg.py <text> [--dark #000] [--module 10]')
    opt = lambda k, d: a[a.index(k) + 1] if k in a else d
    print(svg(a[0], opt('--dark', '#000'), int(opt('--module', '10'))))
