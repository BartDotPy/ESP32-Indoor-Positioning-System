import numpy as np

def rssi_to_distance(rssi, A, n):
    if rssi == 0:
        return None
    return 10**((A - rssi) / (10*n))

def trilaterate(beacons, distances):
    x1, y1 = beacons["BEACON_1"]
    x2, y2 = beacons["BEACON_2"]
    x3, y3 = beacons["BEACON_3"]

    d1, d2, d3 = distances

    A_mat = np.array([
        [2*(x2 - x1), 2*(y2 - y1)],
        [2*(x3 - x2), 2*(y3 - y2)]
    ])
    
    b_mat = np.array([
        [x2**2 + y2**2 - d2**2 - x1**2 - y1**2 + d1**2],
        [x3**2 + y3**2 - d3**2 - x2**2 - y2**2 + d2**2]
    ])

    try:
        # Rozwiązanie układu (x, y)
        pos = np.linalg.solve(A_mat, b_mat)
        return float(pos[0]), float(pos[1])
    except np.linalg.LinAlgError:
        return None