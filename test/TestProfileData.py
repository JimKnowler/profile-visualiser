import nose

import sys
sys.path.insert(0,'..')

from profiledata import ProfileData
from nose.tools import *

class TestProfileData:
	
	def test_should_construct(self):
		profile_data = ProfileData()

	def test_should_consume_thread_data(self):
		profile_data = ProfileData()
		assert_equals(0, profile_data.get_num_threads())

		profile_data.on_thread(0, "my thread")
		assert_equals(1, profile_data.get_num_threads())
		thread_data = profile_data.get_thread(0)
		assert_equals(0, thread_data.get_id())
		assert_equals("my thread", thread_data.get_label())

		profile_data.on_thread(1, "another thread")
		assert_equals(2, profile_data.get_num_threads())
		thread_data_2 = profile_data.get_thread(1)
		assert_equals(1, thread_data_2.get_id())
		assert_equals("another thread", thread_data_2.get_label())

		assert_equals(0, thread_data.get_max_stack_depth())
		assert_equals(0, thread_data_2.get_max_stack_depth())

	def test_should_consume_function_data(self):
		profile_data = ProfileData()
		profile_data.on_thread(0, "my thread")
		profile_data.on_thread(1, "my second thread")

		profile_data.on_function(0, 0, "my first function")
		profile_data.on_function(0, 1, "my second function")
		profile_data.on_function(1, 0, "2nd thread first function")
		profile_data.on_function(0, 2, "my third function")

		thread_data_1 = profile_data.get_thread(0)
		thread_data_2 = profile_data.get_thread(1)

		assert_equals(3, thread_data_1.get_num_functions())
		assert_equals(1, thread_data_2.get_num_functions())

		function_data = thread_data_1.get_function(0)
		assert_equals(0, function_data.get_id())
		assert_equals("my first function", function_data.get_label())

		function_data = thread_data_1.get_function(1)
		assert_equals(1, function_data.get_id())
		assert_equals("my second function", function_data.get_label())

		function_data = thread_data_1.get_function(2)
		assert_equals(2, function_data.get_id())
		assert_equals("my third function", function_data.get_label())

		function_data = thread_data_2.get_function(0)
		assert_equals(0, function_data.get_id())
		assert_equals("2nd thread first function", function_data.get_label())

		assert_equals(0, thread_data_1.get_max_stack_depth())
		assert_equals(0, thread_data_2.get_max_stack_depth())

	def test_should_consume_sample_data(self):
		profile_data = ProfileData()
		profile_data.on_thread(0, "my thread")
		profile_data.on_function(0, 0, "my first function")
		thread_data = profile_data.get_thread(0)
		function_data = thread_data.get_function(0)
		assert_equals(0, len(thread_data.get_samples()))

		profile_data.on_sample_start(0,0,10)
		assert_equals(1, len(thread_data.get_samples()))
		sample = thread_data.get_samples()[0]
		assert_equals(10, sample.get_start_time())
		assert_equals(None, sample.get_finish_time())
		assert_equals(None, sample.get_parent())
		assert_equals(function_data, sample.get_function())

		assert_equals(1, thread_data.get_max_stack_depth())

		profile_data.on_sample_finish(0,0,12)
		assert_equals(1, len(thread_data.get_samples()))
		assert_equals(10, sample.get_start_time())
		assert_equals(12, sample.get_finish_time())
		assert_equals(None, sample.get_parent())
		assert_equals(function_data, sample.get_function())

		assert_equals(1, thread_data.get_max_stack_depth())

	def test_should_consume_sample_data_for_multiple_threads(self):
		profile_data = ProfileData()
		profile_data.on_thread(0, "my thread")
		profile_data.on_thread(1, "another thread")

		profile_data.on_function(0, 0, "my first function")
		profile_data.on_function(0, 1, "my second function")
		profile_data.on_function(1, 0, "2nd thread first function")
		profile_data.on_function(0, 2, "my third function")

		# sample a function call
		profile_data.on_sample_start(0,2,5)
		profile_data.on_sample_finish(0,2,100)

		# sample a function call that calls other functions
		profile_data.on_sample_start(0,0,200)
		profile_data.on_sample_start(0,1,300)
		profile_data.on_sample_finish(0,1,310)
		profile_data.on_sample_start(0,2,320)
		profile_data.on_sample_finish(0,2,330)
		profile_data.on_sample_start(0,1,340)
		profile_data.on_sample_finish(0,1,350)
		profile_data.on_sample_finish(0,0,400)

		# sample a recursive function call on the second thread
		profile_data.on_sample_start(1,0,100)
		profile_data.on_sample_start(1,0,200)
		profile_data.on_sample_start(1,0,300)
		profile_data.on_sample_finish(1,0,400)
		profile_data.on_sample_finish(1,0,500)
		profile_data.on_sample_finish(1,0,600)

		thread_data_1 = profile_data.get_thread(0)
		thread_data_2 = profile_data.get_thread(1)

		# check the samples received for thread 0
		samples = thread_data_1.get_samples()
		assert_equals(2, len(samples))
		assert_equals(thread_data_1.get_function(2), samples[0].get_function())
		assert_equals(0, samples[0].get_num_children())
		assert_equals(5, samples[0].get_start_time())
		assert_equals(100, samples[0].get_finish_time())
		assert_equals(thread_data_1.get_function(0), samples[1].get_function())
		assert_equals(3, samples[1].get_num_children())
		assert_equals(200, samples[1].get_start_time())
		assert_equals(400, samples[1].get_finish_time())
		children = samples[1].get_children()
		assert_equals(3, len(children))
		assert_equals(thread_data_1.get_function(1), children[0].get_function())
		assert_equals(300, children[0].get_start_time())
		assert_equals(310, children[0].get_finish_time())
		assert_equals(2, children[1].get_function().get_id())
		assert_equals(320, children[1].get_start_time())
		assert_equals(330, children[1].get_finish_time())
		assert_equals(thread_data_1.get_function(1), children[2].get_function())
		assert_equals(340, children[2].get_start_time())
		assert_equals(350, children[2].get_finish_time())

		assert_equals(2, thread_data_1.get_max_stack_depth())
		
		assert_equals(5, thread_data_1.get_start_time())
		assert_equals(400, thread_data_1.get_finish_time())

		
		# check the recursive samples parsed for thread 1
		samples = thread_data_2.get_samples()
		assert_equals(1, len(samples))
		assert_equals(thread_data_2.get_function(0), samples[0].get_function())
		assert_equals(1, samples[0].get_num_children())
		assert_equals(100, samples[0].get_start_time())
		assert_equals(600, samples[0].get_finish_time())
		children = samples[0].get_children()
		assert_equals(1, len(children))
		assert_equals(thread_data_2.get_function(0), children[0].get_function())
		assert_equals(1, children[0].get_num_children())
		assert_equals(200, children[0].get_start_time())
		assert_equals(500, children[0].get_finish_time())
		children = children[0].get_children()
		assert_equals(1, len(children))
		assert_equals(thread_data_2.get_function(0), children[0].get_function())
		assert_equals(0, children[0].get_num_children())
		assert_equals(300, children[0].get_start_time())
		assert_equals(400, children[0].get_finish_time())

		assert_equals(3, thread_data_2.get_max_stack_depth())

		assert_equals(100, thread_data_2.get_start_time())
		assert_equals(600, thread_data_2.get_finish_time())

		# check the start/finish times for the profile data
		assert_equals(5, profile_data.get_start_time())
		assert_equals(600, profile_data.get_finish_time())

	def test_should_merge_restarted_threads(self):
		profile_data = ProfileData()
		profile_data.on_thread(0, "my duplicate thread")
		profile_data.on_thread(1, "another thread")
		profile_data.on_thread(2, "my duplicate thread")		# should merge with thread 0
		profile_data.on_thread(3, "yet another thread")
		profile_data.on_thread(4, "my duplicate thread")		# should not merge with thread 0, 
																#   due to events that overlap with thread 2
		profile_data.on_thread(5, "my duplicate thread")		# should merge with thread 0


		profile_data.on_function(0, 0, "my first function")
		profile_data.on_function(1, 0, "my second function")
		profile_data.on_function(2, 0, "my third function")
		profile_data.on_function(3, 0, "my fourth function")
		profile_data.on_function(4, 0, "my fifth function")
		profile_data.on_function(5, 0, "my sixth function")

		# sample function calls on each thread
		profile_data.on_sample_start(0,0,5)
		profile_data.on_sample_finish(0,0,100)

		profile_data.on_sample_start(1,0,110)
		profile_data.on_sample_finish(1,0,200)

		profile_data.on_sample_start(2,0,205)
		profile_data.on_sample_start(2,0,210)					# note: recursive function call on thread 2
		profile_data.on_sample_finish(2,0,295)
		profile_data.on_sample_finish(2,0,300)

		profile_data.on_sample_start(3,0,305)
		profile_data.on_sample_finish(3,0,400)

		profile_data.on_sample_start(4,0,299)					# overlaps with thread 2
		profile_data.on_sample_finish(4,0,350)

		profile_data.on_sample_start(5,0,300)
		profile_data.on_sample_finish(5,0,600)

		# test number of threads before merge
		assert_equals(6, profile_data.get_num_threads())

		# test number of threads after merge
		profile_data.merge_restarted_threads()
		assert_equals(4, profile_data.get_num_threads())

		# test labels and num function calls on threads after merge
		# test max_stack_depth on merged threads

		thread_data_1 = profile_data.get_thread(0)
		assert_equals("my duplicate thread", thread_data_1.get_label())
		assert_equals(2, thread_data_1.get_max_stack_depth())
		assert_equals(3, len(thread_data_1.get_samples()))
		assert_equals(5, thread_data_1.get_start_time())
		assert_equals(600, thread_data_1.get_finish_time())

		thread_data_2 = profile_data.get_thread(1)
		assert_equals("another thread", thread_data_2.get_label())
		assert_equals(1, thread_data_2.get_max_stack_depth())
		assert_equals(1, len(thread_data_2.get_samples()))
		assert_equals(110, thread_data_2.get_start_time())
		assert_equals(200, thread_data_2.get_finish_time())
		
		thread_data_3 = profile_data.get_thread(2)
		assert_equals("yet another thread", thread_data_3.get_label())
		assert_equals(1, thread_data_3.get_max_stack_depth())
		assert_equals(1, len(thread_data_3.get_samples()))
		assert_equals(305, thread_data_3.get_start_time())
		assert_equals(400, thread_data_3.get_finish_time())

		thread_data_4 = profile_data.get_thread(3)
		assert_equals("my duplicate thread", thread_data_4.get_label())
		assert_equals(1, thread_data_4.get_max_stack_depth())
		assert_equals(1, len(thread_data_4.get_samples()))
		assert_equals(299, thread_data_4.get_start_time())
		assert_equals(350, thread_data_4.get_finish_time())
		
	def test_should_track_sample_data_call_stack_depth(self):
		profile_data = ProfileData()
		profile_data.on_thread(0, "my thread")
		profile_data.on_function(0, 0, "my first function")

		# sample a function call
		profile_data.on_sample_start(0,0,5)
		profile_data.on_sample_finish(0,0,100)

		# sample a function call that calls other functions
		profile_data.on_sample_start(0,0,200)			# depth: 0
		profile_data.on_sample_start(0,0,300)			# depth: 1
		profile_data.on_sample_finish(0,0,310)			
		profile_data.on_sample_start(0,0,320)			# depth: 1
		profile_data.on_sample_finish(0,0,330)
		profile_data.on_sample_start(0,0,340)			# depth: 1
		profile_data.on_sample_start(0,0,342)			# depth: 2
		profile_data.on_sample_finish(0,0,346)
		profile_data.on_sample_finish(0,0,350)
		profile_data.on_sample_finish(0,0,400)

		thread_data_1 = profile_data.get_thread(0)

		# check the samples received for thread 0
		samples = thread_data_1.get_samples()
		
		assert_equals(0, samples[0].get_call_stack_depth())
		assert_equals(0, samples[0].get_child_call_stack_depth())
		
		assert_equals(0, samples[1].get_call_stack_depth())
		assert_equals(2, samples[1].get_child_call_stack_depth())
		
		children = samples[1].get_children()		
		assert_equals(1, children[0].get_call_stack_depth())
		assert_equals(0, children[0].get_child_call_stack_depth())
		assert_equals(1, children[1].get_call_stack_depth())
		assert_equals(0, children[1].get_child_call_stack_depth())
		assert_equals(1, children[2].get_call_stack_depth())
		assert_equals(1, children[2].get_child_call_stack_depth())

		children_2 = children[2].get_children()
		assert_equals(2, children_2[0].get_call_stack_depth())
		assert_equals(0, children_2[0].get_child_call_stack_depth())

		assert_equals(3, thread_data_1.get_max_stack_depth())

	def test_should_register_event(self):
		profile_data = ProfileData()
		profile_data.on_thread(0, "my thread")
		profile_data.on_event(0, 0, "my first event")

		thread = profile_data.get_thread(0)
		assert_equals(1, thread.get_num_events())
		event_data = thread.get_event(0)
		assert_equals("my first event", event_data.get_label())
		assert_equals(0, event_data.get_id())

	def test_should_register_events_on_multiple_threads(self):
		profile_data = ProfileData()
		profile_data.on_thread(0, "my thread")
		profile_data.on_thread(1, "my 2nd thread")
		profile_data.on_thread(2, "my 3rd thread")
		profile_data.on_event(0, 0, "my event 1")
		profile_data.on_event(1, 0, "my event 2")
		profile_data.on_event(2, 0, "my event 3")
		profile_data.on_event(2, 1, "my event 4")
		profile_data.on_event(1, 1, "my event 5")
		profile_data.on_event(2, 2, "my event 6")

		thread_0 = profile_data.get_thread(0)
		assert_equals(1, thread_0.get_num_events())
		assert_equals(0, thread_0.get_num_event_samples())
		
		thread_1 = profile_data.get_thread(1)
		assert_equals(2, thread_1.get_num_events())
		assert_equals(0, thread_1.get_num_event_samples())

		thread_2 = profile_data.get_thread(2)
		assert_equals(3, thread_2.get_num_events())
		assert_equals(0, thread_2.get_num_event_samples())
	
	def test_should_register_and_emit_event(self):
		profile_data = ProfileData()
		profile_data.on_thread(0, "my thread")
		profile_data.on_event(0, 0, "my first event")
		profile_data.on_event_emit(0, 0, 1234)
		
		thread = profile_data.get_thread(0)
		assert_equals(1, thread.get_num_events())
		assert_equals(1, thread.get_num_event_samples())

		event_sample_data = thread.get_event_sample(0)
		assert_equals(1234, event_sample_data.get_time())

	def test_should_register_and_emit_events_on_multiple_threads(self):
		profile_data = ProfileData()
		profile_data.on_thread(0, "my thread")
		profile_data.on_thread(1, "my 2nd thread")
		profile_data.on_thread(2, "my 3rd thread")
		profile_data.on_event(0, 0, "my event 1")
		profile_data.on_event(1, 0, "my event 2")
		profile_data.on_event(2, 0, "my event 3")		
		profile_data.on_event_emit(0,0,1)
		profile_data.on_event_emit(1,0,2)
		profile_data.on_event_emit(2,0,3)
		profile_data.on_event_emit(1,0,4)
		profile_data.on_event_emit(0,0,5)
		profile_data.on_event_emit(1,0,6)

		thread_0 = profile_data.get_thread(0)
		thread_1 = profile_data.get_thread(1)
		thread_2 = profile_data.get_thread(2)
		assert_equals(2, thread_0.get_num_event_samples())
		assert_equals(3, thread_1.get_num_event_samples())
		assert_equals(1, thread_2.get_num_event_samples())

	def test_should_report_num_counters(self):
		profile_data = ProfileData()
		assert_equals(0, profile_data.get_num_counters())

	def test_should_register_counter(self):
		profile_data = ProfileData()
		profile_data.on_counter(0, "my counter")
		assert_equals(1, profile_data.get_num_counters())

		counter_0 = profile_data.get_counter(0)
		assert_equals(0, counter_0.get_id())
		assert_equals("my counter", counter_0.get_label())
	
	def test_should_register_counter_and_handle_values(self):
		profile_data = ProfileData()
		profile_data.on_counter(0, "my counter")

		profile_data.on_counter_value(0, 1, 3)
		profile_data.on_counter_value(0, 200, 2)
		profile_data.on_counter_value(0, 3000, 1)

		counter_0 = profile_data.get_counter(0)
		samples = counter_0.get_samples()
		assert_equals(3, len(samples))

		assert_equals(1, samples[0].get_time())
		assert_equals(3, samples[0].get_value())

		assert_equals(200, samples[1].get_time())
		assert_equals(2, samples[1].get_value())

		assert_equals(3000, samples[2].get_time())
		assert_equals(1, samples[2].get_value())
	
	def test_should_register_multiple_counters(self):
		profile_data = ProfileData()
		profile_data.on_counter(0, "my counter")
		profile_data.on_counter(1, "my counter 2")
		assert_equals(2, profile_data.get_num_counters())
				
		counter_0 = profile_data.get_counter(0)
		assert_equals(0, counter_0.get_id())
		assert_equals("my counter", counter_0.get_label())

		counter_1 = profile_data.get_counter(1)
		assert_equals(1, counter_1.get_id())
		assert_equals("my counter 2", counter_1.get_label())

	def test_should_register_multiple_counters_and_handle_values(self):
		profile_data = ProfileData()
		profile_data.on_counter(0, "my counter")
		profile_data.on_counter(1, "my counter 2")
		assert_equals(2, profile_data.get_num_counters())

		profile_data.on_counter_value(0, 1, 3)
		profile_data.on_counter_value(1, 200, 2)
		profile_data.on_counter_value(0, 3000, 1)

		counter_0 = profile_data.get_counter(0)
		samples_0 = counter_0.get_samples()
		assert_equals(2, len(samples_0))

		assert_equals(1, samples_0[0].get_time())
		assert_equals(3, samples_0[0].get_value())

		assert_equals(3000, samples_0[1].get_time())
		assert_equals(1, samples_0[1].get_value())

		counter_1 = profile_data.get_counter(1)
		samples_1 = counter_1.get_samples()
		assert_equals(1, len(samples_1))		

		assert_equals(200, samples_1[0].get_time())
		assert_equals(2, samples_1[0].get_value())

	# @todo fail to consume out of order thread
	# @todo fail to consume function for unknown thread
	# @todo fail to consume out of order function for thread
	# @todo fail to consume out of order samples on a thread
