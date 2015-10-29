"""
My solution for the task of the research engineering job position at the
Wikimedia Foundation.

Dan Milon <i@danmilon.me>
"""
import json
import os
import collections
import time
from concurrent.futures import ThreadPoolExecutor


class RCEventProcessorBase:
    """
    Base class for RC event processing that provides all the ordering
    logic. Subclasses must implement `process_rc_event()` and `handle_result()`.

    :Parameters:
        max_workers : `int`
            Number of workers threads to use. If `None` then it defaults to the
            default behavior of `concurrent.futures.ThreadPoolExecutor` (number
            of CPUs * 5 currently).
    """

    def __init__(self, max_workers=None):
        self._executor = ThreadPoolExecutor(max_workers)

        # keep a queue of running futures from oldest to newest
        self._ordered_futures_queue = collections.deque()

    def process_rc_event(self, rc_event):
        """
        Processes an RC event. It is called in an unordered manner.
        Must be implemented by subclasses.

        :Parameters:
            rc_event : `dict`
                The RC event to process.

        :Returns:
            The processing result that will later be passed to `handle_result()`.
        """

        raise NotImplementedError('Must be implemented by subclasses')

    def handle_result(self, result):
        """
        Finalizes the processing of an event. It is called in an ordered manner
        (same order as the events were submitted to the processor).

        Must be implemented by subclasses.

        :Parameters:
            result : The result of a processing as returned by `process_rc_event()`.
        """

        raise NotImplementedError('Must be implemented by subclasses')

    def _add_clean_callback(self, future):
        """
        Add callback `_clean_futures_queue()` to future `future`.

        :Parameters:
            future : `concurrent.futures.Future`
                The future to add the callback to.
        """

        future.add_done_callback(lambda fut: self._clean_futures_queue())

    def _clean_futures_queue(self):
        """
        Inspect `_ordered_futures_queue` and finalize as much events processing
        as possible but in an ordered manner.
        """

        while len(self._ordered_futures_queue) > 0:
            future = self._ordered_futures_queue[0]
            # if future is not done, then we can't do anything more
            if not future.done():
                break

            # if future is done, then get user to finalize it and drop it.
            result = future.result()
            self.handle_result(result)
            self._ordered_futures_queue.popleft()

        # now add clean callback to first future, its the one that must be
        # finished next
        # Note: Even if the future completed in the meantime, the callback will
        # still run.
        if len(self._ordered_futures_queue) > 0:
            self._add_clean_callback(self._ordered_futures_queue[0])

    def submit(self, rc_event):
        """
        Submit an RC Event to be processed by the workers.
        Actual processing happens in an asynchronous manner.

        :Parameters:
            rc_event : `dict`
                The RC event to be processed by the workers.
        """
        future = self._executor.submit(self.process_rc, rc_event)
        # save future in the ordered list of futures
        self._ordered_futures_queue.append(future)

        # if it is the only future we have, we know its the first that must be
        # finalized, lets add a clean callback to it.
        if len(self._ordered_futures_queue) == 1:
            self._add_clean_callback(future)


class RCEventProcessor(RCEventProcessorBase):
    """
    Dummy implementation of the `RCEventProcessorBase` for the purposes of the
    task.
    """

    def process_rc(self, rc_event):
        """
        Dummy function that supposedly performs computations about an RC event. For
        this implementation it merely goes into a busy wait loop for the number of
        seconds dictated by `rc_event['wait']`.

        :Parameters:
            rc_event : dict
                The RC event to process.

        :Returns:
            The RC event itself.
        """

        RCEventProcessor._busy_wait(rc_event['wait'])
        return rc_event

    def handle_result(self, result):
        """
        Merely prints the RC event for demo purposes.
        """

        print(result)

    @staticmethod
    def _busy_wait(wait_secs):
        """
        Performs a simple busy wait loop.

        :Parameters:
            wait_secs : Number of seconds to wait.
        """

        start = time.time()
        while time.time() - start < wait_secs:
            time.sleep(0.001)


if __name__ == '__main__':
    # deserialize sampled RC JSON file in list
    stream = []
    DIR_PATH = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(DIR_PATH, 'sampled_rc.json')) as samples_fd:
        for line in samples_fd:
            stream.append(json.loads(line))

    # create the RC event processor and feed it the events from older to newer.
    rc_processor = RCEventProcessor(max_workers=None)
    for rc_event in stream:
        rc_processor.submit(rc_event)
