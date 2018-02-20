

class FunctionData:
	def __init__(self, id, label):
		self._id = id
		self._label = label

	def get_id(self):
		return self._id

	def get_label(self):
		return self._label

class SampleData:
	def __init__(self, function, start_time, call_stack_depth):
		self._function = function
		self._start_time = start_time
		self._finish_time = None
		self._duration = 0
		self._children = []
		self._parent = None
		self._call_stack_depth = call_stack_depth
		self._child_call_stack_depth = 0

	def get_children(self):
		return self._children

	def get_num_children(self):
		return len(self._children)

	def set_finish_time(self, finish_time):
		self._finish_time = finish_time
		self._duration = self._finish_time - self._start_time

	def set_parent(self, parent):
		self._parent = parent
		self._parent._on_child_call_stack_depth(self._call_stack_depth)
		
	def _on_child_call_stack_depth(self, call_stack_depth):
		child_call_stack_depth = call_stack_depth - self._call_stack_depth
		
		if self._child_call_stack_depth < child_call_stack_depth:
			self._child_call_stack_depth = child_call_stack_depth
			if self._parent:
				self._parent._on_child_call_stack_depth( call_stack_depth )		

	def get_parent(self):
		return self._parent

	def get_start_time(self):
		return self._start_time

	def get_finish_time(self):
		return self._finish_time
	
	def get_duration(self):
		return self._duration

	def get_function(self):
		return self._function
	
	def get_call_stack_depth(self):
		return self._call_stack_depth
	
	def get_child_call_stack_depth(self):
		return self._child_call_stack_depth

class ThreadData:
	def __init__(self, id, label):
		self._id = id
		self._label = label
		self._functions = []
		self._samples = []
		self._active_sample = None
		self._active_stack_depth = 0
		self._max_stack_depth = 0
		self._start_time = None
		self._finish_time = None

	def get_id(self):
		return self._id

	def get_label(self):
		return self._label

	def add_function(self, function_data):
		self._functions.append(function_data)

	def get_num_functions(self):
		return len(self._functions)

	def get_function(self, index):
		return self._functions[index]

	def get_samples(self):
		return self._samples

	def on_sample_start(self, function_id, start_time):
		function = self._functions[function_id]		
		sample_data = SampleData(function, start_time, self._active_stack_depth)
		if self._active_sample:
			sample_data.set_parent(self._active_sample)
			self._active_sample.get_children().append(sample_data)
		else:
			self._samples.append(sample_data)

		self._active_sample = sample_data
		self._active_stack_depth += 1
		self._max_stack_depth = max(self._max_stack_depth, self._active_stack_depth)

		if self._start_time == None:
			self._start_time = start_time

	def on_sample_finish(self, function_id, finish_time):
		# @todo - check that active sample has matching function_id
		self._active_sample.set_finish_time(finish_time)

		self._active_sample = self._active_sample.get_parent()
		self._active_stack_depth -= 1

		self._finish_time = finish_time

	def get_max_stack_depth(self):
		return self._max_stack_depth

	def get_start_time(self):
		return self._start_time

	def get_finish_time(self):
		return self._finish_time

	def merge(self, other):
		self._max_stack_depth = max(self._max_stack_depth, other._max_stack_depth)
		self._start_time = min(self._start_time, other._start_time)
		self._finish_time = max(self._finish_time, other._finish_time)
		num_functions = len(self._functions)
		self._functions.extend(other._functions)
		self._samples.extend(other._samples)

	def debug_tty(self):
		print "Thread:", self._label
		print " Max Stack Depth:", self._max_stack_depth
		print " Start Time:", self._start_time
		print " Finish Time:", self._finish_time

class ProfileData:
	def __init__(self):
		self._threads = []
		self._start_time = None
		self._finish_time = None

	def on_thread(self, thread_id, thread_label):
		thread_data = ThreadData(thread_id, thread_label)
		self._threads.append( thread_data )

	def get_num_threads(self):
		return len(self._threads)

	def get_thread(self, index):
		return self._threads[index]

	def on_function(self, thread_id, function_id, function_label):
		function_data = FunctionData(function_id, function_label)
		self._threads[thread_id].add_function( function_data )

	def on_sample_start(self, thread_id, function_id, start_time):
		self._threads[thread_id].on_sample_start(function_id, start_time)

		if (self._start_time==None):
			self._start_time = start_time
		#	self._finish_time = finish_time

	def on_sample_finish(self, thread_id, function_id, finish_time):
		self._threads[thread_id].on_sample_finish(function_id, finish_time)

		self._finish_time = finish_time

	def get_start_time(self):
		return self._start_time

	def get_finish_time(self):
		return self._finish_time

	def merge_restarted_threads(self):
		""" merge threads that have the same label, and non-overlapping start/finish times """

		i = 0
		while (i < len(self._threads)):
			thread_data = self._threads[i]

			j = i+1
			while (j < len(self._threads)):
				merge_thread_data = self._threads[j]

				if (thread_data.get_label() == merge_thread_data.get_label()) and (merge_thread_data.get_start_time() >= thread_data.get_finish_time()):
					# merge together
					thread_data.merge( merge_thread_data )

					# remove merge_thread_data
					self._threads.pop(j)

				else:
					j += 1

			i += 1
	
	def debug_tty(self):
		print " Start Time:", self._start_time
		print "Finish Time:", self._finish_time
		for thread in self._threads:
			thread.debug_tty()
