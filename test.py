import math
import minescript as ms
import time, random

player = ms.get_player()

iy = player.yaw
ip = player.pitch

def view_change_random_smooth(ty, tp):
    change_distance_yaw = ty - iy
    change_distance_pitch = tp - ip
    change_quantity = random.randint(10,20)

    change_factor_yaw = change_distance_yaw/change_quantity
    change_factor_pitch = change_distance_pitch/change_quantity

    for x in range(change_quantity):
        player = ms.get_player()
        ms.player_set_orientation(player.yaw + change_factor_yaw, player.pitch + change_factor_pitch)

def attack(x):
    ms.player_press_attack(x)

def movement(cycles):
    for i in range(cycles):
            
        x, y, z = ms.player_position()
        z_increment = 91
        x_increment = 5

        iz = z+z_increment
        while z < iz:
            ms.player_press_right(True)
            x, y, z = ms.player_position()
        else:
            ms.player_press_right(False)

        ix = math.floor(x+x_increment)

        while x < ix:
            ms.player_press_forward(True)
            x, y, z = ms.player_position()
        else:
            ms.player_press_forward(False)

        iz_left= z-z_increment

        while iz_left < z:
            ms.player_press_left(True)
            x, y, z = ms.player_position()
        else:
            ms.player_press_left(False)

        ix = math.floor(x+x_increment)

        while x < ix:
            ms.player_press_forward(True)
            x, y, z = ms.player_position()
        else:
            ms.player_press_forward(False)

    x, y, z = ms.player_position()

view_change_random_smooth(-90, 62)
# attack(False)
# movement(9)
# attack(False)