import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float32, String
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu
from nav_msgs.msg import Odometry
import random
import time
import math

class MavicNoCompensation(Node):
    def __init__(self):
        super().__init__('mavic_no_compensation')
        
        # Публикаторы
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.propeller_health_pub = self.create_publisher(Bool, '/propeller_health', 10)
        self.vibration_pub = self.create_publisher(Float32, '/vibration_level', 10)
        self.status_pub = self.create_publisher(String, '/drone_status', 10)
        
        # Подписки на датчики для мониторинга
        self.imu_sub = self.create_subscription(Imu, '/imu', self.imu_callback, 10)
        self.odom_sub = self.create_subscription(Odometry, '/odometry', self.odom_callback, 10)
        
        # Состояние винтов - изначально все исправны
        self.propeller_health = [True, True, True, True]
        self.propeller_efficiency = [1.0, 1.0, 1.0, 1.0]
        
        # Данные с датчиков для мониторинга
        self.current_imu = None
        self.current_odom = None
        self.vibration_level = 0.1
        
        # Таймеры управления и мониторинга
        self.create_timer(0.1, self.control_loop)  # 10 Hz управление
        self.create_timer(1.0, self.publish_health_data)  # 1 Hz мониторинг
        self.create_timer(3.0, self.simulate_damage)  # Проверка повреждений каждые 3 сек
        
        # Параметры симуляции повреждений
        self.flight_time = 0.0
        self.damage_probability = 0.4  # 40% вероятность повреждения каждые 3 секунды
        self.is_airborne = False
        self.takeoff_time = None
        self.crash_occurred = False
        
        self.get_logger().info('Mavic No Compensation controller started')

    def simulate_damage(self):
        """Симуляция случайных повреждений винтов без компенсации"""
        if not self.is_airborne or self.crash_occurred:
            return
            
        self.flight_time += 3.0
        
        # Вероятность повреждения увеличивается со временем полета
        current_probability = self.damage_probability + (self.flight_time / 30.0) * 0.3
        
        for i in range(4):
            # Проверяем каждый винт на повреждение
            if self.propeller_health[i] and random.random() < current_probability:
                # Помечаем винт как поврежденный
                self.propeller_health[i] = False
                self.propeller_efficiency[i] = random.uniform(0.0, 0.3)
                
                # Сообщение о повреждении в консоль
                self.get_logger().error(f'Propeller {i+1} DAMAGED! Efficiency: {self.propeller_efficiency[i]:.2f}')
                
                # Публикация статуса повреждения
                status_msg = String()
                status_msg.data = f"PROPELLER_{i+1}_DAMAGED"
                self.status_pub.publish(status_msg)
                
                # Логирование потери контроля
                damaged_count = sum(not health for health in self.propeller_health)
                if damaged_count >= 1:
                    self.get_logger().error('DRONE LOSING CONTROL!')

    def imu_callback(self, msg):
        """Обработка данных с инерциального измерительного блока"""
        self.current_imu = msg
        # Расчет уровня вибрации на основе линейного ускорения
        linear_accel = msg.linear_acceleration
        real_vibration = math.sqrt(linear_accel.x**2 + linear_accel.y**2 + linear_accel.z**2)
        self.vibration_level = min(real_vibration / 10.0, 1.0)

    def odom_callback(self, msg):
        """Обработка данных одометрии для определения состояния полета"""
        self.current_odom = msg
        current_altitude = msg.pose.pose.position.z
        # Определение взлета по достижению высоты более 0.3 метра
        if not self.is_airborne and current_altitude > 0.3:
            self.is_airborne = True
            self.takeoff_time = time.time()
            self.get_logger().info('Drone airborne - damage simulation active')

    def calculate_vibration_level(self):
        """Расчет уровня вибрации на основе состояния винтов"""
        base_vibration = 0.1
        damage_penalty = 0.0
        
        # Увеличение вибрации за каждый поврежденный винт
        for health in self.propeller_health:
            if not health:
                damage_penalty += 0.4
                
        vibration = base_vibration + damage_penalty
        return min(vibration, 2.0)

    def control_loop(self):
        """Цикл управления без компенсации повреждений"""
        cmd_msg = Twist()
        
        if self.crash_occurred:
            # Режим падения - дрон неконтролируемо снижается
            cmd_msg.linear.z = -1.0
            cmd_msg.angular.z = random.uniform(-5.0, 5.0)
            self.cmd_vel_pub.publish(cmd_msg)
            return
            
        if not self.is_airborne:
            # Режим взлета
            cmd_msg.linear.z = 0.7
            if self.takeoff_time is None:
                self.takeoff_time = time.time()
            elif time.time() - self.takeoff_time > 2.0:
                self.is_airborne = True
        else:
            # Режим полета
            damaged_count = sum(not health for health in self.propeller_health)
            
            if damaged_count == 0:
                # Нормальный полет без повреждений
                cmd_msg.linear.z = 0.4  # Базовая тяга для удержания высоты
                cmd_msg.linear.x = 0.1  # Небольшое движение вперед
                cmd_msg.angular.z = 0.1  # Медленное вращение
            else:
                # Режим с повреждениями - КОМПЕНСАЦИЯ ОТСУТСТВУЕТ
                # Расчет потери эффективности из-за повреждений
                efficiency_loss = sum(1.0 - eff for eff in self.propeller_efficiency)
                
                # Тяга уменьшается пропорционально повреждениям
                cmd_msg.linear.z = 0.4 - (efficiency_loss * 0.2)
                
                # Случайные возмущения из-за повреждений
                cmd_msg.linear.x = random.uniform(-1.0, 1.0) * damaged_count
                cmd_msg.linear.y = random.uniform(-1.0, 1.0) * damaged_count
                cmd_msg.angular.z = random.uniform(-2.0, 2.0) * damaged_count
                
                # Проверка на катастрофическое состояние
                if damaged_count >= 2 or cmd_msg.linear.z < 0:
                    self.crash_occurred = True
                    self.get_logger().error('CATASTROPHIC FAILURE: DRONE CRASH!')

        self.cmd_vel_pub.publish(cmd_msg)

    def publish_health_data(self):
        """Публикация данных о состоянии системы"""
        # Публикация общего состояния здоровья
        health_msg = Bool()
        health_msg.data = all(self.propeller_health)
        self.propeller_health_pub.publish(health_msg)
        
        # Публикация уровня вибрации
        vibration_msg = Float32()
        vibration_msg.data = self.calculate_vibration_level()
        self.vibration_pub.publish(vibration_msg)
        
        # Публикация текстового статуса
        status_msg = String()
        damaged_count = sum(not health for health in self.propeller_health)
        
        if self.crash_occurred:
            status_msg.data = "CRASHED - NO COMPENSATION"
        elif not self.is_airborne:
            status_msg.data = "TAKEOFF_IN_PROGRESS"
        else:
            status_msg.data = (f"FLYING - Time:{self.flight_time:.1f}s "
                             f"DAMAGED:{damaged_count}/4 "
                             f"Vibration:{vibration_msg.data:.2f}")
        
        self.status_pub.publish(status_msg)
        
        # Логирование состояния повреждений
        if damaged_count > 0:
            self.get_logger().warning(f'Damaged propellers: {damaged_count}, no compensation active')

def main():
    rclpy.init()
    node = MavicNoCompensation()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Controller shutdown requested')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
