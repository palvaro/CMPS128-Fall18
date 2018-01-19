# Assignment 1 : Introduction to Docker and REST API

## Due date: Jan 24th 2018, Wednesday 11.59 pm

## Instructions
For the first assignment, you will create a REST API service that is able to differentiate between GET, POST and PUT requests, and responds to GET requests for the endpoints *'hello'* and *'check'*.
You will use Docker to create an image which must expose a web server at port 8080 that implements the REST interface given below.

**Please note that for this project, team size is not relevant, but will be in the future.** It is alright to submit this assignment as an individual, even, or as a member of a team of up to four people. From assignment 2 onward, we require that you be a part of a team of 3-4 people in order to receive full credit for the assignment. This eases the burden of work for you, as the projects increase in difficulty, and also for the TA, as he grades fewer projects and can give feedback and grades sooner rather than later.

You will need to submit a new repo for each assignment. Each repo must contain a “members.txt” file and a “contribution-notes.txt” file, which lists the members and their contributions respectively. The format for these files are given below. Please read them carefully and adhere to the instructions exactly for full credit. 

## REST API
**Hello:**
1. Method: GET   
  Resource Identifier: http://localhost:8080/hello?name=John   
  Response message-body: Hello John!

2. Method: GET   
  Resource Identifier: http://localhost:8080/hello (No parameter)   
  Response message-body: Hello user!

**Check:**
1. Method: GET  
  Resource Identifier: http://localhost:8080/check   
  Response message-body: This is a GET request  
  Status code: 200
 
2. Method: POST  
  Resource Identifier: http://localhost:8080/check  
  Response message-body: This is a POST request  
  Status code: 200

3. Method: PUT  
  Resource Identifier: http://localhost:8080/check  
  Should not support this method. Status code returned should be 405.    

## Building/Testing your container:

Test scripts will be posted soon. Ensure your container builds, runs, and responds to the call examples for the methods above during development until then.
It is critical that you run the test scripts before submitting your assignment, as the behavior should be predictable, and the test scripts provided will be similar to the further tests that will be run during grading.

## Instructions how to submit your homework:

0. Preconditions - You have a project folder on your local machine.
1. Create a file *members.txt*. It will contain one member per line, member being the ucsc id. e.g.  
members.txt:  
palvaro  
usardesa  

2. Create a *contribution-notes.txt* file. This can be empty until the moment of final submission. e.g.   
palvaro  
created all the docker related stuff  
usardesa  
wrote the web server app in python  

3. Create a local git repo (git init, add, commit)

4. Create a bitbucket account (https://bitbucket.org/account/signup/)

5. Create a team (NOTE: Do NOT create a repo before creating a team, it will be 'wasted')  
  1. Team ID needs to be unique at bitbucket, but prefix it with cmps128 e.g. cmps128team1.
  2. Add team members -- *UmangSardesai* and *palvaro*

6. Create a repository for the team. Ensure that it is private.

7. Commit files to the repository  
```cd /path/to/my/repo```  
```git remote add origin <repo>```   
```Ex: git remote add origin  https://johndoe@bitbucket.org/cmps128TAtest/hw1```  
```git push -u origin --all # pushes up the repo and its refs for the first time```  
```git push -u origin --tags # pushes up any tags```

8. Create your Dockerfile, create your source folder for the server that will run in the docker image. Test output. Commit early, commit often.

9. When you are satisfied with your solution (or when you nearly run out of time :’( ), submit your latest commit id to the Google form that will be posted closer to the due date.

To evaluate a homework submission, TA will be creating a docker image using your Dockerfile in your project directory. It will be tested by sending GET and POST request to 8080 port.
