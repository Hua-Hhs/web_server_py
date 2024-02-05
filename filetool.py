import os
import urllib.parse

def get_file_size(filepath):
    try:
        size = os.path.getsize(filepath)
        return size
    except FileNotFoundError:
        print('---get_file_size:---')
        print(f"File '{filepath}' not found.")
        return None

# 只计算相对路径，不计算实际路径，需要额外凭借实际路径
def next_path(current_path,folder_name):
    '''-1刷新当前页，空返回上一级，其他进入下一级'''
    if(folder_name != '-1' and folder_name):         
        folder_path = os.path.join(current_path, folder_name)
        current_path = os.path.join(current_path, folder_name)
        print('...next_path:...')
        print('go ', folder_path)

    elif(not folder_name):        
        '''回退上一级'''
        current_path = os.path.dirname(current_path)   
        if(not current_path):
            current_path = ''
        print('...next_path:...') 
        print('back ',current_path)
    else:
        '''刷新当前页'''
        print('...next_path:...')
        print('refrash ',current_path)
    return current_path

# 获取文件夹下的所有文件，判断文件是否为文件夹，获取大小
def get_path_file_info(folder_path):
    # folder_path = os.path.join(file_root_path,folder_path)
    file_info_list = []
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)
        is_directory = os.path.isdir(item_path)
        if(get_file_size(item_path)):
            size_int = os.path.getsize(item_path)
            # size_mb = os.path.getsize(item_path) / (1024 * 1024)  # 文件大小转换为MB
            size_mb = size_int / (1024 * 1024)
            size_mb = "{:.2f}".format(size_mb) + 'MB'  # 保留两位小数"
        else :
            size_mb = ''
            size_int = 0
        quoted_file_name = urllib.parse.quote(item)        
        file_info_list.append({
            'quoted_file_name' : quoted_file_name,
            'file_name': item,
            'is_directory': is_directory,
            'size_mb': size_mb,
            'size_int':size_int
        })
    return file_info_list
    
def get_empty_file_info_list():
    file_info_list = []
    file_info_list.append({
            'quoted_file_name' : '',
            'file_name': '',
            'is_directory': True,
            'size_mb': '',
            'size_int':0
        })

    return file_info_list