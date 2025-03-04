import os
import time
from datetime import datetime

# 定义脚本路径
script_folder = r"E:\005-midjourneyshowcase\001-jb"
scripts = ["001mj.py"]
log_folder = r"E:\005-midjourneyshowcase\001-jb\777-miss"

# 确保日志文件夹存在
os.makedirs(log_folder, exist_ok=True)

def log_skipped_script(script_name):
    # 获取当前时间
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file_name = datetime.now().strftime("%Y%m%d%H%M%S") + ".txt"
    log_file_path = os.path.join(log_folder, log_file_name)

    # 写入日志
    with open(log_file_path, "a") as log_file:
        log_file.write(f"{current_time} - Skipped: {script_name}\n")

def execute_script(script_path):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            os.system(f'python "{script_path}"')  # 执行脚本
            return True  # 如果执行成功，返回True
        except Exception as e:
            print(f"Attempt {attempt + 1} failed for {script_path}: {e}")
            time.sleep(120)  # 等待2分钟再重试
    return False  # 如果所有尝试都失败，返回False

def execute_scripts():
    while True:
        for script in scripts:
            script_path = os.path.join(script_folder, script)
            if os.path.exists(script_path):
                success = execute_script(script_path)
                if not success:
                    log_skipped_script(script)  # 记录跳过的脚本
                    break  # 跳出当前脚本执行循环，等待2小时后再尝试
            else:
                log_skipped_script(script)  # 记录跳过的脚本
                continue  # 跳过不存在的脚本

        # 等待2小时
        time.sleep(7200)  # 7200秒 = 2小时

if __name__ == "__main__":
    execute_scripts()