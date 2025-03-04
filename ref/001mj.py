from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
import os
import datetime

# 设置日志
logging.basicConfig(level=logging.INFO)

# 设置Selenium WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

def create_folders():
    # 主文件夹路径
    main_folder = r"E:\005-midjourneyshowcase\1mj-linkdoc"
    
    # 获取当前日期
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # 创建子文件夹路径
    sub_folder = os.path.join(main_folder, today)
    
    # 计算小时并生成MD文件名
    hour_index = (datetime.datetime.now().hour // 2) + 1
    md_file_name = f"{today}-{hour_index:02d}.md"
    md_file = os.path.join(sub_folder, md_file_name)

    # 创建子文件夹
    if not os.path.exists(sub_folder):
        os.makedirs(sub_folder)

    return md_file

def job():
    try:
        # 输出当前检测到的时间
        current_time = datetime.datetime.now()
        logging.info(f"Current detected time: {current_time}")

        # 目标网页的URL
        url = 'https://www.midjourney.com/showcase'

        # 使用Selenium打开网页
        driver.get(url)

        # 等待页面加载
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

        # 滚动页面以加载更多内容
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(3)  # 等待加载
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # 找到所有预览图链接
        image_elements = driver.find_elements(By.XPATH, '//div[@class="absolute @container/jobCard group/jobCard overflow-hidden border-transparent"]//a[@class="block bg-cover bg-center w-full h-full bg-light-skeleton overflow-hidden dark:bg-dark-skeleton"]')

        image_links = []
        for index, image_element in enumerate(image_elements):
            try:
                # 获取预览图链接
                image_link = image_element.get_attribute('href')
                logging.info(f"Image link {index + 1}: {image_link}")
                image_links.append(image_link)

            except Exception as e:
                logging.error(f"Error processing image {index + 1}: {e}")

        # 创建MD文件路径
        md_file = create_folders()

        # 将预览图链接写入MD文件
        with open(md_file, 'w', encoding='utf-8') as file:
            for index, image_link in enumerate(image_links):
                file.write(f"Image Link {index + 1}: {image_link}\n\n")

    finally:
        # 关闭浏览器
        driver.quit()

# 运行一次任务
job()