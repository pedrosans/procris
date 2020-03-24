import pwm.applications as applications
import unittest

applications.load()


class ApplicationsIntegrationTestCase(unittest.TestCase):

	def test_list_application_names(self):
		for app_name in applications.NAME_MAP.keys():
			print('{:30}  ::: {}'.format(app_name, applications.LOCATION_MAP[app_name]))
		self.assertIn('Calculator', applications.NAME_MAP.keys())


if __name__ == '__main__':
	unittest.main()

