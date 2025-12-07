import numpy as np

# Partially AI generated. Too much boilerplate...

def distance_point_to_segment(P, V1, V2):
    """
    Calculates the minimum distance from point P to the line segment V1-V2.
    
    Assumes segment V1-V2 is axis-aligned (strictly horizontal or vertical).
    
    P, V1, V2 are 2-element NumPy arrays (x, y).
    """
    P = np.array(P)
    V1 = np.array(V1)
    V2 = np.array(V2)
    
    # 1. Check if the segment is horizontal or vertical
    is_horizontal = V1[1] == V2[1]
    
    if is_horizontal:
        # Segment S is horizontal (y = V1[1])
        S_y = V1[1]
        
        # Get the min/max x-coordinates of the segment
        S_x_min = min(V1[0], V2[0])
        S_x_max = max(V1[0], V2[0])
        
        # Check if the projection of P is ON the segment (x-range)
        if S_x_min <= P[0] <= S_x_max:
            # The closest point is (P[0], S_y). Distance is the vertical difference.
            return abs(P[1] - S_y)
        else:
            # The closest point is an endpoint. Return the shorter distance to V1 or V2.
            dist_to_V1 = np.linalg.norm(P - V1)
            dist_to_V2 = np.linalg.norm(P - V2)
            return min(dist_to_V1, dist_to_V2)
            
    else:
        # Segment S is vertical (x = V1[0])
        S_x = V1[0]

        # Get the min/max y-coordinates of the segment
        S_y_min = min(V1[1], V2[1])
        S_y_max = max(V1[1], V2[1])

        # Check if the projection of P is ON the segment (y-range)
        if S_y_min <= P[1] <= S_y_max:
            # The closest point is (S_x, P[1]). Distance is the horizontal difference.
            return abs(P[0] - S_x)
        else:
            # The closest point is an endpoint.
            dist_to_V1 = np.linalg.norm(P - V1)
            dist_to_V2 = np.linalg.norm(P - V2)
            return min(dist_to_V1, dist_to_V2)

# This function calculates the minimum distance between two line segments from our detected speech bubbles.
# In most cases, the actual logic would be FAR more complicated, but our speech bubbles are parallel.
# "parallel" as in we only compare left edge of I to right edge of J, top of edge of I ot bottom edge of J, etc.
def distance_segment_to_segment(I_A, I_B, J_C, J_D):
    """
    Calculates the minimum distance between segment I (A to B) and segment J (C to D).
    
    This uses the 4-check method which is robust for axis-aligned segments.
    I_A, I_B, J_C, J_D are points (x, y) defining the segment endpoints.
    """
    
    # Check 1: Distance from endpoints of I to segment J
    d1 = distance_point_to_segment(I_A, J_C, J_D)
    d2 = distance_point_to_segment(I_B, J_C, J_D)
    
    # Check 2: Distance from endpoints of J to segment I
    d3 = distance_point_to_segment(J_C, I_A, I_B)
    d4 = distance_point_to_segment(J_D, I_A, I_B)
    
    # The minimum of these 4 checks is the shortest distance between the segments.
    # This covers endpoint-to-segment interior and endpoint-to-endpoint cases.
    return min(d1, d2, d3, d4)