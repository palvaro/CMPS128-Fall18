# CMPS128 Fall 2018
## Distributed Systems
| key | value | 
|-----|-------|
|When: | Monday, Wednesday and Friday at <b>2:40 PM</b>. |
|Where: | Thimann Lecture 001 |
|Who: | [Peter Alvaro](http://people.ucsc.edu/~palvaro/) |
|Office hours: | Fridays at 1PM and TBD |
|Prerequisites: | CMPS101 or CE150 required. CMPS111 or CMPS105 recommended. |
|Text: | [Distributed Systems](http://www.amazon.com/Distributed-Systems-Concepts-Design-5th/dp/0132143011/), Coulouris et al. -- Optional|
|TA: | Elisabeth Oliver and Nidhi Shah|
|TA sections: | Tuesdays 9:50-10:55am in Kresge 323 |
|| Fridays 10:40-11:45am in Kresge 323
|Modules: | [Modules](modules.md)|
|Readings (in flux): | [Readings](readings.md)|

# Description

This course will explore fundamental as well as emerging topics in distributed systems.

Distributed systems are notoriously difficult to program, and even harder to reason about.  Much of this difficulty arises from *uncertainty* in the executions of distributed programs.  Uncertainty about the ordering and timing of events and communication give rise to concerns about the *consistency* of program outputs and states. Uncertainty about what may go wrong during an execution (e.g., computers crashing, messages being lost) gives rise to concerns about the *completeness* of these outputs and states.  Together, these sources of uncertainty make achieving even relatively modest guarantees in large-scale systems extremely difficult.

While distributed systems have been studied for some time, they have only recently become essentially ubiquitous:
nearly all non-trivial systems are now physically distributed.  It is no longer possible to relegate responsibility for managing the complexity of distributed systems to a group of expert library or infrastructure writers: all programmers must now be distributed programmers. This is both a crisis and an opportunity.

This course will cover both theoretical and practical aspects of distributed systems and distributed programming, diving the subject
matter into four core [Modules](modules.md):

 * Time and Asynchrony
 * Fault Tolerance
 * Consistency
 * Parallelism and Scaleup

 
# Readings and Prerequisites

The optional text for CMPS128 is [Distributed Systems](http://www.amazon.com/Distributed-Systems-Concepts-Design-5th/dp/0132143011/) by Coulouris et al.  Despite having perhaps the worst cover art that I have ever seen on any book in my life, this text covers most of the fundamental
concepts of the course.  Note however that the text is supplemental.  The key material of this course is covered in lecture, and reading the text will not be sufficient to pass the examinations.

For optional reading, Mikito Takada's [Distributed Systems for fun and profit](http://book.mixu.net/distsys/) covers 
many of the same topics in a sophisticated (albeit high-level) way.

Students are required to have completed either CMPS101 or CE150, and are recommended to have completed CMPS111 or CMPS105.

One of the purposes of CMPS128 is to familiarize you with practical aspects of implementing and reasoning about programs that 
require the cooperation of some number of physical machines.  Hence system building is a critical part of the course.
While CMPS128 will involve a substantial implementation component, we will not be teaching any particular language.
That is to say, you are here to build *distributed* systems, 
but we expect you to come to the table with enough programming knowledge and experience to build non-distributed systems with minimal guidance.  Regardless of the coursework you have undertaken, if you are not comfortable using programming languages 
(e.g. C, Java, Python, Ruby, Scala, Erlang, Bloom -- pick your poison) to build systems, this course is not for you.



 
# Assigments and Grading

## Pop quizzes

To ensure that everyone keeps up with the reading and attends class, we will hold a small number of pop quizzes.  Students who do not attend class on the day of a pop quiz will not receive credit.  If you need to miss class, please email the professor or TA *before* the absence with a brief explanation of the cause.

## Final Project

The final project will involve implementing and managing fault-tolerant distributed system.  This will be a substantial enginering effort, and we encourage you to work in teams of up to four people.

The final project will be divided into four sub-projects, coming due roughly every two weeks.

Project specifications will be posted on a separate page and announced on Piazza.  They will usually be posted before they are announced, but they are subject to change until announcement.  If we need to change an assigment after it was announced, we will email the class about the change.

Assigments announcements will always include a due date.  

<del>Late assignments are not accepted</del>.  Late assignments will forfeit 10% of the grade for every day late.  Students are granted *one grace day* that they may use for any assignment submission to avoid this penalty.


## Examinations

There will be two examinations: the midterm and the final.

## Grading

| Subject | Share |
|-------|---------|
| Pop quizzes | 10% |
| Participation | 5% |
| Midterm | 15% |
| Project | 40% |
| Final   | 30%   | 

Final projects are required to pass the course.  The fact that participation accounts for 5% of the grade (and pop quizzes for 10%) should give you an idea of the important of class attendance.  

# Academic honesty

Collaboration is a key part of research.  I encourage you to discuss the readings and the final project ideas with your classmates.  However, you must reveal the students with whom you discussed the assignments.  Failure to do so will result in formal disciplinary proceedings.  

I should not need to say so, but I do: plagiarism in any form is not acceptable and will not be tolerated.  As researchers, we always stand upon the shoulders of giants, and building upon existing work is the norm.  It is essential, however, that we provide proper attribution.  When in doubt, cite!  
