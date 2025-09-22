import matplotlib.pyplot as plt
import numpy as np

# Prepare quadrant grid for visualization
fig, ax = plt.subplots(figsize=(6,6))

# Draw grid lines to represent block boundaries
for i in range(-5, 6):
    ax.axhline(i, color="lightgrey", linewidth=0.5)
    ax.axvline(i, color="lightgrey", linewidth=0.5)

# Highlight axes
ax.axhline(0, color="black", linewidth=1)
ax.axvline(0, color="black", linewidth=1)

# Example player positions in each quadrant
positions = [
    (2.7, 2.3),   # +/+ quadrant
    (-2.7, 2.3),  # -/+ quadrant
    (-2.7, -2.3), # -/- quadrant
    (2.7, -2.3)   # +/- quadrant
]

for (x, z) in positions:
    # int() truncation (toward zero)
    trunc = (int(x), int(z))
    # floor() correct block placement
    floored = (np.floor(x), np.floor(z))
    
    # Plot player position
    ax.plot(x, z, "bo", label="Player" if (x,z)==positions[0] else "")
    # Plot int() placement
    ax.plot(trunc[0], trunc[1], "rx", markersize=10, label="int() result" if (x,z)==positions[0] else "")
    # Plot floor() placement
    ax.plot(floored[0], floored[1], "g+", markersize=10, label="floor() result" if (x,z)==positions[0] else "")
    
    # Annotate
    ax.text(x+0.1, z+0.1, f"({x:.1f},{z:.1f})", fontsize=8)
    ax.text(trunc[0]+0.1, trunc[1]+0.1, f"int={trunc}", fontsize=7, color="red")
    ax.text(floored[0]+0.1, floored[1]+0.1, f"floor={floored}", fontsize=7, color="green")

ax.set_title("Minecraft Quadrants: int() vs floor()")
ax.set_xlim(-5,5)
ax.set_ylim(-5,5)
ax.set_aspect("equal")
ax.legend()

plt.show()
