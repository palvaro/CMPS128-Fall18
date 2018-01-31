# Assignment 2 : A single-site Key-value store with forwarding

## Instructions
This assignment consists of two parts: 
1. A REST-accessible single-site key-value store. 
2. A service that consist of several instances. One instance is a single site key-value store. All other instance process requests by forwarding them to the main instance.

This piece of infrastructure will form the foundation of all future projects, which will extend it to become fault-tolerant and scalable.


### Part 1: Single-site Key-value store

Key-value stores provide a simple storage API in which values (arbitrary data, often semi-structured documents in formats such as JSON) are stored and retrieved by *key*.  The typical KVS API looks like:

|Call|Parameters|Returns|Example|
|----|----------|-------|--------|
|put/post|     key, val   |  Success or failure    | put(foo, bar) |
|get| key | value | X = get(foo) # now X=bar|
|del| key | Success or failure | del(foo) # subsequent gets to foo will fail|

You can implement a KVS in whatever way you choose.  We will only be testing its adherence to certain *functional guarantees*, which we enumerate below.  As in the last assignment, you will also create a REST API that allows users (as well as our test scripts) to interact with it over HTTP.


### Input format restrictions
- key
  - charset: [a-zA-Z0-9_] i.e. Alphanumeric including underscore, and case-sensitive 
  - size:    1 to 250 characters

- val
  - size:    1.5MB  

You key-value store does not need persist the data, i.e. it can store data in memory only. For example, if the key-value store goes down and then get started again, then the key-value store does not need contain the data it had before the crash.

You need to implement your own key value store, and not use an existing key value stores such as Redis, Couch, Mongo etc. The best approach would be to use a [Hash Table](https://en.wikipedia.org/wiki/Hash_table) in your respective language. 


### Functional guarantees for a single site key-value store
- service runs on port 8080 and is available as a resource named kvs. i.e. service listens at http://server-hostname:8080/kvs
- service listens to requests on a network
- get on a key that does not exist returns an error message
- get on a key that exists returns the last value successfully written (via put/post) to that key
- del on a key that does not exist returns an error message
- put on a key that does not exist (say key=foo, val=bar) creates a resource at /kvs. Subsequent gets with 'key=foo' returns 'bar' until the next put with 'key=foo'
- del on a key that exists (say foo) deletes the resource at /kvs and returns success. Subsequent gets with 'key=foo' returns a 404 until the next put with 'key=foo'
- put on a key that exists (say key=foo) replaces the existing val with the new val (say baz), and acknowledges a replacement in the response by setting the 'replaced' field to 1 (see examples below) . Subsequent gets return 'baz' until the next put at /kvs with 'key=foo'. 

### Part 2: Network of instances with request forwarding
Once you have a single site key-value store working, you will create a network of instances. One instance is the key-value store, which we call the main one. All other instances process request by forwarding them to the main instance.

We are going to create several instances of your container. However, you are just submitting one container, so your service will need to know how to play either role.
The role of a container is specified via environment variables.
https://docs.docker.com/engine/reference/run/#env-environment-variables

We will set the following ENV variables when running your docker instances:  
IP -- the externally-visible ip to which your instance should bind  
PORT -- the port to which your instance should bind  
MAINIP -- is a pair IP:PORT of the main key-value store instance

Then ENV variables for the main instance will look like this:  
IP=10.0.0.20  
PORT=8080  
We do not need to set the MAINIP variable.  

The corresponding ENV variables for a forwarding instance will look like:  
IP=10.0.0.21  
PORT=8080  
MAINIP=10.0.0.20:8080  

As an illustration, let our service consist of 3 instance A, B, and C. Instance A is the main key-value store. Instances B and C process requests by forwarding to instance A.
When instance B receives request, say get(key1), it queries instance A and returns the value (or error message) it has received from A.
If we stop instance B, then it should not affect the service: requests can be successfully processed by instances A or C.
However, if we stop instance A, then B and C cannot process put, get and del requests. They should return an error message.


### Functional guarantees for a service with forwarding
- The main instance and the forwarding instances satisfy functional guarantees for a single site key-value store described above 
- If the main instance is down then forwarding instances return error messages on requests.
- If the main server is active then all active instances can successfully process requests.


### Request and Response formats

Pre-condition - localhost:4000 forwards to 8080 of the docker container running the kvs service

1. PUT localhost:4000/kvs -d "key=foo&value=bart"
    - case 'foo' does not exist
      - status code : 201
      - response type : application/json
      - response body:
<pre>
		{
      'replaced': 0, // 1 if an existing key's val was replaced
      'msg': 'success'
		}
</pre>

    - case 'foo' exists
		  - status code : 200
		  - response type : application/json
		  - response body:
<pre>
		{
      'replaced': 1, // 0 if key did not exist
      'msg': 'success'
		}
</pre>
		
2. GET localhost:4000/kvs -d "key=foo"
    - case 'foo' does not exist
      - status code : 404
      - response type : application/json
      - response body:
<pre>
			{
				'msg' : 'error',
				'error' : 'key does not exist'
			}
</pre>
    - case 'foo' exists
      - status code : 200
      - response type : application/json
      - response body:
<pre>
			{
				'msg' : 'success',
				'value': 'bart'
		 	}
</pre>

3. DELETE localhost:4000/kvs -d "key=foo"
    - case 'foo' does not exist
      - status code : 404
      - response type : application/json
      - response body:
<pre>
			{
				'msg' : 'error',
				'error' : 'key does not exist'
		 	}
</pre>

    - case 'foo' exists
      - status code : 200
      - response type : application/json
      - response body:
<pre>
			{
				'msg' : 'success'
		 	}
</pre>

4. PUT, GET, DELETE 
    - case the main instance is down 
      - status code : 404
      - response type : application/json
      - response body:
<pre>
			{
				'msg' : 'error',
				'error' : 'service is not available'
		 	}
</pre>

### Things to note:

1. Data will be passed via '-d' parameter in cURL and not via arguments.

2. Here's a sample of how three containers will be initiated in a Docker subnet:
```bash
docker run -p 4000:8080 --net=mynet --ip=10.0.0.20 -d contname
docker run -p 4001:8080 --net=mynet -e MAINIP=10.0.0.20:8080 -d contname
docker run -p 4002:8080 --net=mynet -e MAINIP=10.0.0.20:8080 -d contname
```
