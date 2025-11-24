import os
import shutil
import subprocess

# ================= 配置区域 =================
# 输出格式 (建议 .mkv)
OUTPUT_EXT = '.mkv'
# 输入源格式 (DownKyi 默认是 .mp4)
INPUT_EXTS = ['.mp4'] 
# ===========================================

# 资源文件后缀
IMAGE_EXTS = ['.jpg', '.png', '.jpeg']
SUB_EXTS = ['.ass', '.srt']

def get_subtitle_label(filename):
    """智能命名字幕"""
    fname_lower = filename.lower()
    name, ext = os.path.splitext(fname_lower)
    label = "未知字幕"
    if ext == '.ass': label = "ASS 弹幕"
    elif ext == '.srt':
        if '中文' in name or 'chs' in name: label = "中文字幕"
        elif '日语' in name or 'jpn' in name: label = "日文字幕"
        elif '英语' in name or 'eng' in name: label = "英文字幕"
        else: label = "SRT 字幕"
    return label

def inspect_folder(folder_path):
    """
    检查文件夹状态
    返回: (状态代码, 视频文件列表, 封面, 字幕列表)
    状态代码: 
      'READY': 可以处理
      'SKIP_DONE': 包含MKV，认为是已完成的目录，跳过
      'SKIP_MULTI': 包含多个MP4，可能是未分类的目录，跳过
      'SKIP_EMPTY': 无视频
    """
    mp4_files = []
    mkv_files = [] # 关键：用于检测是否包含已完成文件
    cover_file = None
    sub_files = []
    
    try:
        files = os.listdir(folder_path)
    except Exception:
        return 'SKIP_EMPTY', [], None, []
    
    for f in files:
        full_path = os.path.join(folder_path, f)
        if not os.path.isfile(full_path):
            continue
        
        name, ext = os.path.splitext(f)
        ext = ext.lower()
        
        if "temp_" in f: continue # 忽略临时文件
        
        if ext == '.mkv':
            mkv_files.append(f)
        elif ext in INPUT_EXTS:
            mp4_files.append(f)
        elif ext in IMAGE_EXTS:
            if 'cover' in name.lower() or cover_file is None: cover_file = f
        elif ext in SUB_EXTS:
            sub_files.append(f)
            
    # === 核心安全逻辑 ===
    if len(mkv_files) > 0:
        # 只要文件夹里有 MKV，就假设这是分类目录（或者已经处理过的），绝对不动
        return 'SKIP_DONE', mkv_files, None, None
        
    if len(mp4_files) == 0:
        return 'SKIP_EMPTY', [], None, None
        
    if len(mp4_files) > 1:
        # 如果有多个 MP4 但没有 MKV，可能是一堆视频混在一起，不确定该合并谁，跳过以防万一
        return 'SKIP_MULTI', mp4_files, None, None

    # 只有当：没有MKV，且只有唯一一个MP4时，才认为是“下载子文件夹”
    # 字幕排序：ASS 优先
    sub_files.sort(key=lambda x: 0 if x.lower().endswith('.ass') else 1)
    return 'READY', mp4_files, cover_file, sub_files

def process_folder(folder_path):
    folder_name = os.path.basename(folder_path)
    parent_dir = os.path.dirname(folder_path)
    
    # 1. 检查状态
    status, videos, cover, subs = inspect_folder(folder_path)
    
    if status == 'SKIP_DONE':
        # 这是一个包含 MKV 的文件夹（比如 '术力口'），默默跳过，不要打扰它
        return False
    elif status == 'SKIP_MULTI':
        print(f"⚠️ [跳过] 文件夹含多个视频，无法自动合并: {folder_name}")
        return False
    elif status == 'SKIP_EMPTY':
        return False
        
    # status == 'READY'
    video = videos[0]
    output_filename = folder_name + OUTPUT_EXT
    output_path = os.path.join(parent_dir, output_filename)

    # 再次确认目标不存在
    if os.path.exists(output_path):
        return False

    print(f"🎬 正在处理子目录: {folder_name}")
    
    # === 构建命令 (同 v5.0) ===
    input_args = ['-i', os.path.join(folder_path, video)]
    map_args = ['-map', '0']
    metadata_args = ['-metadata', f'title={folder_name}']
    current_input_idx = 1
    
    if cover:
        input_args.extend(['-i', os.path.join(folder_path, cover)])
        map_args.extend(['-map', str(current_input_idx)])
        metadata_args.extend([
            '-c:v:1', 'mjpeg', '-disposition:v:1', 'attached_pic',
            '-metadata:s:v:1', 'title=Cover'
        ])
        current_input_idx += 1
    
    sub_stream_idx = 0
    for sub in subs:
        label = get_subtitle_label(sub)
        print(f"   -> 添加轨道: {label}")
        input_args.extend(['-i', os.path.join(folder_path, sub)])
        map_args.extend(['-map', str(current_input_idx)])
        metadata_args.extend([f'-metadata:s:s:{sub_stream_idx}', f'title={label}'])
        if 'ASS' in label:
            metadata_args.extend([f'-metadata:s:s:{sub_stream_idx}', 'language=chi'])
        current_input_idx += 1
        sub_stream_idx += 1
    
    cmd = ['ffmpeg', '-y'] + input_args + map_args + metadata_args + ['-c', 'copy']
    
    temp_output_path = os.path.join(parent_dir, f"temp_{folder_name}{OUTPUT_EXT}")
    cmd.append(temp_output_path)
    
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if os.path.exists(output_path): os.remove(output_path)
        os.rename(temp_output_path, output_path)
        try:
            shutil.rmtree(folder_path)
            print(f"✅ 完成并归档到上一级: {output_filename}\n")
        except:
            print(f"⚠️ 无法删除原文件夹\n")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 失败: {folder_name}")
        if os.path.exists(temp_output_path): os.remove(temp_output_path)
        return False

def main():
    root_dir = os.getcwd()
    print(f"🛡️ 启动安全封装程序 v6.0 (防乱序版)")
    print(f"📂 根目录: {root_dir}")
    print("--------------------------------------------------")
    
    count = 0
    # 递归遍历
    for root, dirs, files in os.walk(root_dir, topdown=False):
        for name in dirs:
            # 这里的 root 是当前文件夹的父路径， name 是文件夹名
            # 如果 root 就是 E:\mv, name 就是 '术力口'
            # 如果 root 是 E:\mv\术力口, name 就是 '【可不】Kyu-kurarin...'
            
            full_path = os.path.join(root, name)
            if process_folder(full_path):
                count += 1
                
    print("--------------------------------------------------")
    if count == 0:
        print("💤 没有发现需要处理的新下载（分类文件夹已自动跳过）。")
    else:
        print(f"🎉 全部完成，新处理了 {count} 个视频。")
    input("按回车键退出...")

if __name__ == '__main__':
    main()
