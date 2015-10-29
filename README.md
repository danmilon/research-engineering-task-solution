
This is my solution for the task of the research engineering job position at the
Wikimedia Foundation. The implementation is written in Python, using concurrency
features from Python 3.4.

Run it like this

```
$ python rc-processor.py
```

It will start printing the output of the processing of the events, in order with
the input.

## Approach ##

In order for the processing of the edits to be in real time and be able to catch
up with the rate of edit events being generated, they need to be processed in
parallel. Since the processing of the events might be CPU bound we need to run
multiple threads which will process the stream of events in parallel, but as
dictated by the task, the output from the processing needs to be in order with
the input stream. This means there are two steps for each processing. The
parallel part and the part that needs to happen in order.

To ensure the output is in order, I use a queue where I keep the
[promises/futures](https://en.wikipedia.org/wiki/Futures_and_promises) of the
threads that are processing an event, in order. When we need to clean this queue
we perform the output part of the processing for all the continuous futures in
the beginning (oldest to newest) of the queue that are completed.

Initially I thought of running the clean up code as a callback whenever a future
completes. But then realized that this is kind of a brute force approach, since
I can do even better by running it only for the first future that is submitted,
and in the callback logic, after the clean up, add the same callback to the new
first future. That is because I know that nothing can complete before the first
future completes. This approach is better both because of performance reasons
(less calls to the clean up code) but more importantly in the first approach the
clean up code would run in parallel multiple times and has concurrency issues
which can be solved by a lock. Whereas in the second approach the clean up code
runs in a controlled manner and is guaranteed to not run in parallel. Please
advise the code also to better understand these details.

Generally I am very glad with this approach because it goes with the nature of
the problem and is truly streaming.

## Reason for deque data structure ##

The `collections.deque` data structure was chosen as the data structure for the
list of futures for two reasons. First it has thread safe read and write
methods, which we need since it is used both by the `submit()` method and the
clean up function and these two can run in parallel. Secondly, its `popleft()`
method is faster than removing from the front of a regular list.

## Map approach ##

I could also go with a parallel and ordered map approach which is already
implemented in the standard library of python and most high level programming
languages. But that means that I need to chunk the input stream in blocks, run
the map function on them, and when all of them complete fill up a new chunk and
repeat. This way the threads are under utilized since the whole block must
complete in order to process new events, and also it is not truly streaming.

## Time spent on the task ##

I spent one hour and a half to understand the problem, design a solution and
implement it in code. Then another hour was spent polishing it, putting it in
classes and writing documentation. And then another half hour for this text.

## Unit Testing ##

I'd also like to add unit testing to my solution, but this is beyond the two
hour limit.
