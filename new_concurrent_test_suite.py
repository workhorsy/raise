#!/usr/bin/env python

#import unittest
import os, sys
import inspect
import threading
import time
import multiprocessing



class TestCase(object):
	def assertEqual(self, a, b):
		if a == b:
			return
		raise AssertionError("{0} != {1}".format(a, b))

class TestThread(threading.Thread):
	def run(self):
		try:
			threading.Thread.run(self)
		except Exception as self.err:
			pass
		else:
			self.err = None

class ConcurrentTestRunner(object):
	def __init__(self):
		self.test_cases = []
		self.fails = []

	def add(self, test_case):
		self.test_cases.append(test_case)

	def run(self):
		cpus_total = multiprocessing.cpu_count()
		cpus_free = cpus_total
		threads = []

		for test_case_cls in self.test_cases:
			test_case = test_case_cls()
			members = inspect.getmembers(test_case, predicate=inspect.ismethod)
			
			for name, member in members:
				if not name.startswith('test_'):
					continue

				t = TestThread(target=member)
				threads.append(t)

		running_threads = []
		while True:
			while cpus_free and threads:
				t = threads.pop()
				t.start()
				running_threads.append(t)
				cpus_free -= 1

			for t in running_threads[:]:
				#print(cpus_free, len(threads), len(running_threads))
				if t.isAlive():
					continue

				cpus_free += 1
				running_threads.remove(t)
				t.join()
				if t.err:
					self.fails.append(t.err)
					sys.stdout.write('F')
				else:
					sys.stdout.write('.')
				sys.stdout.flush()

			if not threads and not running_threads:
				break

			time.sleep(0.2)

		sys.stdout.write('\n')
		for fail in self.fails:
			print(fail)

def fib(n):
	if n == 0:
		return 0
	elif n == 1:
		return 1
	return fib(n - 1) + fib(n - 2)

class FibonacciTestCase(TestCase):
	def test_a(self):
		self.assertEqual(fib(30), 1346269)

	def test_b(self):
		self.assertEqual(fib(31), 1346269)

	def test_c(self):
		self.assertEqual(fib(32), 1346269)

	def test_d(self):
		self.assertEqual(fib(33), 1346269)

if __name__ == '__main__':
	runner = ConcurrentTestRunner()
	for cls in TestCase.__subclasses__():
		runner.add(cls)
	runner.run()

