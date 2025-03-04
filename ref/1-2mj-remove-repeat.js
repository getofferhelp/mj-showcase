const fs = require('fs');
const path = require('path');

// 输入和输出文件夹路径
const inputDir = 'E:\\005-midjourneyshowcase\\1mj-linkdoc02';
const outputDir = 'E:\\005-midjourneyshowcase\\1mj-linkdoc-output';

// 每个输出文件的最大链接数
const maxLinksPerFile = 20;

// 递归读取文件夹中的所有 .md 文件
const readFilesRecursively = (dir) => {
    let files = [];
    const items = fs.readdirSync(dir);
    items.forEach(item => {
        const itemPath = path.join(dir, item);
        if (fs.statSync(itemPath).isDirectory()) {
            files = files.concat(readFilesRecursively(itemPath));
        } else if (path.extname(item) === '.md') {
            files.push(itemPath);
        }
    });
    return files;
};

// 读取文件内容并返回链接数组
const readFileLinks = (filePath) => {
    console.log(`读取文件: ${filePath}`);
    const content = fs.readFileSync(filePath, 'utf-8');
    const links = content.split('\n').filter(line => line.trim() !== '');

    // 提取以 https 开头的链接
    const extractedLinks = links
        .map(line => line.match(/https?:\/\/[^\s]+/)) // 使用正则表达式提取链接
        .filter(match => match !== null) // 过滤掉未匹配的行
        .map(match => match[0]); // 获取匹配的链接

    console.log(`文件 ${filePath} 中找到 ${extractedLinks.length} 个链接`);
    return new Set(extractedLinks); // 使用 Set 去重
};

// 获取每个子文件夹的所有链接
const getLinksByFolder = (files) => {
    const linksByFolder = new Map();

    files.forEach(file => {
        const links = readFileLinks(file);
        const relativeDir = path.relative(inputDir, path.dirname(file));
        
        if (!linksByFolder.has(relativeDir)) {
            linksByFolder.set(relativeDir, []);
        }

        linksByFolder.get(relativeDir).push(...links);
    });

    return linksByFolder;
};

// 输出结果到对应的子文件夹和文档
const outputLinks = (linksByFolder) => {
    linksByFolder.forEach((links, folderName) => {
        const uniqueLinks = Array.from(new Set(links));
        const fileCount = Math.ceil(uniqueLinks.length / maxLinksPerFile);

        for (let i = 0; i < fileCount; i++) {
            const outputFilePath = path.join(outputDir, folderName, `${folderName}-${i + 1}.md`);
            const outputDirPath = path.dirname(outputFilePath);

            // 确保输出目录存在
            if (!fs.existsSync(outputDirPath)) {
                console.log(`创建目录: ${outputDirPath}`);
                fs.mkdirSync(outputDirPath, { recursive: true });
            }

            // 获取当前文件的链接
            const startIndex = i * maxLinksPerFile;
            const endIndex = startIndex + maxLinksPerFile;
            const currentLinks = uniqueLinks.slice(startIndex, endIndex);

            // 将链接写入文件，序号从 startIndex + 1 开始
            const outputContent = currentLinks.map((link, index) => `Image Link ${startIndex + index + 1}: ${link}`).join('\n');
            fs.writeFileSync(outputFilePath, outputContent + '\n');
            console.log(`写入链接到文件: ${outputFilePath}，链接数量: ${currentLinks.length}`);
        }
    });
};

// 确保输出目录存在
if (!fs.existsSync(outputDir)) {
    console.log(`创建输出目录: ${outputDir}`);
    fs.mkdirSync(outputDir, { recursive: true });
}

// 读取所有 .md 文件
const files = readFilesRecursively(inputDir);
console.log('找到的 .md 文件:', files);

// 获取每个子文件夹的所有链接
const linksByFolder = getLinksByFolder(files);
console.log('每个子文件夹的链接信息:', linksByFolder);

// 输出结果到对应的子文件夹和文档
outputLinks(linksByFolder);

console.log('处理完成，结果已保存到输出文件夹。');