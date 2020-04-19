import unittest

import pocoy.state as state


class StateTestCase(unittest.TestCase):

	def setUp(self):
		self.origin = {
			'name': 'foo',
			'surname': 'foobar',
			'children': [{'name': 'bob'}],
			'car': {'name': 'foo'}
		}
		self.destination = {
			'name': 'bar',
			'children': [{'name': 'jon'}],
			'car': {'name': 'bar'}
		}

	def test_override(self):
		state.deep_copy(self.destination, self.origin, override=True)
		self.assertEqual('foo', self.destination['name'])

	def test_override_deep_values(self):
		state.deep_copy(self.destination, self.origin, override=True)
		self.assertEqual('foo', self.destination['car']['name'])

	def test_override_property_inside_list(self):
		state.deep_copy(self.destination, self.origin, override=True)
		self.assertEqual('bob', self.destination['children'][0]['name'])

	def test_dont_override(self):
		state.deep_copy(self.destination, self.origin, override=False)
		self.assertEqual('bar', self.destination['name'])

	def test_copy_default(self):
		state.deep_copy(self.destination, self.origin, override=False)
		self.assertEqual('foobar', self.destination['surname'])

	def test_dont_override_deep_values(self):
		state.deep_copy(self.destination, self.origin, override=False)
		self.assertEqual('bar', self.destination['car']['name'])

	def test_override_module_values(self):
		import pocoy as pocoy
		pocoy.inner_gap = 5
		cache = {'inner_gap': 0}
		state.read_user_config(cache, pocoy)
		self.assertEqual(5, cache['inner_gap'])


if __name__ == '__main__':
	unittest.main()
