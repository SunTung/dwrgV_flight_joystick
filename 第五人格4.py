import os
import time
import threading
import pygame
import tkinter as tk
import ctypes
import subprocess
import psutil
import win32api
import win32con
import sys

# 初始化Pygame
def initialize():
    pygame.init()
    pygame.joystick.init()
    connect_joystick()

# 检查并连接摇杆
joystick_flight = None
def connect_joystick():
    global joystick_flight
    joystick_flight = None
    for i in range(pygame.joystick.get_count()):
        joystick = pygame.joystick.Joystick(i)
        joystick.init()
        joystick_flight = joystick
        break

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

    return f"Joystick X: {x}, Y: {y}, Buttons: {buttons}", (x, y, buttons)

# 模拟按键事件
def simulate_key_event(key, press=True):
    if press:
        win32api.keybd_event(key, 0, 0, 0)
    else:
        win32api.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)

# 根据摇杆输入模拟按键
def handle_joystick_input(x, y, buttons):
    commands = []
    # 映射轴到W、S、A、D
    if y < -0.5:
        simulate_key_event(win32con.VK_UP)
        commands.append("W")
    elif y > 0.5:
        simulate_key_event(win32con.VK_DOWN)
        commands.append("S")
    else:
        simulate_key_event(win32con.VK_UP, False)
        simulate_key_event(win32con.VK_DOWN, False)

    if x < -0.5:
        simulate_key_event(win32con.VK_LEFT)
        commands.append("A")
    elif x > 0.5:
        simulate_key_event(win32con.VK_RIGHT)
        commands.append("D")
    else:
        simulate_key_event(win32con.VK_LEFT, False)
        simulate_key_event(win32con.VK_RIGHT, False)

    # 映射按钮到空白键、E、B、R
    if buttons & 0x01:
        simulate_key_event(win32con.VK_SPACE)
        commands.append("Space")
    else:
        simulate_key_event(win32con.VK_SPACE, False)

    if buttons & 0x02:
        simulate_key_event(ord('E'))
        commands.append("E")
    else:
        simulate_key_event(ord('E'), False)

    if buttons & 0x04:
        simulate_key_event(ord('B'))
        commands.append("B")
    else:
        simulate_key_event(ord('B'), False)

    if buttons & 0x08:
        simulate_key_event(ord('R'))
        commands.append("R")
    else:
        simulate_key_event(ord('R'), False)

    return commands

# 提升权限并启动游戏
def launch_game_with_elevation(executable_path):
    try:
        subprocess.run(['powershell', 'Start-Process', executable_path, '-Verb', 'runAs'])
    except Exception as e:
        raise Exception(f"Failed to launch game with elevation: {str(e)}")

# 根据进程名称查找进程
def find_process_by_name(name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == name:
            return proc.info['pid']
    raise Exception(f"Process with name {name} not found")

# 捕捉进程的键盘和摇杆输入
def monitor_inputs(process_info):
    while True:
        for pid, name in process_info:
            print(f"Monitoring process: {name} (PID: {pid})")
            
        time.sleep(5)

# 建立主视窗
root = tk.Tk()
root.geometry("600x400")
root.title("Joystick HID Reports")

# 第1视窗: 显示捕捉到的摇杆动作
joystick_text = tk.Text(root, height=10, width=70)
joystick_text.pack()

# 第2视窗: 显示游戏进程信息和摇杆指令
process_text = tk.Text(root, height=10, width=70)
process_text.pack()

# 停止标志
stop_flag = False

# 捕捉和显示摇杆输入的线程
def capture_and_display():
    global stop_flag
    while not stop_flag:
        if joystick_flight:
            report, input_data = capture_joystick_input(joystick_flight)
            joystick_text.delete(1.0, tk.END)
            joystick_text.insert(tk.END, f"{report}\n")

            if input_data:
                commands = handle_joystick_input(*input_data)
                if commands:
                    process_text.insert(tk.END, f"Inserted commands: {', '.join(commands)}\n")
                    print(f"Inserted commands: {', '.join(commands)}")

        time.sleep(0.1)

def start_capture():
    global stop_flag
    stop_flag = False
    capture_thread = threading.Thread(target=capture_and_display)
    capture_thread.start()

    # 初始化
    initialize()

    # 等待捕捉输入后启动游戏
    time.sleep(1)  # 模拟捕捉到输入的等待时间

    # 游戏执行档路径
    game_executable_path = "C:\\IdentityV\\dwrg.exe"
    
    try:
        launch_game_with_elevation(game_executable_path)
    except Exception as e:
        process_text.insert(tk.END, f"Error: {str(e)}\n")
        return
    
    time.sleep(5)  # 等待游戏启动

    # 根据进程名称查找进程
    try:
        game_pid = find_process_by_name("dwrg.exe")
    except Exception as e:
        process_text.insert(tk.END, f"Error: {str(e)}\n")
        return

    # 显示摇杆和进程信息
    joystick_text.insert(tk.END, f"Joystick PID: {psutil.Process().pid}\n")
    process_text.delete(1.0, tk.END)
    process_text.insert(tk.END, f"Game Process: dwrg.exe (PID: {game_pid})\n")

    # 启动监控进程的线程
    process_info = [(game_pid, "dwrg.exe")]
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
