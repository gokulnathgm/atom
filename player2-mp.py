from socketIO_client import SocketIO
from sympy.geometry import *
from sympy import sympify
import random
import math
from socketIO_client import BaseNamespace
import threading as th
import multiprocessing as mp
from multiprocessing import Manager

class Namespace(BaseNamespace):
    def on_connect(self):
        print '[Connected]'

    def on_disconnect(self):
    	print '[Disconnected]'

socketIO = SocketIO('10.7.90.8', 4000, Namespace)
print socketIO.connected

player1Key = 'T8uhv56xvs'
player2Key = 'GSwwserRd2'
gameKey = '9lVRq6Py7a3Vl1I0c4Fm'

striker_x = 846.7742
striker_y = 194

pocket4_x = 967.7419
pocket4_y = 967.7419
pocket3_x = 32.2581
pocket3_y = 967.7419
pocket2_x = 967.7419
pocket2_y = 32.2581
pocket1_x = 32.2581
pocket1_y = 32.2581

pocket4_point = (pocket4_x, pocket4_y)
pocket3_point = (pocket3_x, pocket3_y)
pocket2_point = (pocket2_x, pocket2_y)
pocket1_point = (pocket1_x, pocket1_y)
striker_point = (striker_x, striker_y)

pocket3_results = []
pocket1_results = []

def dot(vA, vB):
    return vA[0] * vB[0] + vA[1] * vB[1]

def ang(lineA, lineB):
    vA = [(lineA[0][0] - lineA[1][0]), (lineA[0][1] - lineA[1][1])]
    vB = [(lineB[0][0] - lineB[1][0]), (lineB[0][1] - lineB[1][1])]
    dot_prod = dot(vA, vB)
    magA = dot(vA, vA) ** 0.5
    magB = dot(vB, vB) ** 0.5
    angle = math.acos(dot_prod / magB / magA)
    ang_deg = math.degrees(angle) % 360
    if ang_deg - 180 >= 0:
        return 360 - ang_deg
    else: 
        return ang_deg

def distance_between_points(point1, point2):
	x1, y1 = point1[0], point1[1]
	x2, y2 = point2[0], point2[1]
	distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
	return distance

def clean_strikes(coins, destination_point, positions, radius_total, check):
	strike_through = []
	for coin in coins:
		if check == False and coin['type'] == 'stricker':
			continue

		coin_x = coin['x']
		coin_y = coin['y']
		coin_point = (coin_x, coin_y)
		line_coin_pocket = Line(coin_point, destination_point)
		distance_coin_pocket = distance_between_points(coin_point, destination_point)
		path = True
		for coin_subset in positions:
			if coin_subset['type'] == 'stricker':
				continue
			coin_subset_x = coin_subset['x']
			coin_subset_y = coin_subset['y']

			coin_subset_point = (coin_subset_x, coin_subset_y)
			distance_subset_coin_pocket = distance_between_points(coin_subset_point, destination_point)
			distance_between_coins = distance_between_points(coin_point, coin_subset_point)
			if(distance_coin_pocket > distance_between_coins and distance_coin_pocket > distance_subset_coin_pocket):
				if float(line_coin_pocket.perpendicular_segment(coin_subset_point).length) < radius_total:
					path = False
					break
		if path:
			if check:
				coin = {'x': coin['x1'], 'y': coin['y1'], 'type': coin['type']}
				strike_through.append(coin)
			else:
				strike_through.append(coin)

	return strike_through

def emit_response(*args):
	print 'Emit response'
	print args, '\n'

def connection_response(*args):
	print 'connection_response'
	print args, '\n'

def coin_positions(*args):
	positions = args[0]['position']
	positions = args[0]['position']
	number_of_coins = len(positions)
	print 'Number of coins = ', number_of_coins, '\n'

	black = []
	white = []
	red = []
	for coin in positions:
		if coin['type'] == 'black':
			black.append(coin)
		if coin['type'] == 'white':
			white.append(coin)
		if coin['type'] == 'red':
			red.append(coin)
	positions = []
	positions.extend(red)
	positions.extend(white)
	positions.extend(black)

	manager = Manager()
	return_dict = manager.dict()

	q = mp.Queue()
	job1 = mp.Process(target=coin_positions3, args=(args, return_dict))
	job2 = mp.Process(target=coin_positions1, args=(args, return_dict))
	job1.start()
	job2.start()
	job1.join()
	job2.join()

	print 'results3', return_dict['pocket3'], '\n' 
	print 'results1', return_dict['pocket1'], '\n'

	result = return_dict['pocket3']
	result.extend(return_dict['pocket1'])

	black = []
	white = []
	red = []
	large = 140
	for coin in result:
		if coin['type'] == 'black':
			black.append(coin)
			if coin['angle_mutual'] > large:
				large = coin['angle_mutual']
				angle = coin['angle']
				position = coin['position']
				force = coin['force']
		if coin['type'] == 'white':
			white.append(coin)
			if coin['angle_mutual'] > large:
				large = coin['angle_mutual']
				angle = coin['angle']
				position = coin['position']
				force = coin['force']
		if coin['type'] == 'red':
			red.append(coin)
			if coin['angle_mutual'] > large:
				large, angle = coin['angle_mutual'], coin['angle_mutual']
				position = coin['position']
				force = coin['force']

	red = sorted(red, key=lambda k: k['angle'], reverse=True) 
	white = sorted(white, key=lambda k: k['angle'], reverse=True) 
	black = sorted(black, key=lambda k: k['angle'], reverse=True) 
	print red
	print white
	print black

	if red:
		angle = red[0]['angle']
		force = red[0]['force']
		position = red[0]['position']
	elif white:
		angle = white[0]['angle']
		force = white[0]['force']
		position = white[0]['position']

	elif black:
		angle = black[0]['angle']
		force = black[0]['force']
		position = black[0]['position']

	if not result:
		print '\nlooking for a reverse/straight shot\n'
		striker_positions = []
		for i in range(194,806,10):
			valid_position = True
			for j in positions:
				j_x = j['x']
				j_y = j['y']
				if (j_x > 792 and j_x < 902) and (j_y > i - 55 and j_y < i + 55):
					valid_position = False
					break
			if valid_position:
				striker_positions.append(i)
		print 'valid positions: ', striker_positions, '\n'
		coin_to_strike = positions[0]
		coin_y = coin_to_strike['y']
		coin_x = coin_to_strike['x']
		coin = (coin_x, coin_y)
		if coin_to_strike['x'] > 796:
			print 'Attempting reverse shot on: ', coin_to_strike, '\n'
			if coin_y > 500:
				striker_y = striker_positions[len(striker_positions) - 1]
			else:
				striker_y = striker_positions[0]

			striker_point = (striker_x, striker_y)
			mid_point = (striker_y + coin_y) / 2
			point_mid_point = (0, mid_point)
			line_coin_mid_point = Line(striker_point, point_mid_point)
			slope_coin_mid_point = line_coin_mid_point.slope
			angle = math.degrees(math.atan(slope_coin_mid_point))
			#angle += 2
			force = 3000
			position = striker_y
		else:
			print 'Attempting straight shot on: ', coin_to_strike, '\n'
			if coin_y > 500:
				striker_y = striker_positions[len(striker_positions) - 1]
			else:
				striker_y = striker_positions[0]
			striker_point = (striker_x, striker_y)
			line_coin_striker = Line(coin, striker_point)
			slope_coin_striker = line_coin_striker.slope
			angle = math.degrees(math.atan(slope_coin_striker))
			force = 3000
			position = striker_y
		angle += 90


	print {'position': position, 'force': force, 'angle': angle}, '\n'
	socketIO.emit('player_input', {'position': position, 'force': force, 'angle': angle})



def coin_positions3(args, return_dict):
	pocket3_results = []
	print 'coin positions'
	print args, '\n'
	angle = 0

	positions = args[0]['position']
	number_of_coins = len(positions)
	print 'Number of coins = ', number_of_coins, '\n'

	black = []
	white = []
	red = []
	for coin in positions:
		if coin['type'] == 'black':
			black.append(coin)
		if coin['type'] == 'white':
			white.append(coin)
		if coin['type'] == 'red':
			red.append(coin)
	positions = []
	positions.extend(red)
	positions.extend(white)
	positions.extend(black)
	
	strike_through_pocket = clean_strikes(positions, pocket3_point, positions, 50, False)
	print 'clean1: ', strike_through_pocket, '\n'

	no_strike = False
	pocket1 = True
	back_strike = False
	pocket3_results = []
	for i in xrange(194, 806, 100):
		striker_ok = True	
		striker_y = i
		striker_point = (striker_x, striker_y)

		for j in positions:
			if j['type'] == 'stricker':
				continue
			x = j['x']
			y = j['y']
			if (x > 792 and x < 902) and (y > striker_y - 55 and y < striker_y + 55):
				striker_ok = False
				break
		if not striker_ok:
			if i == 794:
				no_strike = True
			continue

		strike_through_pocket_modified = []
		for coin in strike_through_pocket:
			coin_x = coin['x']
			coin_y = coin['y']
			if coin_y < 194 + 50 or coin_x > 846 - 50:
				continue
			coin_point = (coin_x, coin_y)
			circle = Circle(coin_point, 55)
			line_coin_pocket = Line(coin_point, pocket3_point)
			intersection_points = circle.intersection(line_coin_pocket)
			intersection_point_x = float(intersection_points[0][0])
			intersection_point_y = float(intersection_points[0][1])
			point = {'x': intersection_point_x, 'y': intersection_point_y, 'x1': coin_x, 'y1': coin_y, 'type': coin['type']}
			strike_through_pocket_modified.append(point)

		strike_through_striker = clean_strikes(strike_through_pocket_modified, striker_point, positions, 55, True)
		print 'clean2: ', strike_through_striker, '\n'

		striked = False
		if strike_through_striker:
			for coin in strike_through_striker:
				#coin = strike_through_striker[len(strike_through_striker)-1]
				coin_x = coin['x']
				coin_y = coin['y']
				print coin
				# if coin_y < 194 + 50 or coin_x < 153 + 50:
				# 	continue
				coin_pocket = ((coin_x, coin_y), (0, 1000))
				coin_striker = ((coin_x, coin_y),(striker_x, striker_y))
				angle_striker_coin_pocket = ang(coin_pocket, coin_striker)
				if angle_striker_coin_pocket < 140:
					print 'Angle b/w striker coin & pocket: ', angle_striker_coin_pocket, '\n'
					continue
				coin_point = (coin_x, coin_y)
				print coin_point
				circle = Circle(coin_point, 55)
				line_coin_pocket = Line(coin_point, pocket3_point)
				intersection_points = circle.intersection(line_coin_pocket)
				intersection_point_x = float(intersection_points[0][0])
				intersection_point_y = float(intersection_points[0][1])
				point = (intersection_point_x, intersection_point_y)
				strike_line = Line(point, striker_point)
				slope = strike_line.slope
				angle = math.degrees(math.atan(slope))
				pocket1 = False
				print 'Angle b/w striker coin & pocket: ', angle_striker_coin_pocket, '\n'
				if angle_striker_coin_pocket >= 175:
					force = 1000
				elif angle_striker_coin_pocket >= 170 and angle_striker_coin_pocket < 175:
						force = 1500
				elif angle_striker_coin_pocket > 120 and angle_striker_coin_pocket < 170:
					force = 2000
				else:
					force = 4000

				angle += 90
				strike = {'angle': angle, 'force': force, 'position': i, 'angle_mutual': angle_striker_coin_pocket, 'type': coin['type']}
				pocket3_results.append(strike)
				striked = True
				break
			if striked:
				break

	return_dict['pocket3'] = pocket3_results


def coin_positions1(args, return_dict):
	pocket1_results = []
	print '.........................Aiming for pocket1.........................' ,'\n'
	positions = args[0]['position']
	number_of_coins = len(positions)
	print 'Number of coins = ', number_of_coins, '\n'

	black = []
	white = []
	red = []
	for coin in positions:
		if coin['type'] == 'black':
			black.append(coin)
		if coin['type'] == 'white':
			white.append(coin)
		if coin['type'] == 'red':
			red.append(coin)
	positions = []
	positions.extend(red)
	positions.extend(white)
	positions.extend(black)
	no_strike = False
	pocket1_results = []
	strike_through_pocket = clean_strikes(positions, pocket1_point, positions, 50, False)
	print 'clean1: ', strike_through_pocket, '\n'

	for i in xrange(806, 194, -100):
		striker_ok = True	
		striker_y = i
		striker_point = (striker_x, striker_y)

		for j in positions:
			if j['type'] == 'stricker':
				continue
			x = j['x']
			y = j['y']
			if (x > 792 and x < 902) and (y > striker_y - 55 and y < striker_y + 55):
				striker_ok = False
				break
		if not striker_ok:
			if i == 206:
				no_strike = True
			back_strike = True
			continue

		strike_through_pocket_modified = []
		for coin in strike_through_pocket:
			coin_x = coin['x']
			coin_y = coin['y']
			if coin_y > 806 - 50 or coin_x > 846 - 50:
				continue
			coin_point = (coin_x, coin_y)
			circle = Circle(coin_point, 55)
			line_coin_pocket = Line(coin_point, pocket1_point)
			intersection_points = circle.intersection(line_coin_pocket)
			intersection_point_x = float(intersection_points[0][0])
			intersection_point_y = float(intersection_points[0][1])
			point = {'x': intersection_point_x, 'y': intersection_point_y, 'x1': coin_x, 'y1': coin_y, 'type': coin['type']}
			strike_through_pocket_modified.append(point)

		strike_through_striker = clean_strikes(strike_through_pocket_modified, striker_point, positions, 55, True)
		print 'clean2: ', strike_through_striker, '\n'

		striked = False
		back_strike = True
		if strike_through_striker:
			for coin in strike_through_striker:
				#coin = strike_through_striker[len(strike_through_striker)-1]
				coin_x = coin['x']
				coin_y = coin['y']
				print coin
				# if coin_y > 806 - 50 or coin_x < 153 + 50:
				# 	continue
				coin_pocket = ((coin_x, coin_y), (0, 0))
				coin_striker = ((coin_x, coin_y),(striker_x, striker_y))
				angle_striker_coin_pocket = ang(coin_pocket, coin_striker)
				if angle_striker_coin_pocket < 140:
					print 'Angle b/w striker coin & pocket: ', angle_striker_coin_pocket, '\n'
					continue
				coin_point = (coin_x, coin_y)
				print coin_point
				circle = Circle(coin_point, 55)
				line_coin_pocket = Line(coin_point, pocket1_point)
				intersection_points = circle.intersection(line_coin_pocket)
				intersection_point_x = float(intersection_points[0][0])
				intersection_point_y = float(intersection_points[0][1])
				point = (intersection_point_x, intersection_point_y)
				strike_line = Line(point, striker_point)
				slope = strike_line.slope
				angle = math.degrees(math.atan(slope))
				back_strike = False
				print 'Angle b/w striker coin & pocket: ', angle_striker_coin_pocket, '\n'
				if angle_striker_coin_pocket >= 175:
					force = 970
				elif angle_striker_coin_pocket >= 170 and angle_striker_coin_pocket < 175:
					force = 1500
				elif angle_striker_coin_pocket > 120 and angle_striker_coin_pocket < 170:
					force = 2000
				else:
					force = 4000

				angle += 90
				strike = {'angle': angle, 'force': force, 'position': i, 'angle_mutual': angle_striker_coin_pocket, 'type': coin['type']}
				pocket1_results.append(strike)
				striked = True
				break
			if striked:
				break
	return_dict['pocket1'] = pocket1_results

socketIO.on('player_input', emit_response)
socketIO.emit('connect_game', {'playerKey': player2Key, 'gameKey': gameKey})
socketIO.on('connect_game', connection_response)
socketIO.on('your_turn', coin_positions)
socketIO.wait()