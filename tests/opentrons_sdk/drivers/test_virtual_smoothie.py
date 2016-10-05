import unittest

import json

from opentrons_sdk.drivers.virtual_smoothie import VirtualSmoothie


class VirtualSmoothieTestCase(unittest.TestCase):

    def setUp(self):
        settings = {
            'ot_version': 'one_pro',
            'alpha_steps_per_mm': 80.0
        }
        self.s = VirtualSmoothie('v1.0.5', settings)

    def test_version(self):
        self.s.write('version')
        res = self.s.readline()
        self.assertEqual(res, '{"version":v1.0.5}')

    def test_config_get(self):
        self.s.write('config-get sd ot_version')
        res = self.s.readline()
        self.assertEqual(res, 'sd: ot_version is set to one_pro')

        self.s.write('config-get sd go_crazy')
        res = self.s.readline()
        self.assertEqual(res, 'sd: go_crazy is not in config')

    def test_config_set(self):
        self.s.write('config-set sd ot_version hood')
        res = self.s.readline()
        self.assertEqual(res, 'sd: ot_version has been set to hood')

        self.s.write('config-get sd ot_version')
        res = self.s.readline()
        self.assertEqual(res, 'sd: ot_version is set to hood')

    def test_parse_command(self):
        expected_result = {
            'command': 'G0',
            'arguments': {
                'X': 1.0,
                'Y': 2.5,
                'Z': 3.0,
                'a': 4.0,
                'b': 5.0,
                'F': -66.0
            }
        }

        res = self.s.parse_command('G0X1Y2.5Z3a4b5F-66')
        self.assertDictEqual(res, expected_result)

        res = self.s.parse_command('G0 X1Y2.5Z3a4b5F-66')
        self.assertDictEqual(res, expected_result)

        res = self.s.parse_command('G0X1 Y2.5Z3a4b5F-66')
        self.assertDictEqual(res, expected_result)

    def test_set_position(self):
        self.s.write('G92X1Y2.5Z3')
        response = self.s.readline()
        self.assertEquals(response, 'ok')

        self.s.write('M114')
        response = self.s.readline()
        self.assertEquals(response[:3], 'ok ')

        response = json.loads(response[3:])
        expected_result = {'M114': {
            'X': 1.0,
            'Y': 2.5,
            'Z': 3.0,
            'A': 0.0,
            'B': 0.0,
            'x': 1.0,
            'y': 2.5,
            'z': 3.0,
            'a': 0.0,
            'b': 0.0
        }}
        self.assertDictEqual(response, expected_result)

    def test_endstops(self):
        self.s.write('M119')
        response = self.s.readline()
        self.assertEquals(
            response,
            r'{"M119":{"min_x":0,"min_y":0,"min_z":0,"min_a":0,"min_b":0}}')
        response = self.s.readline()
        self.assertEquals(response, 'ok')

    def test_calm_down(self):
        self.s.write('M999')
        response = self.s.readline()
        self.assertEquals(response, 'ok')

    def test_dwell(self):
        self.s.write('G4 S1 P200')
        response = self.s.readline()
        self.assertEquals(response, 'ok')

    def test_home(self):
        self.s.write('G0X1Y2.5Z3')
        response = self.s.readline()
        self.assertEquals(response, 'ok')

        self.s.write('G28X')
        response = self.s.readline()
        self.assertEquals(response, 'ok')

        expected_result = {'M114': {
            'X': 0.0,
            'Y': 2.5,
            'Z': 3.0,
            'A': 0.0,
            'B': 0.0,
            'x': 0.0,
            'y': 2.5,
            'z': 3.0,
            'a': 0.0,
            'b': 0.0
        }}

        self.s.write('M114')
        response = self.s.readline()
        self.assertEquals(response[:3], 'ok ')

        response = json.loads(response[3:])
        self.assertDictEqual(response, expected_result)
        self.s.write('G28')
        response = self.s.readline()
        self.assertEquals(response, 'ok')

        expected_result = {'M114': {
            'X': 0.0,
            'Y': 0.0,
            'Z': 0.0,
            'A': 0.0,
            'B': 0.0,
            'x': 0.0,
            'y': 0.0,
            'z': 0.0,
            'a': 0.0,
            'b': 0.0
        }}

        self.s.write('M114')
        response = self.s.readline()
        self.assertEquals(response[:3], 'ok ')

        response = json.loads(response[3:])
        self.assertDictEqual(response, expected_result)

    def test_move(self):

        self.s.write('G90')
        response = self.s.readline()
        self.assertEquals(response, 'ok')

        self.s.write('G0X1Y2.5Z3')
        response = self.s.readline()
        self.assertEquals(response, 'ok')

        self.s.write('M114')
        response = self.s.readline()
        self.assertEquals(response[:3], 'ok ')

        response = json.loads(response[3:])
        expected_result = {'M114': {
            'X': 1.0,
            'Y': 2.5,
            'Z': 3.0,
            'A': 0.0,
            'B': 0.0,
            'x': 1.0,
            'y': 2.5,
            'z': 3.0,
            'a': 0.0,
            'b': 0.0
        }}
        self.assertDictEqual(response, expected_result)

        self.s.write('G91')
        response = self.s.readline()
        self.assertEquals(response, 'ok')

        self.s.write('G0X1Y1Z-1')
        response = self.s.readline()
        self.assertEquals(response, 'ok')

        self.s.write('M114')
        response = self.s.readline()
        self.assertEquals(response[:3], 'ok ')

        response = json.loads(response[3:])
        expected_result = {'M114': {
            'X': 2.0,
            'Y': 3.5,
            'Z': 2.0,
            'A': 0.0,
            'B': 0.0,
            'x': 2.0,
            'y': 3.5,
            'z': 2.0,
            'a': 0.0,
            'b': 0.0
        }}
        self.assertDictEqual(response, expected_result)



