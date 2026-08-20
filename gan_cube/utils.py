import time

def now():
    return int(time.time() * 1000)

CORNER_FACELET_MAP = [
    [8, 9, 20],   # URF
    [6, 18, 38],  # UFL
    [0, 36, 47],  # ULB
    [2, 45, 11],  # UBR
    [29, 26, 15], # DFR
    [27, 44, 24], # DLF
    [33, 53, 42], # DBL
    [35, 17, 51]  # DRB
]

EDGE_FACELET_MAP = [
    [5, 10],  # UR
    [7, 19],  # UF
    [3, 37],  # UL
    [1, 46],  # UB
    [32, 16], # DR
    [28, 25], # DF
    [30, 43], # DL
    [34, 52], # DB
    [23, 12], # FR
    [21, 41], # FL
    [50, 39], # BL
    [48, 14]  # BR
]

def to_kociemba_facelets(cp, co, ep, eo):
    faces = "URFDLB"
    facelets = list("".join([f * 9 for f in faces]))
    
    # Kociemba order: U1-U9, R1-R9, F1-F9, D1-D9, L1-L9, B1-B9
    # Indices: 0-8 (U), 9-17 (R), 18-26 (F), 27-35 (D), 36-44 (L), 45-53 (B)
    
    for i in range(8):
        # CORNER_FACELET_MAP[i] is the list of facelet indices for corner at position i
        # cp[i] is the corner piece currently at position i
        # co[i] is the orientation of that piece
        # Pieces are also indexed by their home position.
        # Home facelets for corner i are CORNER_FACELET_MAP[i]
        for p in range(3):
            # The facelet at CORNER_FACELET_MAP[i][(p + co[i]) % 3]
            # should get the color of the p-th facelet of corner cp[i] in its home position.
            target_facelet_idx = CORNER_FACELET_MAP[i][(p + co[i]) % 3]
            if cp[i] < len(CORNER_FACELET_MAP):
                source_facelet_idx = CORNER_FACELET_MAP[cp[i]][p]
                facelets[target_facelet_idx] = faces[source_facelet_idx // 9]
            else:
                facelets[target_facelet_idx] = "?"
            
    for i in range(12):
        for p in range(2):
            target_facelet_idx = EDGE_FACELET_MAP[i][(p + eo[i]) % 2]
            if ep[i] < len(EDGE_FACELET_MAP):
                source_facelet_idx = EDGE_FACELET_MAP[ep[i]][p]
                facelets[target_facelet_idx] = faces[source_facelet_idx // 9]
            else:
                facelets[target_facelet_idx] = "?"
            
    return "".join(facelets)
