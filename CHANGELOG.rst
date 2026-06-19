^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Changelog for package mqtt_ros
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

0.0.1 (19-06-2026)
------------------
* Initial release.
* Added ``MqttToRosBridge`` node in ``mqtt_ros/mqtt_ros.py`` that bridges
  MQTT messages to ROS 2 ``ObjectRegion3DArray`` topics.
* Added ``MQTTMessageParser``, ``FlatCameraParser`` and ``ParserRegistry``
  for topic-specific MQTT payload parsing.
* Added ``main.py`` entry point and ``mqtt_ros.launch.py`` launch file.
* Added ``mqtt_publisher_example.py`` helper script to test the bridge.
* Added default parameter configuration in ``params/default_params.yaml``.
* Added linter tests (copyright, flake8, pep257, xmllint) and unit tests
  in ``test/``.
* Added GitHub Actions CI workflow.
* Contributors: Jose Galeas
