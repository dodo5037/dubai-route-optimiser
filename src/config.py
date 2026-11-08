"""All assumptions for the Dubai last-mile routing model live here.

IMPORTANT: the delivery points are SYNTHETIC. Neighbourhood centres are approximate
public coordinates; each day's customers are placed randomly around them. Road distance
is estimated from straight-line (haversine) distance times a circuity factor, and travel
time from an average urban speed. These are stated assumptions, not real customer data.
"""

# Depot: a last-mile delivery station in Al Quoz Industrial Area (approximate)
DEPOT = ("Al Quoz depot", 25.1350, 55.2300)

# (name, lat, lon, relative demand weight)
NEIGHBOURHOODS = [
    ("Dubai Marina", 25.0805, 55.1403, 3),
    ("JLT", 25.0693, 55.1440, 2),
    ("JVC", 25.0580, 55.2090, 3),
    ("Al Barsha", 25.1130, 55.1980, 3),
    ("Arabian Ranches", 25.0550, 55.2680, 1),
    ("Jumeirah", 25.2050, 55.2400, 2),
    ("Downtown", 25.1970, 55.2740, 2),
    ("Business Bay", 25.1860, 55.2630, 2),
    ("Bur Dubai", 25.2540, 55.2970, 2),
    ("Deira", 25.2710, 55.3070, 3),
    ("Al Nahda", 25.2900, 55.3700, 2),
    ("Mirdif", 25.2190, 55.4200, 2),
    ("International City", 25.1650, 55.4080, 2),
    ("Silicon Oasis", 25.1180, 55.3830, 2),
]
SCATTER_KM = 1.2            # customers spread around each neighbourhood centre (std dev, km)

# Road and time assumptions
CIRCUITY = 1.35             # road km per straight-line km (urban networks are typically ~1.2-1.4)
SPEED_KMH = 32.0            # average van speed including traffic and lights (assumption)
SERVICE_MIN_PER_STOP = 4.0  # park, walk, hand over
SERVICE_MIN_PER_PARCEL = 0.5

# Shift: minute 0 = 09:00
SHIFT_END_MIN = 510         # vans must be back by 17:30
WINDOWS = [(0, 120), (120, 240), (240, 360), (360, 480)]  # 09-11, 11-13, 13-15, 15-17
SHARE_WITH_WINDOW = 0.6     # 60% of customers choose a 2-hour window, the rest accept any time

# Fleet
VAN_CAPACITY = 40           # parcels
MAX_VANS = 10
PARCELS_PER_STOP = (1, 3)   # uniform integer range

# Experiment
STOPS_PER_DAY = 60
DAYS = 20                   # 20 random days
SENSITIVITY_STOPS = [40, 80]
SENSITIVITY_DAYS = 5
SOLVER_SECONDS = 10
