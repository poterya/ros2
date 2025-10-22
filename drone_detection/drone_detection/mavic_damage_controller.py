import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float32, String
from geometry_msgs.msg import Twist
import random
import time

class MavicDamageController(Node):
    def __init__(self):
        super().__init__('mavic_damage_controller')
        
        # Публикатор для управления Mavic
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Публикаторы для мониторинга повреждений
        self.propeller_health_pub = self.create_publisher(Bool, '/propeller_health', 10)
        self.vibration_pub = self.create_publisher(Float32, '/vibration_level', 10)
        self.status_pub = self.create_publisher(String, '/drone_status', 10)
        
        # Состояние 4 винтов Mavic
        self.propeller_health = [True, True, True, True]
        self.propeller_efficiency = [1.0, 1.0, 1.0, 1.0]
        
        # Визуальные маркеры повреждений (можно публиковать для RViz)
        self.damage_markers_pub = self.create_publisher(String, '/damage_visualization', 10)
        
        # Таймеры
        self.create_timer(0.1, self.control_loop)  # 10 Hz управление
        self.create_timer(1.0, self.publish_health_data)  # 1 Hz мониторинг
        self.create_timer(10.0, self.simulate_damage)  # Каждые 10 сек проверка повреждений
        
        # Статистика
        self.flight_time = 0.0
        self.damage_probability = 0.05  # 5% вероятность повреждения каждые 10 сек
        self.is_airborne = False
        self.takeoff_time = None
        
        self.get_logger().info('Mavic Damage Controller started - waiting for drone...')

    def simulate_damage(self):
        """Симуляция случайных повреждений винтов Mavic"""
        if not self.is_airborne:
            return
            
        self.flight_time += 10.0
        
        # Увеличиваем вероятность повреждения со временем полета
        current_probability = self.damage_probability + (self.flight_time / 600.0) * 0.05
        
        for i in range(4):
            if self.propeller_health[i] and random.random() < current_probability:
                # Повреждаем винт
                self.propeller_health[i] = False
                self.propeller_efficiency[i] = random.uniform(0.2, 0.6)
                
                self.get_logger().error(f'🚨 CRITICAL: Propeller {i+1} DAMAGED! Efficiency: {self.propeller_efficiency[i]:.2f}')
                
                # Публикуем статус повреждения
                status_msg = String()
                status_msg.data = f"PROPELLER_{i+1}_DAMAGED_EFFICIENCY:{self.propeller_efficiency[i]:.2f}"
                self.status_pub.publish(status_msg)
                
                # Визуализация повреждения
                marker_msg = String()
                marker_msg.data = f"DAMAGE_{i+1}"
                self.damage_markers_pub.publish(marker_msg)

    def calculate_vibration_level(self):
        """Расчет уровня вибрации на основе состояния винтов"""
        base_vibration = 0.05
        damage_penalty = 0.0
        
        for i, health in enumerate(self.propeller_health):
            if not health:
                damage_penalty += 0.25 + (1.0 - self.propeller_efficiency[i]) * 0.3
                
        return min(base_vibration + damage_penalty, 1.0)

    def control_loop(self):
        """Система управления Mavic с компенсацией повреждений"""
        cmd_msg = Twist()
        
        if not self.is_airborne:
            # Автоматический взлет
            cmd_msg.linear.z = 0.5
            if self.takeoff_time is None:
                self.takeoff_time = time.time()
            elif time.time() - self.takeoff_time > 3.0:  # Через 3 секунды
                self.is_airborne = True
                self.get_logger().info('✓ Mavic airborne - damage simulation activated')
        else:
            # Полет с компенсацией повреждений
            base_thrust = 0.3  # Базовая тяга для удержания высоты
            base_yaw = 0.0
            
            # Компенсация для поврежденных винтов
            thrust_compensation, roll_compensation, pitch_compensation, yaw_compensation = self.calculate_compensation()
            
            cmd_msg.linear.z = base_thrust + thrust_compensation
            cmd_msg.angular.z = base_yaw + yaw_compensation
            
            # Добавляем небольшие движения для демонстрации
            if self.flight_time > 30.0:  # После 30 секунд полета
                cmd_msg.linear.x = 0.1
                cmd_msg.angular.z = 0.1
            
            # Компенсация крена и тангажа
            cmd_msg.angular.x = roll_compensation
            cmd_msg.angular.y = pitch_compensation
            
            # Если повреждены 3+ винта - аварийная посадка
            damaged_count = sum(not health for health in self.propeller_health)
            if damaged_count >= 3:
                cmd_msg.linear.z = -0.2  # Снижение
                self.get_logger().error('🚨 EMERGENCY LANDING: 3+ propellers damaged!')

        self.cmd_vel_pub.publish(cmd_msg)

    def calculate_compensation(self):
        """Расчет компенсации для поврежденных винтов Mavic"""
        thrust_comp = 0.0
        roll_comp = 0.0
        pitch_comp = 0.0
        yaw_comp = 0.0
        
        damaged_count = sum(not health for health in self.propeller_health)
        
        if damaged_count > 0:
            # Увеличиваем общую тягу для компенсации потери эффективности
            thrust_comp = damaged_count * 0.15
            
            # Компенсация в зависимости от того, какой винт поврежден
            # Mavic винты: 0-передний_левый, 1-передний_правый, 2-задний_левый, 3-задний_правый
            if not self.propeller_health[0]:  # Передний левый
                roll_comp = -0.1
                pitch_comp = -0.1
                yaw_comp = 0.2
            elif not self.propeller_health[1]:  # Передний правый
                roll_comp = 0.1
                pitch_comp = -0.1
                yaw_comp = -0.2
            elif not self.propeller_health[2]:  # Задний левый
                roll_comp = -0.1
                pitch_comp = 0.1
                yaw_comp = -0.1
            elif not self.propeller_health[3]:  # Задний правый
                roll_comp = 0.1
                pitch_comp = 0.1
                yaw_comp = 0.1
                
        return thrust_comp, roll_comp, pitch_comp, yaw_comp

    def publish_health_data(self):
        """Публикация данных о состоянии Mavic"""
        # Общее состояние здоровья
        health_msg = Bool()
        health_msg.data = all(self.propeller_health)
        self.propeller_health_pub.publish(health_msg)
        
        # Уровень вибрации
        vibration_msg = Float32()
        vibration_level = self.calculate_vibration_level()
        vibration_msg.data = vibration_level
        self.vibration_pub.publish(vibration_msg)
        
        # Статус полета
        status_msg = String()
        damaged_count = sum(not health for health in self.propeller_health)
        
        if not self.is_airborne:
            status_msg.data = f"TAKEOFF_IN_PROGRESS"
        else:
            efficiency_avg = sum(self.propeller_efficiency) / 4.0
            status_msg.data = (f"FLYING_TIME:{self.flight_time:.1f}s "
                             f"DAMAGED:{damaged_count}/4 "
                             f"EFFICIENCY:{efficiency_avg:.2f} "
                             f"VIBRATION:{vibration_level:.2f}")
        
        self.status_pub.publish(status_msg)
        
        # Логирование предупреждений
        if damaged_count > 0:
            self.get_logger().warning(f'⚠️ Damaged propellers: {damaged_count}, Vibration: {vibration_level:.2f}')
        elif self.is_airborne:
            self.get_logger().info(f'✓ Normal flight - Time: {self.flight_time:.1f}s')

def main():
    rclpy.init()
    node = MavicDamageController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Controller shutdown requested')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()