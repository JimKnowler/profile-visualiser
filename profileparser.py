class ProfileParser:

	def __init__(self, consumer):
		self._consumer = consumer

	def load_file(self, filename):
		with open(filename, "r") as file:
			for line_number, line in enumerate(file):
				try:
					line = line.rstrip()
					self.parse(line)
				except Exception as e:
					print "exception while parsing line ", line_number
					print ">> line: [", line, "]"
					print ">>", e
					raise e

	def parse(self, line):
		if line.startswith('#'):
			# ignore comment lines
			return

		split_line = line.split(' ',1)
		line_type = split_line[0]

		if line_type == 'T':
			split_line = line.split(' ',2)

			thread_id = int(split_line[1])
			thread_label = split_line[2]

			self._consumer.on_thread(thread_id, thread_label)
		elif line_type == 'F':
			split_line = line.split(' ',3)

			thread_id = int(split_line[1])
			function_id = int(split_line[2])
			function_label = split_line[3]

			self._consumer.on_function(thread_id, function_id, function_label)
		elif line_type == 'S':
			split_line = line.split(' ',3)
			
			thread_id = int(split_line[1])
			function_id = int(split_line[2])
			time = int(split_line[3])

			self._consumer.on_sample_start(thread_id, function_id, time)
		elif line_type == 'E':
			split_line = line.split(' ',3)
			
			thread_id = int(split_line[1])
			function_id = int(split_line[2])
			time = int(split_line[3])

			self._consumer.on_sample_finish(thread_id, function_id, time)
		elif line_type == 'V':
			split_line = line.split(' ',3)

			thread_id = int(split_line[1])
			event_id = int(split_line[2])
			event_label = split_line[3]

			self._consumer.on_event(thread_id, event_id, event_label)
		elif line_type == 'Y':
			split_line = line.split(' ',3)
			
			thread_id = int(split_line[1])
			event_id = int(split_line[2])
			time = int(split_line[3])

			self._consumer.on_event_emit(thread_id, event_id, time)
