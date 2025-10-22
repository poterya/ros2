import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float32, String
from geometry_msgs.msg import Twist
import random
import time

class DroneController(Node):
    def __init__(self):
        super().__init__('drone_controller')
        
        # Публикаторы
        self.propeller_health_pub = self.create_publisher(Bool, '/propeller_health', 10)
        self.vibration_pub = self.create_publisher(Float32, '/vibration_level', 10)
        self.status_pub = self.create_publisher(String, '/drone_status', 10)
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Состояние винтов
        self.propeller_health = [True, True, True, True]  # 4 винта
        self.propeller_efficiency = [1.0, 1.0, 1.0, 1.0]  # Эффективность каждого винта
        
        # Таймеры
        self.create_timer(0.1, self.control_loop)  # 10 Hz control
        self.create_timer(1.0, self.publish_health_data)  # 1 Hz health monitoring
        self.create_timer(5.0, self.simulate_damage)  # Каждые 5 сек проверка повреждений
        
        # Статистика
        self.flight_time = 0.0
        self.damage_probability = 0.01  # 1% вероятность повреждения каждые 5 сек
        
        self.get_logger().info('Drone controller started with damage simulation')

    def simulate_damage(self):
        """Симуляция случайных повреждений винтов"""
        self.flight_time += 5.0
        
        # Увеличиваем вероятность повреждения со временем
        current_probability = self.damage_probability + (self.flight_time / 300.0) * 0.01
        
        for i in range(4):
            if self.propeller_health[i] and random.random() < current_probability:
                # Повреждаем винт
                self.propeller_health[i] = False
                self.propeller_efficiency[i] = random.uniform(0.1, 0.5)  # Сила уменьшается
                
                self.get_logger().warning(f'🚨 Propeller {i+1} DAMAGED! Efficiency: {self.propeller_efficiency[i]:.2f}')
                
                # Публикуем статус
                status_msg = String()
                status_msg.data = f"PROPELLER_{i+1}_DAMAGED"
                self.status_pub.publish(status_msg)

    def calculate_vibration_level(self):
        """Расчет уровня вибрации на основе состояния винтов"""
        base_vibration = 0.1
        damage_penalty = 0.0
        
        for i, health in enumerate(self.propeller_health):
            if not health:
                damage_penalty += 0.3  # Каждый поврежденный винт добавляет вибрацию
                
        return base_vibration + damage_penalty

    def control_loop(self):
        """Система управления с компенсацией повреждений"""
        cmd_msg = Twist()
        
        # Базовая тяга
        base_thrust = 2.0
        base_yaw = 0.0
        
        # Компенсация для поврежденных винтов
        thrust_compensation, yaw_compensation = self.calculate_compensation()
        
        cmd_msg.linear.z = base_thrust + thrust_compensation
        cmd_msg.angular.z = base_yaw + yaw_compensation
        
        # Небольшие случайные движения для реалистичности
        cmd_msg.linear.x = random.uniform(-0.1, 0.1)
        cmd_msg.linear.y = random.uniform(-0.1, 0.1)
        
        self.cmd_vel_pub.publish(cmd_msg)

    def calculate_compensation(self):
        """Расчет компенсации для поврежденных винтов"""
        thrust_comp = 0.0
        yaw_comp = 0.0
        
        damaged_count = sum(not health for health in self.propeller_health)
        
        if damaged_count > 0:
            # Увеличиваем общую тягу для компенсации
            thrust_comp = damaged_count * 0.5
            
            # Компенсация момента в зависимости от того, какой винт поврежден
            if not self.propeller_health[0]:  # Передний левый
                yaw_comp = 0.2
            elif not self.propeller_health[1]:  # Передний правый
                yaw_comp = -0.2
            elif not self.propeller_health[2]:  # Задний левый
                yaw_comp = -0.1
            elif not self.propeller_health[3]:  # Задний правый
                yaw_comp = 0.1
                
        return thrust_comp, yaw_comp

    def publish_health_data(self):
        """Публикация данных о состоянии"""
        # Общее состояние здоровья
        health_msg = Bool()
        health_msg.data = all(self.propeller_health)
        self.propeller_health_pub.publish(health_msg)
        
        # Уровень вибрации
        vibration_msg = Float32()
        vibration_msg.data = self.calculate_vibration_level()
        self.vibration_pub.publish(vibration_msg)
        
        # Статус
        status_msg = String()
        damaged_count = sum(not health for health in self.propeller_health)
        status_msg.data = f"FLIGHT_TIME:{self.flight_time:.1f}s DAMAGED:{damaged_count}/4 VIBRATION:{vibration_msg.data:.2f}"
        self.status_pub.publish(status_msg)
        
        if damaged_count > 0:
            self.get_logger().warning(f'Damaged propellers: {damaged_count}, Vibration: {vibration_msg.data:.2f}')

def main():
    rclpy.init()
    node = DroneController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
