import numpy as np

def cardinal_spline(control_points, t):
    control_points = [control_points[1]] + control_points + [control_points[-2]]

    def catmull_rom(P0, P1, P2, P3, T):

        P0 = np.array(P0)
        P1 = np.array(P1)
        P2 = np.array(P2)
        P3 = np.array(P3)

        return (
            T * ((2 - T) * T - 1) * P0
            + (T * T * (3 * T - 5) + 2) * P1
            + T * ((4 - 3 * T) * T + 1) * P2
            + (T - 1) * T * T * P3) / 2

    segment = int(t * (len(control_points) - 3))
    print("Segment: (" + str(segment) + ", " + str(segment + 3) + ")  |  t: " + str(t))
    t = (t * (len(control_points) - 3)) - segment
    p0, p1, p2, p3 = control_points[segment:segment+4]

    return catmull_rom(p0, p1, p2, p3, t)

import numpy as np


points = [(0,), (1,), (2,), (3,), (4,), (5,), (6,), (7,), (8,), (9,)]

segment = int(t * (len(points) - 3))

for i in range(100):
    t = i/100
    cardinal_spline(points, t)