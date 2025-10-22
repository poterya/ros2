import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float32, String
from geometry_msgs.msg import Twist
import random
import time

class MavicFastDamage(Node):
    def __init__(self):
        super().__init__('mavic_fast_damage')
        
        # Публикатор для управления Mavic
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # Публикаторы для мониторинга повреждений
        self.propeller_health_pub = self.create_publisher(Bool, '/propeller_health', 10)
        self.vibration_pub = self.create_publisher(Float32, '/vibration_level', 10)
        self.status_pub = self.create_publisher(String, '/drone_status', 10)
        
        # Состояние 4 винтов Mavic
        self.propeller_health = [True, True, True, True]
        self.propeller_efficiency = [1.0, 1.0, 1.0, 1.0]
        
        # Таймеры
        self.create_timer(0.1, self.control_loop)  # 10 Hz управление
        self.create_timer(1.0, self.publish_health_data)  # 1 Hz мониторинг
        self.create_timer(3.0, self.simulate_damage)  # Каждые 3 сек проверка повреждений
        
        # Статистика - ВЫСОКАЯ вероятность повреждения
        self.flight_time = 0.0
        self.damage_probability = 0.4  # 40% вероятность повреждения каждые 3 сек!
        self.is_airborne = False
        self.takeoff_time = None
        self.crash_occurred = False
        
        self.get_logger().info('🚀 Mavic Fast Damage Controller - Quick failure mode activated!')

    def simulate_damage(self):
        """Быстрая симуляция повреждений винтов БЕЗ КОМПЕНСАЦИИ"""
        if not self.is_airborne or self.crash_occurred:
            return
            
        self.flight_time += 3.0
        
        # ОЧЕНЬ ВЫСОКАЯ вероятность повреждения
        current_probability = self.damage_probability + (self.flight_time / 30.0) * 0.3
        
        for i in range(4):
            if self.propeller_health[i] and random.random() < current_probability:
                # Повреждаем винт СИЛЬНО
                self.propeller_health[i] = False
                self.propeller_efficiency[i] = random.uniform(0.0, 0.2)  # Почти нулевая эффективность
                
                self.get_logger().error(f'💥 CATASTROPHIC FAILURE: Propeller {i+1} DESTROYED!')
                
                # Публикуем статус повреждения
                status_msg = String()
                status_msg.data = f"CRITICAL_FAILURE_PROPELLER_{i+1}"
                self.status_pub.publish(status_msg)
                
                # Если сломаны 2+ винта - КРАХ
                damaged_count = sum(not health for health in self.propeller_health)
                if damaged_count >= 2:
                    self.crash_occurred = True
                    self.get_logger().error('💀 CATASTROPHIC FAILURE: DRONE CRASH IMMINENT!')
                    crash_msg = String()
                    crash_msg.data = "DRONE_CRASH"
                    self.status_pub.publish(crash_msg)

    def calculate_vibration_level(self):
        """Расчет экстремального уровня вибрации"""
        base_vibration = 0.1
        damage_penalty = 0.0
        
        for i, health in enumerate(self.propeller_health):
            if not health:
                damage_penalty += 0.5  # Высокая вибрация за каждый поврежденный винт
                
        return min(base_vibration + damage_penalty, 2.0)  # Максимальная вибрация

    def control_loop(self):
        """Управление БЕЗ КОМПЕНСАЦИИ - дрон должен упасть при повреждениях"""
        cmd_msg = Twist()
        
        if self.crash_occurred:
            # АВАРИЙНЫЙ РЕЖИМ - дрон падает
            cmd_msg.linear.z = -1.0  # Быстрое снижение
            cmd_msg.linear.x = random.uniform(-2.0, 2.0)  # Случайные рывки
            cmd_msg.linear.y = random.uniform(-2.0, 2.0)
            cmd_msg.angular.z = random.uniform(-3.0, 3.0)  # Бесконтрольное вращение
            self.cmd_vel_pub.publish(cmd_msg)
            return
            
        if not self.is_airborne:
            # Быстрый взлет
            cmd_msg.linear.z = 0.8
            if self.takeoff_time is None:
                self.takeoff_time = time.time()
            elif time.time() - self.takeoff_time > 2.0:  # Быстрый взлет за 2 секунды
                self.is_airborne = True
                self.get_logger().info('⚡ Mavic airborne - RAPID FAILURE MODE ACTIVATED!')
        else:
            # Полет БЕЗ КОМПЕНСАЦИИ повреждений
            damaged_count = sum(not health for health in self.propeller_health)
            
            if damaged_count == 0:
                # Нормальный полет
                cmd_msg.linear.z = 0.3  # Удержание высоты
                # Небольшие движения
                cmd_msg.linear.x = 0.1
                cmd_msg.angular.z = 0.1
            elif damaged_count == 1:
                # Один поврежденный винт - начинаются проблемы
                cmd_msg.linear.z = 0.2  # Тяга уменьшается
                # Появляется крен
                cmd_msg.angular.x = random.uniform(-0.5, 0.5)
                cmd_msg.angular.y = random.uniform(-0.5, 0.5)
                cmd_msg.angular.z = random.uniform(-1.0, 1.0)
                self.get_logger().warning('⚠️ Stability compromised - one propeller failed!')
            else:
                # Два и более поврежденных винта - КАТАСТРОФА
                cmd_msg.linear.z = -0.3  # Начинаем падать
                # Полная потеря контроля
                cmd_msg.linear.x = random.uniform(-1.0, 1.0)
                cmd_msg.linear.y = random.uniform(-1.0, 1.0)
                cmd_msg.angular.z = random.uniform(-2.0, 2.0)
                cmd_msg.angular.x = random.uniform(-1.0, 1.0)
                cmd_msg.angular.y = random.uniform(-1.0, 1.0)
                
                if not self.crash_occurred and damaged_count >= 2:
                    self.crash_occurred = True
                    self.get_logger().error('💀 CATASTROPHIC FAILURE: DRONE CRASH!')

        self.cmd_vel_pub.publish(cmd_msg)

    def publish_health_data(self):
        """Публикация данных о состоянии"""
        health_msg = Bool()
        health_msg.data = all(self.propeller_health)
        self.propeller_health_pub.publish(health_msg)
        
        vibration_msg = Float32()
        vibration_level = self.calculate_vibration_level()
        vibration_msg.data = vibration_level
        self.vibration_pub.publish(vibration_msg)
        
        status_msg = String()
        damaged_count = sum(not health for health in self.propeller_health)
        
        if self.crash_occurred:
            status_msg.data = "🚨 CRASHED - DRONE DESTROYED"
        elif not self.is_airborne:
            status_msg.data = "FAST_TAKEOFF"
        else:
            status_msg.data = (f"FLYING_DAMAGE_MODE - "
                             f"Time:{self.flight_time:.1f}s "
                             f"Damaged:{damaged_count}/4 "
                             f"Vibration:{vibration_level:.2f}")
        
        self.status_pub.publish(status_msg)
        
        # Яркие логи для быстрого отслеживания состояния
        if damaged_count == 1:
            self.get_logger().warning(f'🔸 First failure! Damaged: {damaged_count}/4')
        elif damaged_count >= 2:
            self.get_logger().error(f'🔻 CRITICAL: {damaged_count} propellers failed!')

def main():
    rclpy.init()
    node = MavicFastDamage()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('Controller shutdown')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()