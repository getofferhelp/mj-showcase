from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import logging
import os
import datetime
import sys
import random

# 设置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_folders():
    # 使用相对路径或环境变量
    main_folder = os.environ.get('OUTPUT_FOLDER', './output/mj-linkdoc')
    
    # 获取当前日期
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # 创建子文件夹路径
    sub_folder = os.path.join(main_folder, today)
    
    # 计算小时并生成MD文件名
    hour_index = (datetime.datetime.now().hour // 2) + 1
    md_file_name = f"{today}-{hour_index:02d}.md"
    md_file = os.path.join(sub_folder, md_file_name)

    # 创建主文件夹和子文件夹
    os.makedirs(main_folder, exist_ok=True)
    os.makedirs(sub_folder, exist_ok=True)

    return md_file

def log_error(error_message):
    # 使用相对路径或环境变量
    log_folder = os.environ.get('LOG_FOLDER', './logs')
    os.makedirs(log_folder, exist_ok=True)
    
    # 创建日志文件
    log_file_name = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + ".txt"
    log_file_path = os.path.join(log_folder, log_file_name)
    
    # 写入日志
    with open(log_file_path, "a") as log_file:
        log_file.write(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Error: {error_message}\n")

def scrape_midjourney():
    # 设置Chrome选项以适应GitHub Actions环境
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # 无头模式
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36")  # 添加用户代理
    chrome_options.add_argument("--window-size=1920,1080")  # 设置更大的窗口尺寸
    
    driver = None
    try:
        # 输出当前检测到的时间
        current_time = datetime.datetime.now()
        logging.info(f"Starting scrape at: {current_time}")

        # 初始化WebDriver
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # 目标网页的URL
        url = 'https://www.midjourney.com/showcase'
        logging.info(f"Accessing URL: {url}")

        # 使用Selenium打开网页
        driver.get(url)

        # 等待页面加载 - 增加等待时间并等待特定元素
        logging.info("Waiting for page to load completely...")
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        time.sleep(15)  # 增加初始等待时间
        logging.info("Page loaded successfully")
        
        # 更自然的滚动页面以加载更多内容
        logging.info("Starting to scroll the page...")
        total_height = 0
        scroll_count = 0
        max_scrolls = 30  # 增加最大滚动次数
        
        # 滚动方式调整为更小增量的渐进式滚动
        for scroll in range(max_scrolls):
            # 随机滚动距离（200-500像素）
            scroll_distance = random.randint(200, 500)
            driver.execute_script(f"window.scrollBy(0, {scroll_distance});")
            scroll_count += 1
            time.sleep(random.uniform(1.5, 3.0))  # 随机等待，更像人类行为
            
            # 每5次滚动后，暂停更长时间让内容完全加载
            if scroll_count % 5 == 0:
                logging.info(f"Extended pause after {scroll_count} scrolls to let content load...")
                time.sleep(5)
            
            current_height = driver.execute_script("return document.body.scrollHeight")
            total_height += scroll_distance
            logging.info(f"Scroll {scroll_count}/{max_scrolls}, cumulative scroll: {total_height}px, page height: {current_height}")
            
            # 如果已经滚动到底部，等待一会儿再检查是否有新内容加载
            if total_height >= current_height - 1000:
                logging.info("Near the end of page, waiting for possible new content...")
                time.sleep(7)
                new_height = driver.execute_script("return document.body.scrollHeight")
                
                # 如果高度没有变化，尝试点击"加载更多"按钮（如果存在）
                if new_height == current_height:
                    try:
                        load_more = driver.find_elements(By.XPATH, '//button[contains(text(), "Load") and contains(text(), "More")]')
                        if load_more and len(load_more) > 0:
                            logging.info("Found 'Load More' button, clicking...")
                            load_more[0].click()
                            time.sleep(5)
                        else:
                            logging.info("No 'Load More' button found, may have reached true end of content")
                            break
                    except Exception as e:
                        logging.info(f"Error looking for 'Load More' button: {e}")
                        break
        
        # 找到所有预览图链接 - 尝试多种选择器
        logging.info("Finding image links...")
        logging.info(f"Page source length: {len(driver.page_source)}")
        
        # 尝试多种选择器
        selectors = [
            (By.XPATH, '//a[contains(@class, "bg-cover")]'),
            (By.CSS_SELECTOR, 'a[href*="/jobs/"]'),
            (By.CSS_SELECTOR, 'a[href*="/imagine/"]'),
            (By.XPATH, '//a[contains(@href, "/jobs/")]')
        ]
        
        image_elements = []
        for selector_type, selector in selectors:
            if len(image_elements) == 0:
                image_elements = driver.find_elements(selector_type, selector)
                logging.info(f"Tried selector: {selector}, found {len(image_elements)} elements")
        
        logging.info(f"Found {len(image_elements)} image elements total")

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
        logging.info(f"Writing links to file: {md_file}")

        # 将预览图链接写入MD文件
        with open(md_file, 'w', encoding='utf-8') as file:
            for index, image_link in enumerate(image_links):
                file.write(f"Image Link {index + 1}: {image_link}\n\n")
        
        logging.info(f"Successfully saved {len(image_links)} links to {md_file}")
        return True
        
    except Exception as e:
        error_message = f"Error in scrape_midjourney: {str(e)}"
        logging.error(error_message)
        log_error(error_message)
        return False
        
    finally:
        if driver:
            driver.quit()
            logging.info("WebDriver closed")

def main():
    # 检查是否需要单次运行模式
    single_run = False
    if len(sys.argv) > 1 and sys.argv[1] == "--single":
        single_run = True
    
    # 单次运行模式
    if single_run:
        logging.info("Running in single-run mode")
        success = scrape_midjourney()
        sys.exit(0 if success else 1)
    
    # 循环运行模式
    logging.info("Running in continuous mode")
    while True:
        max_retries = 3
        success = False
        
        for attempt in range(max_retries):
            logging.info(f"Attempt {attempt + 1}/{max_retries}")
            try:
                success = scrape_midjourney()
                if success:
                    logging.info("Scraping successful")
                    break
                else:
                    logging.warning(f"Attempt {attempt + 1} failed, retrying...")
                    time.sleep(120)  # 等待2分钟再重试
            except Exception as e:
                logging.error(f"Unexpected error in attempt {attempt + 1}: {e}")
                time.sleep(120)
        
        if not success:
            logging.error("All attempts failed")
            log_error("Failed to scrape after maximum retries")
        
        # 等待指定的时间间隔
        interval = int(os.environ.get('SCRAPE_INTERVAL_SECONDS', '7200'))  # 默认2小时
        logging.info(f"Waiting for {interval} seconds before next run")
        time.sleep(interval)

if __name__ == "__main__":
    main()