const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
const fs = require('fs-extra');
const path = require('path');

puppeteer.use(StealthPlugin());

// 定义输入和输出根目录
const inputRootDir = 'E:\\005-midjourneyshowcase\\1mj-linkdoc-output';
const outputRootDir = 'E:\\005-midjourneyshowcase\\2mj-imgtextdocs';
const saveFolder = path.join(outputRootDir, 'images');
const notLoadedFile = path.join(outputRootDir, 'notloaded.md');

// 创建保存图片的文件夹
fs.ensureDirSync(saveFolder);

(async () => {
    const browser = await puppeteer.launch({ headless: false });
    const page = await browser.newPage();

    // 递归遍历目录
    const processDirectory = async (dir) => {
        const files = fs.readdirSync(dir);

        for (const file of files) {
            const filePath = path.join(dir, file);
            const stat = fs.statSync(filePath);

            if (stat.isDirectory()) {
                // 检查输出文件夹中是否已经存在同名子文件夹
                const outputDir = path.join(outputRootDir, path.relative(inputRootDir, filePath));
                if (fs.existsSync(outputDir)) {
                    console.log(`跳过处理: ${file}（输出文件夹中已存在）`);
                    continue; // 跳过当前文件夹的处理
                }

                // 如果是目录,递归调用
                await processDirectory(filePath);
            } else if (file.endsWith('.md')) {
                // 如果是 Markdown 文件,处理链接
                const outputDir = path.join(outputRootDir, path.relative(inputRootDir, dir));
                if (!fs.existsSync(outputDir)) {
                    fs.mkdirSync(outputDir, { recursive: true });
                }

                const fileName = path.basename(file, '.md');
                const [year, month, day] = fileName.split('-'); // 提取年、月、日

                // 读取 Markdown 文件内容
                const content = fs.readFileSync(filePath, 'utf-8');

                // 提取链接
                const links = [];
                const linkRegex = /Image Link \d+: (https:\/\/www\.midjourney\.com\/jobs\/[^\s]+)/g;
                let match;
                while ((match = linkRegex.exec(content)) !== null) {
                    links.push(match[1]);
                }

                // 处理每个链接
                let images = [];
                for (let i = 0; i < links.length; i++) {
                    const url = links[i];
                    console.log(`处理链接: ${url}`);
                    await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });

                    let text;
                    try {
                        await page.waitForSelector('div.break-word p', { timeout: 15000 });
                        text = await page.$eval('div.break-word p', el => el.innerText);
                    } catch (e) {
                        console.log("未找到文本元素");
                        text = null; // 修改为 null
                    }

                    let imageUrls;
                    try {
                        await page.waitForSelector('img[src*="cdn.midjourney.com"]', { timeout: 15000 });
                        imageUrls = await page.$$eval('img[src*="cdn.midjourney.com"]', imgs => imgs.map(img => img.src));
                    } catch (e) {
                        console.log("未找到图像元素");
                        imageUrls = []; // 保持为空数组
                    }

                    const jpegImageUrl = imageUrls.find(imgUrl => imgUrl.endsWith('.jpeg')) || imageUrls[0] || '';

                    // 如果没有提取到图像和文本，则跳过该链接
                    if (!jpegImageUrl && !text) {
                        console.log(`跳过链接: ${url} (图像和文本均未找到)`);
                        continue; // 直接跳过
                    }

                    // 如果提取到图像或文本，添加到images数组
                    images.push({
                        src: jpegImageUrl,
                        text: text ? text.replace(/(^"|"$)/g, '').replace(/"/g, "'") : null
                    });

                    // 下载图片
                    if (jpegImageUrl) {
                        const subfolder = jpegImageUrl.split('/')[3]; // 获取UUID部分
                        const imageName = jpegImageUrl.split('/').pop(); // 获取文件名
                        const imagePath = path.join(saveFolder, subfolder, imageName);

                        // 检查图像是否已经存在
                        if (!fs.existsSync(imagePath)) {
                            await downloadImage(page, jpegImageUrl, subfolder, imageName, i === 0); // 第一个链接需要验证
                        } else {
                            console.log(`图像已存在，跳过保存: ${imagePath}`);
                        }
                    }

                    // 等待适当的时间以避免影响网站
                    await new Promise(resolve => setTimeout(resolve, 10000)); // 等待10秒
                }

                // 生成 YAML 头信息
                const yamlHeader = `---
author: "GoWithAI.Help"  
date: ${new Date().toISOString().slice(0, 10)}
images:
`;

                // 写入输出文件
                const outputFilePath = path.join(outputDir, file);
                const outputContent = yamlHeader + 
                      images.map(image => `  - src: ${image.src}\n    text: >\n        ${image.text ? image.text.replace(/\n/g, '\n        ') : ''}`).join('\n') + '\n\n' +
                      '---\n\n' +
                      `## ${year}年${month}月${day}日 MJ精选例图\n\n` +
                      `
<div style="text-align: center; margin-bottom: 20px;">
                          <button 
                            style="border-radius: 50%; padding: 20px; background-color: #28a745; color: white; border: none; cursor: pointer; width: 60px; height: 60px; transition: background-color 0.3s, transform 0.2s; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);" 
                            onmouseover="this.style.backgroundColor='#218838'; this.style.transform='scale(1.05';" 
                            onmouseout="this.style.backgroundColor='#28a745'; this.style.transform='scale(1)';" 
                            onclick="location.reload();">
                            刷
                          </button>
                          <div style="margin-top: 10px; font-size: 14px; color: #555;">网络不好，刷一下</div>
                        </div>
                        ` +
                      '<PhotoGallery :images="$frontmatter.images" lazy />'; // 添加 lazy

                fs.writeFileSync(outputFilePath, outputContent);
                console.log(`处理结果已写入: ${outputFilePath}`);
            }
        }
    };

    // 下载图片
    async function downloadImage(page, url, subfolder, imageName, isFirstImage) {
        const subfolderPath = path.join(saveFolder, subfolder);
        await fs.ensureDir(subfolderPath);

        // 访问图片链接
        await page.goto(url, { waitUntil: 'networkidle0', timeout: 70000 }); // 延长加载时间到70秒

        // 如果是第一次图片,等待用户完成验证
        if (isFirstImage) {
            console.log(`请完成验证并等待...`);
            await new Promise(resolve => setTimeout(resolve, 10000)); // 等待10秒以确保用户有足够的时间完成验证
        }

        // 获取图片的 URL
        const imageUrl = page.url(); // 直接获取当前页面的 URL
        const imageFileName = imageName.replace(/\)/g, '').replace(/\(/g, '').replace(/[^a-zA-Z0-9_.-]/g, ''); // 去掉小括号和其他无效字符

        // 下载图片
        try {
            const viewSource = await page.goto(imageUrl);
            await fs.writeFile(path.join(subfolderPath, imageFileName), await viewSource.buffer());
            console.log(`下载成功: ${path.join(subfolderPath, imageFileName)}`);
        } catch (error) {
            console.error(`下载失败: ${url}，错误信息: ${error.message}`);
            
            // 如果下载失败,重试5次
            for (let i = 0; i < 5; i++) {
                try {
                    const viewSource = await page.goto(imageUrl, { waitUntil: 'networkidle0', timeout: 70000 }); // 延长加载时间到70秒
                    await fs.writeFile(path.join(subfolderPath, imageFileName), await viewSource.buffer());
                    console.log(`重试成功: ${path.join(subfolderPath, imageFileName)}`);
                    return;
                } catch (retryError) {
                    console.error(`重试失败 (${i + 1}/5): ${url}，错误信息: ${retryError.message}`);
                }
            }
            
            // 如果重试5次后仍然失败,记录到notloaded.md文件
            await fs.appendFile(notLoadedFile, `- ${url}\n`);
            console.error(`已记录到 notloaded.md: ${url}`);
        }
    }

    // 开始处理根目录
    await processDirectory(inputRootDir);

    await browser.close();
    console.log("所有链接处理完成。");
})();