"""Shared design parameters (cm) for the hall coat-rack proposal: wall LEFT of the window, no bench.

Coordinates: X along the back wall (X=0 at the corner with the right wall, negative towards the
window and the entrance-door wall), Y up from the floor, Z out of the back wall into the hall.
Measured on site: ceiling 270, wall between corner and window opening 55.0, window opening top
231.5 (38.5 below the ceiling), baseboard 8.0 high x 1.6 thick, brick wall, entrance door opens
90 degrees towards the window wall. The panel stands on the baseboard (which stays uncut): it must
not reach below the baseboard top.
Values marked "est." come from the calibrated photo and still deserve a check with the tape.
"""

SITE = dict(
    ceiling=270.0,
    window_x=(-116.0, -65.4),       # est. (opening width ~50.6)
    wall_w=55.0,
    window_top=231.5,
    sill_top=39.2,                  # est.
    sill_protrusion=3.0,            # est.
    baseboard_h=8.0,
    baseboard_t=1.6,
    wall_material="cărămidă",
    # entrance door in the left wall (hinges on the back-wall side, opens 90 deg into the hall)
    entry_open_z=(30.5, 113.3),     # est.
    entry_reveal_d=18.3,            # est.
    entry_head=194.0,               # est.
    entry_leaf_w=76.0,              # est.
    entry_leaf_t=6.0,
    entry_hinge_z=34.5,             # est.
    entry_handle=(6.0, 102.0, 6.5),  # est.: from free edge, height, projection
)
SITE["left_wall_x"] = SITE["window_x"][0] - SITE["wall_w"]

D = dict(
    n_slats=11, pitch=4.0, slat_w=2.7, slat_t=1.2, felt_t=0.9,
    hooks_up_y=178.0, hooks_up_slats=[2, 5, 8],
    hooks_lo_y=150.0, hooks_lo_slats=[3, 7],
    hook_r=1.1, hook_len=7.0, hook_tilt_deg=8.0,
    coat_depth=25.0,
)
D["panel_w"] = D["n_slats"] * D["pitch"]
ZF = D["felt_t"]
ZS = ZF + D["slat_t"]
N_SLATS = D["n_slats"]
EDGE = (D["pitch"] - D["slat_w"]) / 2.0
CUTS = []


class Layout:
    """Panel centred between the left wall and the window opening, top level with the window head,
    bottom resting on the top edge of the (uncut) baseboard."""

    def __init__(self, left_wall_x, window_x0, top, bottom):
        self.left_wall_x = left_wall_x
        self.window_x0 = window_x0
        self.wall_w = window_x0 - left_wall_x
        self.margin = (self.wall_w - D["panel_w"]) / 2.0
        self.x0 = left_wall_x + self.margin
        self.x1 = self.x0 + D["panel_w"]
        self.top = top
        self.bottom = bottom
        self.height = top - bottom

    def slat_x(self, i):
        a = self.x0 + EDGE + i * D["pitch"]
        return a, a + D["slat_w"]

    def slat_center(self, i):
        a, b = self.slat_x(i)
        return 0.5 * (a + b)

    def hooks(self):
        return ([(self.slat_center(i), D["hooks_up_y"]) for i in D["hooks_up_slats"]]
                + [(self.slat_center(i), D["hooks_lo_y"]) for i in D["hooks_lo_slats"]])


LAYOUT = Layout(SITE["left_wall_x"], SITE["window_x"][0], SITE["window_top"], SITE["baseboard_h"])
MARGIN = LAYOUT.margin
X0, X1 = LAYOUT.x0, LAYOUT.x1
D["panel_top"] = LAYOUT.top
D["panel_bottom"] = LAYOUT.bottom
D["panel_h"] = LAYOUT.height
slat_x = LAYOUT.slat_x
slat_center = LAYOUT.slat_center
hooks = LAYOUT.hooks


def entry_door():
    """Entrance-door geometry in plan (X, Z): hinge axis, leaf width and the 90-degree open position."""
    hx = SITE["left_wall_x"] - SITE["entry_reveal_d"] + SITE["entry_leaf_t"]
    hz = SITE["entry_hinge_z"]
    w = SITE["entry_leaf_w"]
    return dict(hinge=(hx, hz), w=w, t=SITE["entry_leaf_t"],
                open_face_z=hz, free_end_x=hx + w,
                handle_x=hx + w - SITE["entry_handle"][0], handle_y=SITE["entry_handle"][1],
                handle_z=hz - SITE["entry_handle"][2])
