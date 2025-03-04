import schedule
import time
import subprocess
import os

# 定义要执行的 JavaScript 脚本路径
script1 = 'E:\\005-midjourneyshowcase\\001-jb\\1-2mj-remove-repeat.js'
script2 = 'E:\\005-midjourneyshowcase\\001-jb\\2-4mj-img-prompt.js'

# 定义执行脚本的函数
def run_scripts():
    print("正在执行脚本...")
    try:
        # 使用 subprocess 执行第一个脚本
        subprocess.run(['node', script1], check=True)
        print(f"成功执行: {script1}")
        
        # 使用 subprocess 执行第二个脚本
        subprocess.run(['node', script2], check=True)
        print(f"成功执行: {script2}")
    except subprocess.CalledProcessError as e:
        print(f"执行脚本时出错: {e}")

# 在启动时立即运行脚本
run_scripts()

# 每天早上 10 点执行脚本
schedule.every().day.at("16:40").do(run_scripts)

print("调度器已启动...")

# 持续运行调度器
while True:
    schedule.run_pending()
    time.sleep(60)  # 每分钟检查一次