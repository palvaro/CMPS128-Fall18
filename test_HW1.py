import unittest
import subprocess
import requests

PORT=8080
class TestHW1(unittest.TestCase):

  # Make some sort of http request
  def test1(self):
    res = requests.get('http://localhost:'+str(PORT)+'/hello')
    self.assertEqual(res.text, 'Hello world!', msg='Incorrect response to /hello endpoint') 

  # Send a parameter with request to app, and access that parameter in app
  def test2(self):
    res = requests.post('http://localhost:'+str(PORT)+'/test?msg=HoorayAMessage123')
    self.assertEqual(res.text, 'POST message received: HoorayAMessage123', msg='Incorrect response to POST request to /test endpoint')

  # Set the status codes of responses
  def test4(self):
    res = requests.get('http://localhost:'+str(PORT)+'/hello')
    self.assertEqual(res.status_code, 200, msg='Did not return status 200 to GET request to /hello endpoint')

    res = requests.post('http://localhost:'+str(PORT)+'/hello')
    self.assertEqual(res.status_code, 405, msg='Did not return status 405 to POST request to /hello endpoint')

    res = requests.get('http://localhost:'+str(PORT)+'/test')
    self.assertEqual(res.status_code, 200, msg='Did not return status 200 to GET request to /test endpoint')   
    
    res = requests.post('http://localhost:'+str(PORT)+'/test')
    self.assertEqual(res.status_code, 200, msg='Did not return status 200 to POST request to /test endpoint')


if __name__ == '__main__':
  unittest.main() 
