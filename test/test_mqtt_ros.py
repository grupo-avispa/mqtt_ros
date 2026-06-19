# Copyright (c) 2026 Jose Galeas
# Copyright (c) 2026 Grupo Avispa, DTE, Universidad de Málaga
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for the MQTT message parsers of the mqtt_ros package."""

import unittest

from mqtt_ros.mqtt_ros import FlatCameraParser, ParserRegistry

from object_with_region.msg import ObjectRegion3DArray


class _StubLogger:
    """Minimal logger stub that swallows all log calls."""

    def info(self, *args, **kwargs) -> None:
        """Ignore info messages."""

    def warn(self, *args, **kwargs) -> None:
        """Ignore warning messages."""

    def warning(self, *args, **kwargs) -> None:
        """Ignore warning messages."""

    def error(self, *args, **kwargs) -> None:
        """Ignore error messages."""

    def debug(self, *args, **kwargs) -> None:
        """Ignore debug messages."""


class _StubNode:
    """Minimal node stub exposing a logger for the parsers."""

    def get_logger(self) -> _StubLogger:
        """Return the stub logger."""
        return _StubLogger()


class TestParserRegistry(unittest.TestCase):
    """Tests for the ParserRegistry default behavior."""

    def setUp(self) -> None:
        """Create a fresh registry for each test."""
        self.registry = ParserRegistry()

    def test_default_parser_registered(self) -> None:
        """The flat_camera parser is registered by default."""
        parser = self.registry.get_parser('smarthome/flat_camera/')
        self.assertIsInstance(parser, FlatCameraParser)

    def test_unknown_topic_returns_none(self) -> None:
        """An unknown topic has no registered parser."""
        self.assertIsNone(self.registry.get_parser('unknown/topic'))


class TestFlatCameraParser(unittest.TestCase):
    """Tests for the FlatCameraParser parsing logic."""

    def setUp(self) -> None:
        """Create the parser and the stub node for each test."""
        self.parser = FlatCameraParser()
        self.node = _StubNode()

    def test_parse_valid_message(self) -> None:
        """A complete payload is parsed into a single object detection."""
        data = {
            'region': 'kitchen',
            'clase': 'table',
            'confianza': 0.75,
            'centro_bb': {'x': 1.5, 'y': 2.3, 'z': 0.0},
            'timestamp': {'segundos': 12, 'nanosegundos': 34},
            'camera_id': '0',
        }
        msg = self.parser.parse(data, self.node)

        self.assertIsInstance(msg, ObjectRegion3DArray)
        self.assertEqual(len(msg.objects), 1)
        self.assertEqual(msg.header.frame_id, '0')
        self.assertEqual(msg.header.stamp.sec, 12)
        self.assertEqual(msg.header.stamp.nanosec, 34)

        obj = msg.objects[0]
        self.assertEqual(obj.region, 'kitchen')
        hypothesis = obj.object.results[0].hypothesis
        self.assertEqual(hypothesis.class_id, 'table')
        self.assertAlmostEqual(hypothesis.score, 0.75)

    def test_parse_missing_class_returns_empty(self) -> None:
        """A payload without 'clase' yields a message with no objects."""
        msg = self.parser.parse({'region': 'kitchen'}, self.node)
        self.assertIsInstance(msg, ObjectRegion3DArray)
        self.assertEqual(len(msg.objects), 0)


if __name__ == '__main__':
    unittest.main()
