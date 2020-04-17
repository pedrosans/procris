import unittest

import pocoy.state as state


class StateTestCase(unittest.TestCase):

	def setUp(self):
		self.origin = {'name': 'foo', 'surname': 'foobar', 'children': [{'name': 'bob'}], 'car': {'name': 'foo'}}
		self.destination = {'name': 'bar', 'car': {'name': 'bar'}}

	def test_override(self):
		state.deep_copy(self.destination, self.origin, override=True)
		self.assertEqual('foo', self.destination['name'])

	def test_override_deep_values(self):
		state.deep_copy(self.destination, self.origin, override=True)
		self.assertEqual('foo', self.destination['car']['name'])

	def test_dont_override(self):
		state.deep_copy(self.destination, self.origin, override=False)
		self.assertEqual('bar', self.destination['name'])

	def test_copy_default(self):
		state.deep_copy(self.destination, self.origin, override=False)
		self.assertEqual('foobar', self.destination['surname'])

	def test_copy_default_list(self):
		state.deep_copy(self.destination, self.origin, override=False)
		self.assertEqual('bob', self.destination['children'][0]['name'])

	def test_dont_override_deep_values(self):
		state.deep_copy(self.destination, self.origin, override=False)
		self.assertEqual('bar', self.destination['car']['name'])

if __name__ == '__main__':
	unittest.main()
