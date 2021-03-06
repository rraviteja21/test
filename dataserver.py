#!/usr/bin/env python
"""
Author: David Wolinsky
Version: 0.02

Description:
The XmlRpc API for this library is:
  get(base64 key)
    Returns the value and ttl associated with the given key using a dictionary
      or an empty dictionary if there is no matching key
    Example usage:
      rv = rpc.get(Binary("key"))
      print rv => {"value": Binary, "ttl": 1000}
      print rv["value"].data => "value"
  put(base64 key, base64 value, int ttl)
    Inserts the key / value pair into the hashtable, using the same key will
      over-write existing values
    Example usage:  rpc.put(Binary("key"), Binary("value"), 1000)
  print_content()
    Print the contents of the HT
  read_file(string filename)
    Store the contents of the Hashtable into a file
  write_file(string filename)
    Load the contents of the file into the Hashtable
"""

import sys, SimpleXMLRPCServer, getopt, pickle, time, threading, xmlrpclib, unittest
from datetime import datetime, timedelta
from xmlrpclib import Binary
from SimpleXMLRPCServer import *
class Myserver(SimpleXMLRPCServer):
		
		def serve_forever(self):
			global running
			running = 1
			while running:
				self.handle_request()
			
# Presents a HT interface
class SimpleHT:
	
  def __init__(self, portlist):
        self.data = {}
        self.next_check = datetime.now() + timedelta(minutes = 5)
        print "WELCOME"
	portlist = portlist[1:]
	url = "http://127.0.0.1:"
	server_list =[]
  	for each in portlist:
			server_list.append(xmlrpclib.Server(url+each))
	keylist = []
	print "server_list", server_list
	
	available_servers = []
	
	for server in server_list:
		try:
			res = server.get(Binary("keys"))
			keylist = res
			available_servers.append(server)
		except:
			print "iterate to next server"
	print "LIST OF KEYS", keylist
	for key in keylist:	
			available_values = []
			print "key is: ", key
			for server in available_servers:
				res = server.get(Binary(key))
				value = pickle.loads(res["value"].data)
				available_values.append(value)

			for each in available_values:
				count = available_values.count(each)
				if count >= 2:
					value = each
					break
				
			print self.put(Binary(key), Binary(pickle.dumps(value)), 6000)
  def count(self):
    # Remove expired entries
    self.next_check = datetime.now() - timedelta(minutes = 5)
    self.check()
    return len(self.data)

  def list_contents(self):
	return self.data.keys()
	

  def corrupt(self,key):
	key = key.data
	value = "corrupted data"
	
	self.put(Binary(key),Binary(pickle.dumps(value)),6000)
	return value

  def terminate(self):
	global running
	running = 0
	print "Terminating server"
	return 1

  # Retrieve something from the HT
  def get(self, key):
    # Remove expired entries
    self.check()
    # Default return value
    rv = {}
    
    # If the key is in the data structure, return properly formated results
    key = key.data
    print "KEY.DATA" , key
   
    if key == "keys":
		newdict = self.data.keys()
    		print "GET check: ", newdict
		return newdict
		
    elif key in self.data:
      ent = self.data[key]
      now = datetime.now()
      print "SELF>DATA ",self.data
      print "NOW", now
      print "ent[1]", ent[1]	
      if ent[1] > now:
        ttl = (ent[1] - now).seconds
	print "TTL", ttl
	print "SERVER 1!!!!!"
        rv = {"value": Binary(ent[0]), "ttl": ttl}
      else:
        del self.data[key]
    return rv

  # Insert something into the HT
  def put(self, key, value, ttl):
    # Remove expired entries
    self.check()

    end = datetime.now() + timedelta(seconds = ttl)
    self.data[key.data] = (value.data, end)
    
    return True
    
  # Load contents from a file
  def read_file(self, filename):
    f = open(filename.data, "rb")
    self.data = pickle.load(f)
    print "READDATA"
    print self.data
    f.close()
    return True

  # Write contents to a file
  def write_file(self, filename):
    f = open(filename.data, "wb")
    print "WRITE"
    print self.data
    pickle.dump(self.data, f)
    f.close()
    return True

  # Print the contents of the hashtable
  def print_content(self):
    print self.data
    print "PRINTCONTENT"
    return True

  # Remove expired entries
  def check(self):
    now = datetime.now()
    if self.next_check > now:
      return
    self.next_check = datetime.now() + timedelta(minutes = 5)
    to_remove = []
    for key, value in self.data.items():
      if value[1] < now:
        to_remove.append(key)
    for key in to_remove:
      del self.data[key]
       
def main():
 
  optlist, args = getopt.getopt(sys.argv[1:], "", ["port=", "test"])
  ol={}
  for k,v in optlist:
    ol[k] = v
  portlist = []
  for i in range(len(args)):
	portlist.append(args[i])
  print "portlist", portlist

  if "--port" in ol:
    port = int(ol["--port"])  
  if "--test" in ol:
    sys.argv.remove("--test")
    unittest.main()
    return

  serve(portlist)

# Start the xmlrpc server
def serve(portlist):
	  file_server = Myserver(('', int(portlist[0])))
	  file_server.register_introspection_functions()
	  sht = SimpleHT(portlist)
	  file_server.register_function(sht.terminate)
	  file_server.register_function(sht.get)
	  file_server.register_function(sht.put)
	  file_server.register_function(sht.print_content)
	  file_server.register_function(sht.read_file)
	  file_server.register_function(sht.write_file)
	  file_server.register_function(sht.list_contents)
	  file_server.register_function(sht.corrupt)  
	  
	  file_server.serve_forever()
  
'''
# Execute the xmlrpc in a thread ... needed for testing
class serve_thread:
  def __call__(self, port):
    serve(port)

# Wrapper functions so the tests don't need to be concerned about Binary blobs
class Helper:
  def __init__(self, caller):
    self.caller = caller

  def put(self, key, val, ttl):
    return self.caller.put(Binary(key), Binary(val), ttl)

  def get(self, key):
    return self.caller.get(Binary(key))

  def write_file(self, filename):
    return self.caller.write_file(Binary(filename))

  def read_file(self, filename):
    return self.caller.read_file(Binary(filename))

class SimpleHTTest(unittest.TestCase):
  def test_direct(self):
    helper = Helper(SimpleHT(portlist))
    self.assertEqual(helper.get("test"), {}, "DHT isn't empty")
    self.assertTrue(helper.put("test", "test", 10000), "Failed to put")
    self.assertEqual(helper.get("test")["value"], "test", "Failed to perform single get")
    self.assertTrue(helper.put("test", "test0", 10000), "Failed to put")
    self.assertEqual(helper.get("test")["value"], "test0", "Failed to perform overwrite")
    self.assertTrue(helper.put("test", "test1", 2), "Failed to put" )
    self.assertEqual(helper.get("test")["value"], "test1", "Failed to perform overwrite")
    time.sleep(2)
    self.assertEqual(helper.get("test"), {}, "Failed expire")
    self.assertTrue(helper.put("test", "test2", 20000))
    self.assertEqual(helper.get("test")["value"], "test2", "Store new value")

    helper.write_file("test")
    helper = Helper(SimpleHT())

    self.assertEqual(helper.get("test"), {}, "DHT isn't empty")
    helper.read_file("test")
    self.assertEqual(helper.get("test")["value"], "test2", "Load unsuccessful!")
    self.assertTrue(helper.put("some_other_key", "some_value", 10000))
    self.assertEqual(helper.get("some_other_key")["value"], "some_value", "Different keys")
    self.assertEqual(helper.get("test")["value"], "test2", "Verify contents")

  # Test via RPC
  def test_xmlrpc(self):
    output_thread = threading.Thread(target=serve_thread(), args=(int(portlist[0]), ))
    output_thread.setDaemon(True)
    output_thread.start()

    time.sleep(1)
    helper = Helper(xmlrpclib.Server("http://127.0.0.1:"+portlist[0]))
    self.assertEqual(helper.get("test"), {}, "DHT isn't empty")
    self.assertTrue(helper.put("test", "test", 10000), "Failed to put")
    self.assertEqual(helper.get("test")["value"], "test", "Failed to perform single get")
    self.assertTrue(helper.put("test", "test0", 10000), "Failed to put")
    self.assertEqual(helper.get("test")["value"], "test0", "Failed to perform overwrite")
    self.assertTrue(helper.put("test", "test1", 2), "Failed to put" )
    self.assertEqual(helper.get("test")["value"], "test1", "Failed to perform overwrite")
    time.sleep(2)
    self.assertEqual(helper.get("test"), {}, "Failed expire")
    self.assertTrue(helper.put("test", "test2", 20000))
    self.assertEqual(helper.get("test")["value"], "test2", "Store new value")
'''
if __name__ == "__main__":

	main()

