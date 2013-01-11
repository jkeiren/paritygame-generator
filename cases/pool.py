import multiprocessing.pool
import threading
import logging
import pickle
from types import NoneType

def __getlogger():
  return logging.getLogger('taskpool')
  # .getChild('worker{0}'.format(multiprocessing.current_process().pid))

def process_task(task):
  try:
    if isinstance(task, Task):
      task.run(__getlogger())
    return task
  except KeyboardInterrupt:
    return
  except:
    __getlogger().exception('Exception while running task.')

class Task(object):
  def __init__(self):
    self.subtasks = []
    self.results = []
    self.parent = None
    self.__maxphase = -1
    while hasattr(self, 'phase{0}'.format(self.__maxphase + 1)):
      self.__maxphase += 1
    self.__phase = 0
    self.__waiting = False
  
  @property
  def waiting(self):
    return self.__waiting > 0
  
  @property
  def done(self):
    return self.__phase > self.__maxphase
  
  def _wait(self):
    self.__waiting = len(self.subtasks)
    self.results = []
    self.subtasks = []
  
  def _collect(self, result):
    if self.__waiting:
      self.results.append(result)
      self.__waiting -= 1
  
  def run(self, log):
    if self.__phase <= self.__maxphase:
      getattr(self, 'phase{0}'.format(self.__phase))(log)
      self.__phase += 1

class TaskPool(multiprocessing.pool.Pool): # pylint: disable-msg=W0223
  def __init__(self, *args, **kwargs):
    super(TaskPool, self).__init__(*args, **kwargs)
    self.__queue = []
    self.__waiting = {}
    self.__results = []
    self.__busy = 0
    self.__event = threading.Event()
    
  def __finished(self, result):
    if result is None:
      return
    if result.subtasks:
      index = 0
      while index in self.__waiting:
        index += 1
      self.__waiting[index] = result
      for sub in result.subtasks:
        sub.parent = index 
      self.__addTasks(result.subtasks, prepend=True)
      result._wait()
    elif not result.done:
      self.__addTasks((result,), prepend=True)
    elif result.parent is not None:
      parent = self.__waiting[result.parent]
      parent._collect(result)
      if not parent.waiting: 
        self.__finished(parent)
    else:
      self.__results.append(result)
      self.__event.set()
  
  def __callback(self, result):
    self.__finished(result)
    if self.__queue:
      self.apply_async(process_task, (self.__queue.pop(0),), callback=self.__callback)
    else:
      self.__busy -= 1
  
  def __addTasks(self, tasks, prepend=False):
    if prepend:
      self.__queue = list(tasks) + self.__queue
    else:
      self.__queue += list(tasks)
    while self.__queue and self.__busy < len(self._pool):
      self.__busy += 1
      self.apply_async(process_task, (self.__queue.pop(0),), callback=self.__callback)
  
  def add(self, *tasks):
    self.__addTasks(tasks)
  
  def run(self, *tasks):
    self.__addTasks(tasks)
    while self.__busy or self.__queue:
      self.__event.clear()
      self.__event.wait()
      while self.__results:
        yield self.__results.pop(0)