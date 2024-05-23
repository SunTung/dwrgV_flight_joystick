import os
import time
import threading
import pygame
import tkinter as tk
import ctypes
import subprocess
import win32api
import win32con
import psutil

# 初始化Pygame
pygame.init()
pygame.joystick.init()

# 检查并连接摇杆
joystick_flight = None
for i in range(pygame.joystick.get_count()):
    joystick = pygame.joystick.Joystick(i)
    joystick.init()
    joystick_flight = joystick
    break  # 只使用第一个发现的摇杆

# 捕捉摇杆输入
def capture_joystick_input(joystick):
    if joystick is None:
        return "No joystick connected", None

    pygame.event.pump()  # 刷新摇杆事件

    # 获取摇杆的按钮状态
    buttons = sum(joystick.get_button(i) << i for i in range(joystick.get_numbuttons()))

    # 获取摇杆的轴状态
    x = joystick.get_axis(0) if abs(joystick.get_axis(0)) >= 0.01 else 0.0
    y = joystick.get_axis(1) if abs(joystick.get_axis(1)) >= 0.01 else 0.0

    return {"x": x, "y": y, "buttons": buttons}

# 将摇杆输入转化为按键事件
def send_key_event(buttons):
    if buttons & 0x01:
        win32api.keybd_event(win32con.VK_UP, 0, 0, 0)
    if buttons & 0x02:
        win32api.keybd_event(win32con.VK_DOWN, 0, 0, 0)
    if buttons & 0x04:
        win32api.keybd_event(win32con.VK_LEFT, 0, 0, 0)
    if buttons & 0x08:
        win32api.keybd_event(win32con.VK_RIGHT, 0, 0, 0)

# 捕捉和发送摇杆输入的线程
def capture_and_send():
    while True:
        if joystick_flight:
            flight_input = capture_joystick_input(joystick_flight)
            send_key_event(flight_input["buttons"])
        time.sleep(0.1)

# 启动游戏并返回其进程信息
def launch_game(executable_path):
    process = subprocess.Popen(executable_path)
    return process.pid

# 根据进程名称查找进程
def find_process_by_name(name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == name:
            return proc.pid
    raise Exception(f"Process with name {name} not found")

# 枚举并监控指定进程
def monitor_processes(target_pid):
    for _ in range(10):  # 重试 10 次
        try:
            parent_process = psutil.Process(target_pid)
            children = parent_process.children(recursive=True)
            processes = [parent_process] + children
            process_info = [(proc.pid, proc.name()) for proc in processes]
            return process_info
        except psutil.NoSuchProcess:
            time.sleep(1)  # 如果进程未找到，等待 1 秒后重试
    raise Exception(f"Process {target_pid} not found after multiple attempts")

# 捕捉进程的键盘和摇杆输入
def monitor_inputs(process_info):
    while True:
        for pid, name in process_info:
            print(f"Monitoring process: {name} (PID: {pid})")
            # 这里可以加入具体的键盘和摇杆事件捕捉逻辑
        time.sleep(5)

# 创建主窗口
root = tk.Tk()
root.geometry("600x400")
root.title("Joystick Input Display")

# 第1视窗: 显示捕捉到的摇杆动作
joystick_text = tk.Text(root, height=10, width=70)
joystick_text.pack()

# 第2视窗: 显示插入进程的动作
process_text = tk.Text(root, height=10, width=70)
process_text.pack()

# 停止标志
stop_flag = False

# 捕捉和显示摇杆输入的线程
def capture_and_display():
    global stop_flag
    while not stop_flag:
        if joystick_flight:
            flight_input = capture_joystick_input(joystick_flight)
            joystick_text.delete(1.0, tk.END)
            if flight_input:
                joystick_text.insert(tk.END, f"Flight Joystick Input:\n{flight_input}\n")
                send_key_event(flight_input["buttons"])
        time.sleep(0.1)

def start_capture():
    global stop_flag
    stop_flag = False
    capture_thread = threading.Thread(target=capture_and_display)
    capture_thread.start()

    # 等待捕捉输入后启动游戏
    time.sleep(1)  # 模拟捕捉到输入的等待时间

    # 游戏执行档路径
    game_executable_path = "C:\\IdentityV\\dwrg.exe"
    
    target_pid = launch_game(game_executable_path)
    process_text.insert(tk.END, f"Launched game with PID: {target_pid}\n")
    time.sleep(5)  # 等待游戏启动

    # 根据进程名称查找游戏进程
    game_name = "dwrg.exe"  # 假设这是目标游戏的进程名称
    game_pid = find_process_by_name(game_name)
    process_text.insert(tk.END, f"Found game process with PID: {game_pid}\n")

    # 启动监控进程的线程
    process_info = monitor_processes(game_pid)
    process_text.insert(tk.END, f"Monitoring processes: {process_info}\n")
    monitor_thread = threading.Thread(target=monitor_inputs, args=(process_info,))
    monitor_thread.start()

def stop_capture():
    global stop_flag
    stop_flag = True

start_button = tk.Button(root, text="Start", command=start_capture)
start_button.pack()

stop_button = tk.Button(root, text="Stop", command=stop_capture)
stop_button.pack()

if __name__ == "__main__":
    root.mainloop()
