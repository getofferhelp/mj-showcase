import os
import json
import logging
from datetime import datetime, timedelta
import time
import random
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MJFileProcessor:
    def __init__(self):
        # 使用环境变量或默认值设置路径
        self.input_dir = os.environ.get('INPUT_DIR', './output/mj-linkdoc')
        self.output_dir = os.environ.get('OUTPUT_DIR', './output/mj-linkdoc-output')
        self.json_output_dir = os.environ.get('JSON_OUTPUT_DIR', './output/mj-linkdoc-json')
        self.max_links_per_file = 20

    def get_yesterday_date(self):
        """获取前一天的日期"""
        yesterday = datetime.now() - timedelta(days=1)
        return yesterday.strftime('%Y-%m-%d')

    def get_yesterday_compact(self):
        """获取用于JSON文件名的紧凑日期格式"""
        yesterday = datetime.now() - timedelta(days=1)
        return yesterday.strftime('%Y%m%d')

    def random_delay(self):
        """添加随机延迟"""
        delay = random.uniform(1, 3)  # 1-3秒的随机延迟
        logger.info(f"随机延迟 {delay:.2f} 秒...")
        time.sleep(delay)

    def read_file_links(self, file_path):
        """读取文件中的链接"""
        logger.info(f"读取文件: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # 提取链接
        links = []
        for line in content.split('\n'):
            if line.strip() and 'https://' in line:
                link = line.split('https://', 1)[1].split()[0]
                links.append(f"https://{link}")

        logger.info(f"文件 {file_path} 中找到 {len(links)} 个链接")
        self.random_delay()
        return links

    def get_yesterday_files(self):
        """获取前一天的所有.md文件"""
        yesterday = self.get_yesterday_date()
        yesterday_dir = Path(self.input_dir) / yesterday
        
        if not yesterday_dir.exists():
            logger.info(f"前一天的目录不存在: {yesterday_dir}")
            return []
        
        logger.info(f"处理前一天({yesterday})的文件")
        return list(yesterday_dir.glob('*.md'))

    def process_files(self):
        """处理所有文件并生成输出"""
        # 创建输出目录
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.json_output_dir).mkdir(parents=True, exist_ok=True)

        # 获取前一天的文件
        files = self.get_yesterday_files()
        logger.info(f"找到前一天的 .md 文件数量: {len(files)}")

        if not files:
            logger.info("没有找到前一天的文件，程序退出。")
            return

        # 收集所有链接
        all_links = []
        for file_path in files:
            links = self.read_file_links(file_path)
            all_links.extend(links)

        # 去重
        unique_links = list(dict.fromkeys(all_links))
        logger.info(f"共收集到 {len(all_links)} 个链接，去重后剩余 {len(unique_links)} 个")

        # 输出MD文件
        self.output_md_files(unique_links)
        
        # 输出JSON文件
        self.output_json_file(unique_links)

    def output_md_files(self, unique_links):
        """将链接分批输出到MD文件"""
        yesterday = self.get_yesterday_date()
        output_dir = Path(self.output_dir) / yesterday
        output_dir.mkdir(parents=True, exist_ok=True)

        for i in range(0, len(unique_links), self.max_links_per_file):
            batch = unique_links[i:i + self.max_links_per_file]
            file_num = (i // self.max_links_per_file) + 1
            output_file = output_dir / f"{yesterday}-{file_num:02d}.md"

            content = '\n\n'.join(f"Image Link {i + 1}: {link}" 
                                for i, link in enumerate(batch, start=i + 1))
            
            output_file.write_text(content + '\n', encoding='utf-8')
            logger.info(f"写入链接到文件: {output_file}，链接数量: {len(batch)}")
            self.random_delay()

    def output_json_file(self, unique_links):
        """输出JSON文件，按月/日组织文件夹结构"""
        yesterday = datetime.now() - timedelta(days=1)
        month_folder = yesterday.strftime('%m')  # 获取月份（01-12）
        day_folder = yesterday.strftime('%d')    # 获取日期（01-31）
        date_str = yesterday.strftime('%Y%m%d')  # 用于文件名

        # 构建完整的输出路径：json_output_dir/月/日/
        json_folder = Path(self.json_output_dir) / month_folder / day_folder
        json_folder.mkdir(parents=True, exist_ok=True)

        # JSON文件路径
        json_file = json_folder / f"midjourney_links_{date_str}.json"

        json_data = {
            'date': self.get_yesterday_date(),
            'total': len(unique_links),
            'links': unique_links
        }

        json_file.write_text(
            json.dumps(json_data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        logger.info(f"已将{len(unique_links)}个去重链接写入JSON文件: {json_file}")

def main():
    processor = MJFileProcessor()
    processor.process_files()

if __name__ == "__main__":
    main() 