#!/usr/bin/env python3
"""
Nodo de ROS que escucha mensajes MQTT del topic /flat_camera/*
y los republica como mensajes ROS después de parsear el formato.
"""

import rospy
import paho.mqtt.client as mqtt
import json
from std_msgs.msg import String
from object_with_region.msg import ObjectRegion3DArray 


class MqttToRosBridge:
    def __init__(self):
        # Inicializar nodo de ROS
        rospy.init_node('mqtt_to_ros_bridge', anonymous=True)
        
        # Declare and get parameters
        self._declare_and_get_parameters()
        
        # Publisher de ROS
        self.ros_pub = rospy.Publisher(self.ros_topic, self.msgs_type, queue_size=10)
                
        # Cliente MQTT
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        
        rospy.loginfo(f"Conectando al broker MQTT en {self.mqtt_broker}:{self.mqtt_port}")
        
    def _declare_and_get_parameters(self) -> None:
        """Declare and retrieve all ROS2 parameters."""
        # Model name
        self.declare_parameter('mqtt_broker', 'localhost')
        self.mqtt_broker = self.get_parameter(
            'mqtt_broker').get_parameter_value().string_value
        self.get_logger().info(
            f'Parameter mqtt_broker: [{self.mqtt_broker}]')
        
        self.declare_parameter('mqtt_port', 1883)
        self.mqtt_port = self.get_parameter(
            'mqtt_port').get_parameter_value().integer_value
        self.get_logger().info(
            f'Parameter mqtt_port: [{self.mqtt_port}]')
        
        self.declare_parameter('client_id', 'mqtt_ros_client')
        self.client_id = self.get_parameter(
            'client_id').get_parameter_value().string_value
        self.get_logger().info(
            f'Parameter client_id: [{self.client_id}]')
        
        self.declare_parameter('mqtt_topic', 'smarthome/flat_camera/')
        self.mqtt_topic = self.get_parameter(
            'mqtt_topic').get_parameter_value().string_value
        self.get_logger().info(
            f'Parameter mqtt_topic: [{self.mqtt_topic}]')
        
        self.declare_parameter('ros_topic', '/camera/image_raw')
        self.ros_topic = self.get_parameter(
            'ros_topic').get_parameter_value().string_value
        self.get_logger().info(
            f'Parameter ros_topic: [{self.ros_topic}]')

    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback cuando se conecta al broker MQTT"""
        if rc == 0:
            rospy.loginfo("Conectado exitosamente al broker MQTT")
            # Suscribirse al topic
            client.subscribe(self.mqtt_topic)
            rospy.loginfo(f"Suscrito al topic: {self.mqtt_topic}")
        else:
            rospy.logerr(f"Error de conexión MQTT. Código: {rc}")
    
    def on_mqtt_message(self, client, userdata, msg):
        """Callback cuando se recibe un mensaje MQTT"""
        try:
            # Decodificar el payload MQTT
            mqtt_payload = msg.payload.decode('utf-8')
            mqtt_topic = msg.topic
            
            rospy.loginfo(f"Mensaje recibido de {mqtt_topic}")
            
            # Parse del mensaje - intenta parsearlo como JSON
            try:
                data = json.loads(mqtt_payload)
                # Crear mensaje parseado con metadata
                parsed_message = {
                    "source_topic": mqtt_topic,
                    "timestamp": rospy.get_time(),
                    "data": data
                }
                ros_message = json.dumps(parsed_message)
            except json.JSONDecodeError:
                # Si no es JSON, enviar como texto plano con metadata
                parsed_message = {
                    "source_topic": mqtt_topic,
                    "timestamp": rospy.get_time(),
                    "data": mqtt_payload
                }
                ros_message = json.dumps(parsed_message)
            
            # Publicar en ROS
            self.ros_pub.publish(ros_message)
            rospy.logdebug(f"Mensaje publicado en ROS: {ros_message[:100]}...")
            
        except Exception as e:
            rospy.logerr(f"Error procesando mensaje MQTT: {str(e)}")
    
    def start(self):
        """Iniciar el bridge"""
        try:
            # Conectar al broker MQTT
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            
            # Iniciar loop MQTT en thread separado
            self.mqtt_client.loop_start()
            
            rospy.loginfo("Bridge MQTT->ROS iniciado")
            
            # Mantener el nodo activo
            rospy.spin()
            
        except Exception as e:
            rospy.logerr(f"Error iniciando el bridge: {str(e)}")
        finally:
            # Limpieza al finalizar
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            rospy.loginfo("Bridge MQTT->ROS finalizado")


if __name__ == '__main__':
    try:
        bridge = MqttToRosBridge()
        bridge.start()
    except rospy.ROSInterruptException:
        pass