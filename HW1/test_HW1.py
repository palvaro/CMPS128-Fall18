import unittest
import subprocess
import requests

PORT=8080
class TestHW1(unittest.TestCase):

  def test1(self):
      res = requests.get('http://localhost:'+str(PORT)+'/check')
      self.assertEqual(res.text, 'This is a GET request', msg='Incorrect response to GET request to /check endpoint')
      self.assertEqual(res.status_code, 200, msg='Did not return status 200 to GET request to /check endpoint')

  def test2(self):
      res = requests.post('http://localhost:'+str(PORT)+'/check')
      self.assertEqual(res.text, 'This is a POST request', msg='Incorrect response to POST request to /check endpoint')
      self.assertEqual(res.status_code, 200, msg='Did not return status 200 to POST request to /check endpoint')      

  def test3(self):
      res = requests.put('http://localhost:'+str(PORT)+'/check')
      self.assertEqual(res.status_code, 405, msg='Did not return status 405 to PUT request to /check endpoint')     

  def test4(self):
      res = requests.get('http://localhost:'+str(PORT)+'/hello?name=Peter')
      self.assertEqual(res.text, 'Hello Peter!', msg='Incorrect response to /hello?name=Peter endpoint')

  def test5(self):
      res = requests.get('http://localhost:'+str(PORT)+'/hello')
      self.assertEqual(res.text, 'Hello user!', msg='Incorrect response to /hello endpoint')            

if __name__ == '__main__':
    unittest.main()
