import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float32, String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu
from nav_msgs.msg import Odometry
import random
import time
import math

class MavicRealSensors(Node):
    def __init__(self):
        super().__init__('mavic_real_sensors')
        
        # Публикаторы
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.propeller_health_pub = self.create_publisher(Bool, '/propeller_health', 10)
        self.vibration_pub = self.create_publisher(Float32, '/vibration_level', 10)
        self.status_pub = self.create_publisher(String, '/drone_status', 10)
        
        # Подписки на датчики (только для мониторинга)
        self.imu_sub = self.create_subscription(Imu, '/imu', self.imu_callback, 10)
        self.odom_sub = self.create_subscription(Odometry, '/odometry', self.odom_callback, 10)
        
        # Состояние винтов (СИМУЛЯЦИЯ как раньше)
        self.propeller_health = [True, True, True, True]
        self.propeller_efficiency = [1.0, 1.0, 1.0, 1.0]
        
        # Данные с датчиков (только для информации)
        self.current_imu = None
        self.current_odom = None
        self.vibration_level = 0.1
        
        # Таймеры
        self.create_timer(0.1, self.control_loop)  # 10 Hz управление
        self.create_timer(1.0, self.publish_health_data)  # 1 Hz мониторинг
        self.create_timer(5.0, self.simulate_damage)  # Каждые 5 сек проверка повреждений
        
        # Статистика (как раньше)
        self.flight_time = 0.0
        self.damage_probability = 0.3  # 30% вероятность повреждения каждые 5 сек
        self.is_airborne = False
        self.takeoff_time = None
        self.crash_occurred = False
        
        self.get_logger().info('Mavic Real Sensors - OLD DAMAGE LOGIC ACTIVE')

    def simulate_damage(self):
        """СТАРАЯ ЛОГИКА - симуляция случайных повреждений винтов"""
        if not self.is_airborne or self.crash_occurred:
            return
            
        self.flight_time += 5.0
        
        # Увеличиваем вероятность повреждения со временем (как раньше)
        current_probability = self.damage_probability + (self.flight_time / 300.0) * 0.01
        
        for i in range(4):
            if self.propeller_health[i] and random.random() < current_probability:
                # Повреждаем винт (как раньше)
                self.propeller_health[i] = False
                self.propeller_efficiency[i] = random.uniform(0.1, 0.5)
                
                # ВЫВОДИМ В КОНСОЛЬ КАК РАНЬШЕ
                self.get_logger().error(f'🚨 Propeller {i+1} DAMAGED! Efficiency: {self.propeller_efficiency[i]:.2f}')
                
                # Публикуем статус
                status_msg = String()
                status_msg.data = f"PROPELLER_{i+1}_DAMAGED"
                self.status_pub.publish(status_msg)
                
                # Если сломаны 2+ винта - КРАХ (как раньше)
                damaged_count = sum(not health for health in self.propeller_health)
                if damaged_count >= 2:
                    self.crash_occurred = True
                    self.get_logger().error('💥 CATASTROPHIC FAILURE: DRONE CRASH!')

    def imu_callback(self, msg):
        """Получение данных с IMU (только для мониторинга)"""
        self.current_imu = msg
        
        # Расчет вибрации на основе реальных данных (дополнительная информация)
        linear_accel = msg.linear_acceleration
        real_vibration = math.sqrt(linear_accel.x**2 + linear_accel.y**2 + linear_accel.z**2)
        self.vibration_level = min(real_vibration / 10.0, 1.0)

    def odom_callback(self, msg):
        """Получение данных одометрии (только для определения взлета)"""
        self.current_odom = msg
        
        # Определяем взлет по высоте
        current_altitude = msg.pose.pose.position.z
        if not self.is_airborne and current_altitude > 0.3:
            self.is_airborne = True
            self.takeoff_time = time.time()
            self.get_logger().info('✈️ Drone airborne - OLD DAMAGE SYSTEM ACTIVE')

    def calculate_vibration_level(self):
        """Расчет уровня вибрации (как раньше + реальные данные)"""
        # Базовая вибрация из старой логики
        base_vibration = 0.1
        damage_penalty = 0.0
        
        for health in self.propeller_health:
            if not health:
                damage_penalty += 0.3
                
        old_vibration = base_vibration + damage_penalty
        
        # Комбинируем с реальными данными
        combined_vibration = (old_vibration + self.vibration_level) / 2.0
        return min(combined_vibration, 1.0)

    def control_loop(self):
        """Система управления с компенсацией повреждений (КАК РАНЬШЕ)"""
        cmd_msg = Twist()
        
        if self.crash_occurred:
            # АВАРИЙНЫЙ РЕЖИМ - дрон падает
            cmd_msg.linear.z = -1.0
            cmd_msg.linear.x = random.uniform(-2.0, 2.0)
            cmd_msg.linear.y = random.uniform(-2.0, 2.0)
            cmd_msg.angular.z = random.uniform(-3.0, 3.0)
            self.cmd_vel_pub.publish(cmd_msg)
            return
            
        if not self.is_airborne:
            # Взлет
            cmd_msg.linear.z = 0.8
            if self.takeoff_time is None:
                self.takeoff_time = time.time()
            elif time.time() - self.takeoff_time > 2.0:
                self.is_airborne = True
                self.get_logger().info('✈️ Drone airborne - OLD DAMAGE SYSTEM ACTIVE')
        else:
            # Полет с компенсацией повреждений (СТАРАЯ ЛОГИКА)
            base_thrust = 0.3
            base_yaw = 0.0
            
            # Компенсация для поврежденных винтов (как раньше)
            thrust_compensation, yaw_compensation = self.calculate_compensation()
            
            cmd_msg.linear.z = base_thrust + thrust_compensation
            cmd_msg.angular.z = base_yaw + yaw_compensation
            
            # Небольшие движения
            cmd_msg.linear.x = random.uniform(-0.1, 0.1)
            cmd_msg.linear.y = random.uniform(-0.1, 0.1)

        self.cmd_vel_pub.publish(cmd_msg)

    def calculate_compensation(self):
        """Расчет компенсации для поврежденных винтов (КАК РАНЬШЕ)"""
        thrust_comp = 0.0
        yaw_comp = 0.0
        
        damaged_count = sum(not health for health in self.propeller_health)
        
        if damaged_count > 0:
            # Увеличиваем общую тягу для компенсации
            thrust_comp = damaged_count * 0.5
            
            # Компенсация момента (как раньше)
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
        """Публикация данных о состоянии (как раньше)"""
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
        
        if self.crash_occurred:
            status_msg.data = "🚨 CRASHED - DRONE DESTROYED"
        elif not self.is_airborne:
            status_msg.data = "TAKEOFF_IN_PROGRESS"
        else:
            status_msg.data = (f"FLYING - Time:{self.flight_time:.1f}s "
                             f"DAMAGED:{damaged_count}/4 "
                             f"Vibration:{vibration_msg.data:.2f}")
        
        self.status_pub.publish(status_msg)
        
        # Логи как раньше
        if damaged_count > 0:
            self.get_logger().warning(f'Damaged propellers: {damaged_count}, Vibration: {vibration_msg.data:.2f}')

def main():
    rclpy.init()
    node = MavicRealSensors()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Controller shutdown')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
