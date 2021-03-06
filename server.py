#!/usr/bin/python
from flask import Flask
from flask import request
from algo import *
import random, math

app = Flask(__name__)
setup()

# Upon receiving /restart?id=<id>, server will send the last badge back to arduino.
# If there is no nearby user or place so far, server will send the user's own badge.
@app.route('/restart', methods=['GET'])
def restart():
  print request.args
  if 'id' in request.args:
    user_id = int(request.args['id'])
    return user_restart(user_id)
  else:
    return "Please specify user ID."

def deg2decimal(x):
  if x >= 0:
    x = math.floor(x/100) + (x - 100*math.floor(x/100))/60
  else:
    x = -(math.floor(-x/100) + (-x - 100*math.floor(-x/100))/60)
  return x

# For reporting GPS location in degree minute format.
@app.route('/status', methods=['POST'])
def post_status():
  if 'id' in request.form and 'lat' in request.form and 'long' in request.form:
    lat = float(request.form['lat'])
    lng = float(request.form['long'])
    user_id = int(request.form['id'])
    return update_user(int(request.form['id']), \
                         [deg2decimal(lat), deg2decimal(lng)])
  else:
    print "malform"
    return "malform"

# For reporting GPS location in degree minute format.
@app.route('/status', methods=['GET'])
def get_status():
  return """
  <!DOCTYPE html>
  <html>
  <body>
    <form  method="post">
      ID:<br>
      <input type="text" name="id"><br>
      Latitude:<br>
      <input type="text" name="lat"><br>
      Longtitude:<br>
      <input type="text" name="long"><br>
      <input type="submit" value="Submit" name="submit">
    </form>
    
  </body>
  </html>
  """

# For reporting GPS location in decimal format.
@app.route('/status2', methods=['POST'])
def post_status2():
  if 'id' in request.form and 'lat' in request.form and 'long' in request.form:
    user_id = int(request.form['id'])
    return update_user(int(request.form['id']), \
                         [float(request.form['lat']), float(request.form['long'])])
  else:
    print "malform"
    return "malform"

# For reporting GPS location in decimal format.
@app.route('/status2', methods=['GET'])
def get_status2():
  return """
  <!DOCTYPE html>
  <html>
  <body>
    <form  method="post">
      ID:<br>
      <input type="text" name="id"><br>
      Latitude:<br>
      <input type="text" name="lat"><br>
      Longtitude:<br>
      <input type="text" name="long"><br>
      <input type="submit" value="Submit" name="submit">
    </form>
    
  </body>
  </html>
  """

# Upload badge
@app.route('/badge', methods=['GET','POST'])
def badge():
  print request.form
  if 'id' in request.form and 'badge' in request.form:
    save_badge(int(request.form['id']),request.form['badge'])
  return """
  <!DOCTYPE html>
  <html>
  <body>
    <form  method="post">
      ID:<br>
      <input type="text" name="id"><br>
      Sequence of 64 x 3:<br>
      <input type="text" name="badge" size="100"><br>
      <input type="submit" value="Submit" name="submit">
    </form>
    
  </body>
  </html>
  """

# Upload personalized message
@app.route('/message', methods=['GET','POST'])
def message():
  print request.form
  print request.args
  if 'id' in request.form and 'message' in request.form:
    save_message(int(request.form['id']),request.form['message'])
  return """
  <!DOCTYPE html>
  <html>
  <body>
    <form  method="post">
      ID:<br>
      <input type="text" name="id"><br>
      Message:<br>
      <input type="text" name="message" size="50"><br>
      <input type="submit" value="Submit" name="submit">
    </form>
    
  </body>
  </html>
  """

@app.route('/map', methods=['GET'])
def map():
  user_id = int(request.args['id'])
  return get_map(user_id)

if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5001, debug=True)

