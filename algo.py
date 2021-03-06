from PIL import Image
import random, time, os

# User object represents either a user or a stationary place.
# For staionary places, 
#   - 'locations' field contains only one location.
#   - 'nearby' and 'nearby_loc' fields are not used.
class User:
  def __init__(self, user_id, \
                 message = "", \
                 badge = ','.join(str(random.randint(0,255)) for x in xrange(64*3*2))):
    self.locations = []
    self.datetime = None
    self.user_id = user_id
    self.nearby = []
    self.nearby_loc = []
    self.badge = badge
    self.message = message
    self.queue = []
    self.generate_badge()
    self.last_sent = None

  # Send the last badge back to arduino.
  # If there is no nearby user or place so far, server will send the user's own badge.
  def restart(self):
    if len(self.nearby) == 0:
      return "0,0,0," + self.badge
    else:
      if self.nearby[-1].badge == self.last_sent:
        return "0,0,0," + self.nearby[-1].badge
      else:
        self.last_sent = self.nearby[-1].badge
        return "1,0,0," + self.nearby[-1].badge

  # 1) Update user's location.
  # 2) Append nearby users and places to the nearby list, and add them to the queue.
  # 3) Send the badge of the first user/place in the queue, 
  #    and remove such user/place from the queue.
  def ping(self,datetime, loc, nearby_users, nearby_places):
    self.locations.append(loc)
    self.datetime = datetime
    # handle nearby users
    for user in nearby_users:
      if not (user.user_id == self.user_id) and not(user.user_id in self.nearby):
        self.nearby.append(user)
        self.nearby_loc.append(user.locations[-1])
        self.queue.append(user.badge)
        user.nearby.append(self)
        user.nearby_loc.append(self.locations[-1])
        user.queue.append(self.badge) # add to queue

    # handle nearby places
    for place in nearby_places:
      self.nearby.append(place)
      self.nearby_loc.append(place.locations[-1])
      self.queue.append(place.badge)

    # send one badge at a time
    if len(self.queue) > 0:
      print "send badge: case 1"
      tmp = self.queue[0]
      self.queue = self.queue[1:]
      return "1,0,0," + tmp
    elif len(self.nearby) == 0:
      print "send badge: case 2 (self)"
      return "0,0,0," + self.badge
    else:
      print "send badge: case 3 (last)"
      return "0,0,0," + self.nearby[-1].badge

  def save_badge(self,badge):
    print "save_badge: id=", self.user_id
    self.badge = badge
    print "generate PNG..."
    self.generate_badge()
    print "save string..."
    f = open('db/' + str(self.user_id),'w')
    f.write(self.badge)
    f.close()
    print "save_badge: sucess!"

  # Generate PNG
  def generate_badge(self):
    k = 5
    arr = [int(x) for x in self.badge.split(',')]
    print "len = ", len(arr)
    pixels = [0 for x in xrange(8*8*k*k)]
    for i in xrange(64):
      color = (arr[3*i],arr[3*i+1],arr[3*i+2])
      x = i % 8
      y = i / 8
      for a in xrange(k):
        for b in xrange(k):
          pixels[(y*k+a)*8*k + (x*k+b)] = color
    im = Image.new("RGB", (8*k,8*k))
    im.putdata(pixels)
    im.save('static/' + str(self.user_id) + '.png')

  def save_message(self, message):
    if isinstance(message, unicode):
      self.message = message.encode('ascii')
    else:
      self.message = message

recent_users = []
stationary = []
id2user = {}

def parseGPS(x):
  tokens = x.split(',')

  latitude = tokens[3]
  latitude = int(latitude[:2]) + float(latitude[2:])/60.0
  if tokens[4] == 'S':
    latitude = -latitude

  longtitude = tokens[5]
  longtitude = int(longtitude[:3]) + float(longtitude[3:])/60.0
  if tokens[6] == 'W':
    longtitude = -longtitude
  return [latitude, longtitude]

def get_datetime():
  # d = 502 for 05/02
  # t = 231801 for 23:18:01 hh:mm:ss
  d = int(time.strftime("%d%m"))
  t = int(time.strftime("%H%M%S"))
  return [d,t]

# Filter for users who ping the server less than 'min_limit' minutes ago.
min_limit = 5
def filter_recent(users, datetime):
  ret = []
  for x_user in users:
    x_datetime = x_user.datetime
    if datetime[0] == x_datetime[0]:
      if datetime[1] - x_datetime[1] < min_limit * 100:
        ret.append(x_user)
    elif datetime[0] + 1 == x_datetime[0]:
      if (246000 - datetime[1]) - x_datetime[1] < min_limit * 100:
        ret.append(x_user)
  return ret

def filter_near(users, my_loc):
  ret = []
  for user in users:
    loc = user.locations[-1]
    if abs(loc[0] - my_loc[0]) < 0.0005 and abs(loc[1] - my_loc[1]) < 0.0005:
      ret.append(user)
  return ret

def report_status(user_id, gps):
  if len(gps.split(',')) < 10:
    print "Invalid GPS data"
    return

  return update_user(user_id, parseGPS(gps))

def update_user(user_id,loc):
  o = open('log','a')
  print >>o, user_id, loc
  o.close()

  if not(user_id in id2user):
    id2user[user_id] = User(user_id)
  print ""
  print "ID = ", user_id
  print "loc = ", loc
  user = id2user[user_id]
  datetime = get_datetime() # TODO
  global recent_users
  recent_users = filter_recent(recent_users, datetime)
  nearby_users = filter_near(recent_users, loc)
  nearby_places = filter_near(stationary, loc)
  print "recent_users = ", [x.user_id for x in recent_users]
  print "nearby_users = ", [x.user_id for x in nearby_users]
  print "nearby_places = ", [x.user_id for x in nearby_places]
  if not user in recent_users:
    recent_users.append(user)
  return user.ping(datetime, loc, nearby_users, nearby_places)
  

def user_restart(user_id):
  if not(user_id in id2user):
    id2user[user_id] = User(user_id)
  user = id2user[user_id]
  ret = user.restart()
  print ret
  return ret

def save_badge(user_id, badge):
  if not(user_id in id2user):
    id2user[user_id] = User(user_id)
  user = id2user[user_id]
  user.save_badge(badge)

def save_message(user_id, message):
  if not(user_id in id2user):
    id2user[user_id] = User(user_id)
  user = id2user[user_id]
  user.save_message(message)

f = open('map.html','r')
html = f.read()
f.close()

f = open('marker.js','r')
marker = f.read()
f.close()

f = open('label.js','r')
label = f.read()
f.close()

def get_map(user_id):
  if user_id in id2user:
    user = id2user[user_id]

    infos = ""
    for i in xrange(len(user.nearby)):
      infos = infos + marker.replace('$', str(i))
      if not user.nearby[i].message == "":
        infos = infos + label.replace('$', str(i))

    return html.replace('$1',str(user.locations))\
        .replace('$2',str(user.nearby_loc))\
        .replace('$3', ','.join(['"/static/' + str(x.user_id) + '.png"' \
                                   for x in user.nearby]))\
        .replace('$4', str([x.message for x in user.nearby]))\
        .replace('$R', infos)
  else:
    return "user_id = %d not found" % (user_id)

# Create stationary place by setting ID, badge, and location.
# Note that we use User() for both users and places.
def create_place(id, loc, badge, message):
  user = User(id, message, badge)
  id2user[id] = user
  user.ping(None, loc, [], [])
  stationary.append(user)

def preprograms_paths():
  # Hard code for users 1 & 2's paths
  update_user(1,[37.870905, -122.258770])
  update_user(1,[37.871237, -122.258049])
  update_user(1,[37.871989, -122.258083])
  update_user(1,[37.872395, -122.258228])
  update_user(1,[37.872730, -122.259236])

  update_user(2,[37.869504,-122.251766])
  update_user(2,[37.869154,-122.254792])
  update_user(2,[37.870774,-122.255854])
  update_user(2,[37.872052,-122.257798])
  update_user(2,[37.874758,-122.258662])

def setup():
  print "set up..."
  os.system('rm log')

  # Add stationary places from database "db/stationary.csv"
  f = open('db/stationary.csv','r')
  for row in f:
    tokens = row.split(';')
    create_place(int(tokens[0]), [float(tokens[2]),float(tokens[3])], tokens[4], tokens[1])
  f.close()

  #preprograms_paths()
  print "done set up."

if __name__ == "__main__":
  setup()
