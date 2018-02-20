import cairo
import colorsys

TITLE_HEIGHT = 35
ROW_HEIGHT = 30
COLOUR_BLACK = (0.1,0.1,0.1)
COLOUR_SAMPLE = (0.7, 0.7, 0.9)

LABEL_X_OFFSET = 4
LABEL_offset_y = 4

class RenderContext:
	def __init__(self, cr, width, height, start_time, finish_time):
		self.cr = cr
		self.width = float(width)
		self.height = float(height)
		self.start_time = start_time
		self.finish_time = finish_time
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

def render_text(cr, label, font_size, x, y, width = None):
	# render label using x,y as top-left co-ords
	cr.select_font_face("Arial", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
	cr.set_font_size(font_size)

	(label_x, label_y, label_width, label_height, label_dx, label_dy) = cr.text_extents(label) 

	if width and (label_width>width):
		return

	cr.move_to(x + LABEL_X_OFFSET,y + LABEL_offset_y + label_height)
	cr.show_text(label) 

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
		cr.rectangle(start_x,y, width, ROW_HEIGHT * call_stack_depth)
		cr.fill()
	else:
		# filled rectangle
		cr.set_source_rgb(*render_context.sample_colour)
		cr.rectangle(start_x,y, width, ROW_HEIGHT)
		cr.fill()

		# black outline
		cr.set_source_rgb(*COLOUR_BLACK)
		cr.rectangle(start_x,y, width, ROW_HEIGHT)
		cr.stroke()

		if width > 10:
			# function name
			label = sample.get_function().get_label()
			render_text(cr, label, 13, start_x, y, width)

		# recursive calls
		children = sample.get_children()
		for child in children:
			if not render_sample( render_context, child, y+ROW_HEIGHT):
				return False

	return True

class ProfileRenderThread:

	def __init__(self, thread_data, colour, background_colour):
		self._thread_data = thread_data
		self._colour = colour
		self._background_colour = background_colour
		self._height = TITLE_HEIGHT + (self._thread_data.get_max_stack_depth() * ROW_HEIGHT)

	def render(self, render_context):
		cr = render_context.cr

		# render background colour
		cr.set_source_rgb(*self._background_colour)
		cr.rectangle(0, 0, render_context.width, self._height)
		cr.fill()

		# render title
		title = self._thread_data.get_label()
		cr.set_source_rgb(*COLOUR_BLACK)
		render_text(cr, title, 17, 0, 0)

		# render samples
		render_context.sample_colour = self._colour
		
		samples = self._thread_data.get_samples()
		for sample in samples:
			if not render_sample(render_context, sample, TITLE_HEIGHT):
				break
			

	def get_height(self):
		""" return the height of this thread on screen, in pixels """
		return self._height

class ProfileRender:
	""" Render the data for a profiling session """

	def __init__(self, profile_data):
		self._width = 0.0
		self._height = 0.0
		self._profile_data = profile_data
		
		self._offset_y = 0

		self._render_threads = []

 		# time at left edge of the window
		self._start_time = profile_data.get_start_time()

		# time at right edge of the window
		self._finish_time = profile_data.get_finish_time()

		num_threads = profile_data.get_num_threads()

		for i in range(num_threads):
			thread_data = profile_data.get_thread(i)
			background_colour =  (1.0,1.0,1.0) if (i%2) else (243.0/255.0,245.0/255.0,220.0/255.0)
			colour = colorsys.hls_to_rgb(float(i+1) / float(num_threads), 0.5, 0.5)
			render_thread = ProfileRenderThread(thread_data, colour, background_colour)
			self._render_threads.append( render_thread )


	def render(self, cr):

		# Fill the background with white
		cr.set_source_rgb(1.0, 1.0, 1.0)
		cr.rectangle(0, 0, self._width, self._height)
		cr.fill()

		offset_y = self._offset_y
		offset_x = 0

		render_context = RenderContext( cr, self._width, self._height, self._start_time, self._finish_time)

		for render_thread in self._render_threads:

			if offset_y > self._height:
				break

			if (offset_y + render_thread.get_height()) > 0:
				cr.save()
				cr.translate(offset_x,offset_y)
				render_thread.render(render_context)
				cr.restore()

			offset_y += render_thread.get_height()


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
		profile_render_height = self._get_render_height()
		offset_y = self._offset_y
		bottom = self._offset_y + profile_render_height
		if bottom < self._height:
			offset_bottom = self._height - bottom
			offset_y += offset_bottom

		offset_y = min(0, offset_y)
		self._offset_y = offset_y

	def _get_render_height(self):
		# get the combined height of all the render threads
		render_height = 0

		for render_thread in self._render_threads:
			render_height += render_thread.get_height()
		
		return render_height