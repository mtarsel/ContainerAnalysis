from requests import post
from json import loads
from base64 import b64decode


class Hub:
	"""An object to connect to dockerhub. 
	   Does not store username or password.
	   Any user information will be entered at execution.
	"""
	def __init__(self, regis, uname, upass):
		self.regis = regis
		self.uname = uname
		self.upass = b64decode(upass)
		self.org_list = ['ppc64le', 'ibmcom']
		self.header = ''

	def token_auth(self):
		# obtain token
		r = post('https://' + self.regis + '/v2/users/login/',
			json={"username": self.uname, "password": self.upass})

		r.raise_for_status()
		token = loads(r.text)["token"]

		# create special packet header with JWT and token
		self.header = {'Authorization': 'JWT ' + token}

