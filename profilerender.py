import cairo
import colorsys

TITLE_HEIGHT = 25
EVENT_LABEL_HEIGHT = 20
SAMPLE_HEIGHT = 40
COLOUR_BLACK = (0.1,0.1,0.1)
COLOUR_WHITE = (1,1,1)

LABEL_X_OFFSET = 4
LABEL_OFFSET_Y = 4

TEXT_SIZE_LABEL = 13
TEXT_SIZE_TITLE = 17
TEXT_SIZE_DURATION = 10

TEXT_LABEL_DURATION_OFFSET_Y = 20

TEXT_SIZE_EVENT_LABEL = 10
EVENT_LABEL_OFFSET_X = 1
EVENT_LABEL_OFFSET_Y = 1

COUNTER_ROW_HEIGHT = 100

class RenderContext:
	def __init__(self, cr, width, height, start_time, finish_time, offset_x, offset_y):
		self.cr = cr
		self.width = float(width)
		self.height = float(height)
		self.start_time = start_time
		self.finish_time = finish_time
		self.offset_x = offset_x
		self.offset_y = offset_y
		self._duration = max(0.001, float(finish_time - start_time))

	def get_x_for_time(self, time):
		if time <= self.start_time:
			return 0
		elif time >= self.finish_time:
			return self.width
		else:
			return (time-self.start_time) * self.width / self._duration

	def is_sample_visible(self, sample):
		return not((sample.get_finish_time() < self.start_time) or (sample.get_start_time() > self.finish_time))

	def is_sample_off_right_of_screen(self, sample):
		return sample.get_start_time() > self.finish_time
	
	def is_event_visible(self, event_sample):
		time = event_sample.get_time()
		return (time > self.start_time) and (time < self.finish_time)
	
	def is_event_off_right_of_screen(self, event_sample):
		time = event_sample.get_time()
		return (time > self.finish_time)

def render_text(cr, label, font_size, x, y, width = None):
	# render label using x,y as top-left co-ords
	cr.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
	cr.set_font_size(font_size)

	(label_x, label_y, label_width, label_height, label_dx, label_dy) = cr.text_extents(label) 

	if width and (label_width > (width-LABEL_X_OFFSET)):
		return

	cr.move_to(x + LABEL_X_OFFSET,y + LABEL_OFFSET_Y + label_height)
	cr.show_text(label)

	return (label_width, label_height)

def render_sample(render_context, sample, y):
	if not render_context.is_sample_visible(sample):
		return not render_context.is_sample_off_right_of_screen(sample)

	cr = render_context.cr

	start_time = sample.get_start_time()
	finish_time = sample.get_finish_time()
	
	start_x = render_context.get_x_for_time(start_time)
	finish_x = render_context.get_x_for_time(finish_time)

	width = finish_x - start_x

	# make sure we always render at least something for a sample
	width = max(width,0.5)

	if width < 4:
		# filled rectangle for this sample + all its' children
		call_stack_depth = sample.get_child_call_stack_depth() + 1
		
		cr.set_source_rgb(*render_context.sample_colour)
		cr.rectangle(start_x,y, width, SAMPLE_HEIGHT * call_stack_depth)
		cr.fill()
	else:
		# filled rectangle
		cr.set_source_rgb(*render_context.sample_colour)
		cr.rectangle(start_x,y, width, SAMPLE_HEIGHT)
		cr.fill()

		# black outline
		cr.set_source_rgb(*COLOUR_BLACK)
		cr.rectangle(start_x,y, width, SAMPLE_HEIGHT)
		cr.stroke()

		if width > 10:
			# function name
			label = sample.get_function().get_label()
			render_text(cr, label, TEXT_SIZE_LABEL, start_x, y, width)

			duration = sample.get_duration()
			
			duration_label = '%.3fms' % ( sample.get_duration() / 1000.0 )
			render_text(cr, duration_label, TEXT_SIZE_DURATION, start_x, y + TEXT_LABEL_DURATION_OFFSET_Y, width)

		# recursive calls
		children = sample.get_children()
		for child in children:
			if not render_sample( render_context, child, y+SAMPLE_HEIGHT):
				return False

	return True

def render_event(render_context, event_sample, y, height):
	if not render_context.is_event_visible(event_sample):
		return not render_context.is_event_off_right_of_screen(event_sample)
	
	cr = render_context.cr

	time = event_sample.get_time()
	x = render_context.get_x_for_time(time)
	
	cr.set_source_rgb(*COLOUR_WHITE)
	cr.move_to(x,y)
	cr.line_to(x,y+height)
	cr.set_line_width(3)
	cr.stroke()

	cr.set_source_rgb(*COLOUR_BLACK)
	cr.move_to(x,y)
	cr.line_to(x,y+height)
	cr.set_line_width(2)
	cr.stroke()

	event = event_sample.get_event()
	label = event.get_label()
	(label_width, label_height) = render_text(cr, label, TEXT_SIZE_EVENT_LABEL, x + EVENT_LABEL_OFFSET_X, y + EVENT_LABEL_OFFSET_Y)

	cr.move_to(x,y)
	cr.line_to(x + EVENT_LABEL_OFFSET_X + label_width, y)
	cr.stroke()

class ProfileRenderCounter:

	def __init__(self, counter_data, colour, background_colour):
		self._counter_data = counter_data
		self._colour = colour
		self._background_colour = background_colour
		self._height = TITLE_HEIGHT + COUNTER_ROW_HEIGHT
			
	def render(self, render_context):
		cr = render_context.cr
		counter_data = self._counter_data

		# render background colour
		cr.set_source_rgb(*self._background_colour)
		cr.rectangle(0, 0, render_context.width, self._height)
		cr.fill()

		# render title
		title = "Counter: " + counter_data.get_label()
		cr.set_source_rgb(*COLOUR_BLACK)
		render_text(cr, title, TEXT_SIZE_TITLE, 0, 0)

		# render values		
		samples = counter_data.get_samples()		
		if len(samples) > 0:		
			cr.set_source_rgb(*self._colour)

			max_value = counter_data.get_max_value()
			min_value = counter_data.get_min_value()
			y_scale = float(COUNTER_ROW_HEIGHT) / (max_value-min_value)
			min_value_height = -min_value * y_scale

			cr.translate(0, TITLE_HEIGHT)
			
			def render_sample(cr, last_x, x, value):
				value_height = float(value) * y_scale
				if value >= 0:
					cr.rectangle(last_x, COUNTER_ROW_HEIGHT - min_value_height - value_height, 1+x-last_x, value_height)
				else:
					value_height = -value_height
					cr.rectangle(last_x, COUNTER_ROW_HEIGHT - min_value_height, 1+x-last_x, value_height)
				cr.fill()				

			last_sample = samples[0]

			for sample in samples:
				last_x = render_context.get_x_for_time(last_sample.get_time())
				x = render_context.get_x_for_time(sample.get_time())
				value = last_sample.get_value()

				render_sample(cr, last_x, x, value)				

				last_sample = sample

			end_x = render_context.get_x_for_time(render_context.finish_time)

			# render the last sample
			last_x = render_context.get_x_for_time(last_sample.get_time())
			value = last_sample.get_value()
			render_sample(cr, last_x, end_x, value)
			
			# render the x-axis
			line_y = COUNTER_ROW_HEIGHT - min_value_height
			cr.set_line_width(1)
			cr.move_to(0, line_y)
			cr.line_to(end_x, line_y)
			cr.stroke()
	
	def get_height(self):
		return self._height

class ProfileRenderThread:

	def __init__(self, thread_data, colour, background_colour):
		self._thread_data = thread_data
		self._colour = colour
		self._background_colour = background_colour
		self._height = TITLE_HEIGHT + EVENT_LABEL_HEIGHT + (self._thread_data.get_max_stack_depth() * SAMPLE_HEIGHT)

	def render(self, render_context):
		cr = render_context.cr

		# render background colour
		cr.set_source_rgb(*self._background_colour)
		cr.rectangle(0, 0, render_context.width, self._height)
		cr.fill()

		# render title
		title = "Thread: " + self._thread_data.get_label()
		cr.set_source_rgb(*COLOUR_BLACK)
		render_text(cr, title, TEXT_SIZE_TITLE, 0, 0)

		# render samples
		render_context.sample_colour = self._colour
		
		samples = self._thread_data.get_samples()
		for sample in samples:
			if not render_sample(render_context, sample, TITLE_HEIGHT + EVENT_LABEL_HEIGHT):
				break
		
		# render events
		event_samples = self._thread_data.get_event_samples()
		event_height = self.get_height()
		for event_sample in event_samples:
			if not render_event(render_context, event_sample, TITLE_HEIGHT, event_height):
				break			

	def get_height(self):
		""" return the height of this thread on screen, in pixels """
		return self._height

class ProfileRenderObjects:

	def __init__(self, profile_data):
		self._counters = []
		self._threads = []

		num_counters = profile_data.get_num_counters()
		num_threads = profile_data.get_num_threads()
		num_rows = num_counters + num_threads

		row_index_mutable = [0]
		def get_row_colours():
			row_index = row_index_mutable[0]
			background_colour =  (1.0,1.0,1.0) if (row_index % 2) else (243.0/255.0,245.0/255.0,220.0/255.0)
			colour = colorsys.hls_to_rgb(float(row_index+1) / float(num_rows), 0.5, 0.5)
			row_index_mutable[0] += 1
			return (background_colour, colour)
		
		for i in range(num_counters):
			counter_data = profile_data.get_counter(i)
			(background_colour, colour) = get_row_colours()			
			render_counter = ProfileRenderCounter(counter_data, colour, background_colour)
			self._counters.append( render_counter )
		 				
		for i in range(num_threads):
			thread_data = profile_data.get_thread(i)
			(background_colour, colour) = get_row_colours()			
			render_thread = ProfileRenderThread(thread_data, colour, background_colour)
			self._threads.append( render_thread )

		self._render_height = self._calculate_render_height()
		
	def _render_background(self, render_context):
		# Fill the background with white
		cr = render_context.cr

		cr.set_source_rgb(1.0, 1.0, 1.0)
		cr.rectangle(0, 0, render_context.width, render_context.height)
		cr.fill()

	def render(self, render_context):		
		cr = render_context.cr
		self._render_background(render_context)
		self._render_counters(render_context)
		self._render_threads(render_context)

	def _render_counters(self, render_context):
		cr = render_context.cr
		offset_x = render_context.offset_x
		offset_y = render_context.offset_y

		for render_counter in self._counters:
			if offset_y > render_context.height:
				break
			
			if (offset_y + render_counter.get_height()) > 0:
				cr.save()
				cr.translate(offset_x,offset_y)
				render_counter.render(render_context)
				cr.restore()

			offset_y += render_counter.get_height()

		render_context.offset_x = offset_x
		render_context.offset_y = offset_y

	def _render_threads(self, render_context):
		cr = render_context.cr
		offset_x = render_context.offset_x
		offset_y = render_context.offset_y

		for render_thread in self._threads:
			if offset_y > render_context.height:
				break

			if (offset_y + render_thread.get_height()) > 0:
				cr.save()
				cr.translate(offset_x,offset_y)
				render_thread.render(render_context)
				cr.restore()

			offset_y += render_thread.get_height()
		
		render_context.offset_x = offset_x
		render_context.offset_y = offset_y
	
	def _calculate_render_height(self):
		# get the combined height of all the render counters & threads
		render_height = 0

		for counter in self._counters:
			render_height += counter.get_height()

		for thread in self._threads:
			render_height += thread.get_height()	
		
		return render_height
	
	def get_render_height(self):
		return self._render_height

class ProfileRender:
	""" Render the data for a profiling session """

	def __init__(self, profile_data):
		self._width = 0.0
		self._height = 0.0
		self._profile_data = profile_data

		self._profile_data_objects = ProfileRenderObjects(profile_data)
		
		self._offset_y = 0
						
		# initialise times at the left + right edges of the window
		self._start_time = profile_data.get_start_time()
		self._finish_time = profile_data.get_finish_time()

	def render(self, cr):								
		offset_y = self._offset_y
		offset_x = 0

		render_context = RenderContext( cr, self._width, self._height, self._start_time, self._finish_time, offset_x, offset_y)
		
		self._profile_data_objects.render(render_context )

	def render_pointer(self, cr, pointer):
		(x,y) = pointer
		t = self._get_time_at_x(x)
		
		cr.set_source_rgb(0.0, 0.0, 0.0)
		cr.move_to(x,0)
		cr.line_to(x, self._height)
		cr.stroke()

	def resize(self, width, height):
		self._width = float(width)
		self._height = float(height)

		self._validate_viewport()

	def pan_by(self, dx, dy):
		dt = self._get_dt_for_dx( dx )

		if dt > 0:
			dt = min(dt, self._start_time - self._profile_data.get_start_time())
		else:
			dt = max(dt, self._finish_time - self._profile_data.get_finish_time())

		self._start_time -= dt
		self._finish_time -= dt

		self._offset_y += dy

		self._validate_viewport()	

	def scale_at(self, scale_factor, x, y):
		x = float(x)

		x_time = self._get_time_at_x(x)

		self._start_time = x_time - ((x_time - self._start_time) / scale_factor)
		self._finish_time = x_time + ((self._finish_time - x_time) / scale_factor)

		self._validate_viewport()

	def _get_time_at_x(self, x):
		if x <= 0:
			return self._start_time
		elif x >= self._width:
			return self._finish_time
		else:
			duration = self._finish_time - self._start_time
			return ((x/self._width) * duration) + self._start_time

	def _get_dt_for_dx(self, dx):
		time_per_pixel = (self._finish_time - self._start_time) / self._width
		dt = dx * time_per_pixel
		return dt
	
	def _validate_viewport(self):
		# validate start / finish time
		profile_start_time = self._profile_data.get_start_time()
		profile_finish_time = self._profile_data.get_finish_time()

		if self._start_time < profile_start_time:
			self._start_time = profile_start_time

		if self._finish_time > profile_finish_time:
			self._finish_time = profile_finish_time	
		
		# validate offset_y		
		profile_render_height = self._profile_data_objects.get_render_height()
		offset_y = self._offset_y
		bottom = self._offset_y + profile_render_height
		if bottom < self._height:
			offset_bottom = self._height - bottom
			offset_y += offset_bottom

		offset_y = min(0, offset_y)
		self._offset_y = offset_y
