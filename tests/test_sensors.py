import sys
import unittest
from unittest.mock import MagicMock, Mock
sys.modules['board'] = Mock()

import Sensors


class SensorTestcase(unittest.TestCase):
    def test_basic(self):
        i2c = Sensors.i2c()
        s = Sensors.Sensors(type="bmp280", i2c=i2c)


if __name__ == '__main__':
    unittest.main()
