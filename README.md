# 🍽️ 食用方法（Usage）

下载器本体：
👉 **[哔哩下载姬（DownKyi 改进版）](https://github.com/yaobiao131/downkyicore/releases)**

---

## 0️⃣ 前提准备

0. python 3.7+
1. 下载并安装 **FFmpeg**
2. 将 `ffmpeg/bin` 加入系统环境变量 **PATH**
3. 终端输入以下命令确认可用：

```bash
ffmpeg -version
```

能输出版本号即可。

---

## 1️⃣ 放置脚本

**[下载脚本](https://github.com/daishuge/downkyi-improvement/releases/download/v0.1/main.py)**

将 `main.py` 放在你的下载根目录，例如：

```
mv/
 ├─ 视频1/
 ├─ 视频2/
 └─ main.py
```

---

## 2️⃣ 运行

双击运行 `main.py` 或使用终端：

```bash
python main.py
```

然后你就可以 **enjoy it! 🎉**

---

## 3️⃣ 程序自动完成的事

* 🔍 自动识别每个子目录
* 🎬 合并：

  * 视频
  * 封面（如存在 `cover.jpg/png`）
  * 字幕（`.ass`/`.srt` 自动命名 track）
* 📦 输出为 `目录名.mkv`（无重编码、无损封装）
* 📤 自动移到上一级目录
* 🧹 成功后删除原子文件夹

**无需额外操作，全自动运行。**

备注: 感谢gemini 3.0提供的无私帮助