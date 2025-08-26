"""
This flask app provides basic mock endpoints for various endpoints called by
the VOSpace. This provides the capability to test the VOSpace in isolation
and in locations which may not have local instances of the user and auth
services.

This service is automatically included in the dev environment and can be used
by setting the AUTH_URL variable to http://auth-mock:8000
"""

from flask import Flask
app = Flask(__name__)

@app.route('/hasAccess')
def has_access():
	"""
	This mocks a response for a call to /hasAccess
	"""
	return "OK"

@app.route('/isValidToken')
def is_valid_token():
	"""
	This mocks a response for a call to /isValidToken
	"""
	return "True"

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8000)
