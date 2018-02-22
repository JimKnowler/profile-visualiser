import nose
from pymock import *

import sys
sys.path.insert(0,'..')

from profileparser import ProfileParser


class TestParser(PyMockTestCase):

	def test_should_construct_with_consumer(self):
		mock_consumer = self.mock()
		parser = ProfileParser(mock_consumer)

	def test_should_parse_thread_msg(self):
		mock_consumer = self.mock()
		parser = ProfileParser(mock_consumer)

		self.expectAndReturn(mock_consumer.on_thread(332, "My Thread Name"), None)
		self.replay()
		parser.parse("T 332 My Thread Name")
		self.verify()

	def test_should_parse_thread_msg_2(self):
		mock_consumer = self.mock()
		parser = ProfileParser(mock_consumer)

		self.expectAndReturn(mock_consumer.on_thread(102, "Another Thread"), None)
		self.replay()
		parser.parse("T 102 Another Thread")
		self.verify()

	def test_should_parse_function_msg(self):
		mock_consumer = self.mock()
		parser = ProfileParser(mock_consumer)

		self.expectAndReturn(mock_consumer.on_function(113, 223, "My function name"), None)
		self.replay()
		parser.parse("F 113 223 My function name")
		self.verify()

	def test_should_parse_function_msg_2(self):
		mock_consumer = self.mock()
		parser = ProfileParser(mock_consumer)

		self.expectAndReturn(mock_consumer.on_function(43, 44, "Another function"), None)
		self.replay()
		parser.parse("F 43 44 Another function")
		self.verify()

	def test_should_parse_sample_start_msg(self):
		mock_consumer = self.mock()
		parser = ProfileParser(mock_consumer)

		self.expectAndReturn(mock_consumer.on_sample_start(0, 113, 333), None)
		self.replay()
		parser.parse("S 0 113 333")
		self.verify()

	def test_should_parse_sample_start_msg_2(self):
		mock_consumer = self.mock()
		parser = ProfileParser(mock_consumer)

		self.expectAndReturn(mock_consumer.on_sample_start(2, 1, 444), None)
		self.replay()
		parser.parse("S 2 1 444")
		self.verify()

	def test_should_parse_sample_finish_msg(self):
		mock_consumer = self.mock()
		parser = ProfileParser(mock_consumer)

		self.expectAndReturn(mock_consumer.on_sample_finish(4, 113, 333), None)
		self.replay()
		parser.parse("E 4 113 333")
		self.verify()

	def test_should_parse_sample_finish_msg_2(self):
		mock_consumer = self.mock()
		parser = ProfileParser(mock_consumer)

		self.expectAndReturn(mock_consumer.on_sample_finish(7, 1, 444), None)
		self.replay()
		parser.parse("E 7 1 444")
		self.verify()

	def test_should_ignore_comments(self):
		mock_consumer = self.mock()
		parser = ProfileParser(mock_consumer)
		self.replay()

		parser.parse("#a_comment_without_spaces")
		parser.parse("# another comment with spaces")

		self.verify()
	
	def test_should_parse_event_msg(self):
		mock_consumer = self.mock()
		parser = ProfileParser(mock_consumer)

		self.expectAndReturn(mock_consumer.on_event(113, 223, "My event name"), None)
		self.replay()
		parser.parse("V 113 223 My event name")
		self.verify()

	def test_should_parse_event_msg_2(self):
		mock_consumer = self.mock()
		parser = ProfileParser(mock_consumer)

		self.expectAndReturn(mock_consumer.on_event(43, 44, "Another event"), None)
		self.replay()
		parser.parse("V 43 44 Another event")
		self.verify()
	
	def test_should_parse_emit_event_msg(self):
		mock_consumer = self.mock()
		parser = ProfileParser(mock_consumer)

		self.expectAndReturn(mock_consumer.on_event_emit(0, 113, 333), None)
		self.replay()
		parser.parse("Y 0 113 333")
		self.verify()

	def test_should_parse_emit_event_msg_2(self):
		mock_consumer = self.mock()
		parser = ProfileParser(mock_consumer)

		self.expectAndReturn(mock_consumer.on_event_emit(2, 1, 444), None)
		self.replay()
		parser.parse("Y 2 1 444")
		self.verify()