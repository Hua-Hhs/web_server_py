import os
import json

anime_root_path = 'E:\\web\\anime\\'
class anime:
    def __init__(self,title,chapter_num,chapter_list) -> None:
        self.title = title
        self.chapter_num = chapter_num
        self.chapter_list = chapter_list
        
        pass
class animeinfolist:
    def __init__(self):
        self.anime_root_path = anime_root_path
    # 获取动画根路径下所有文件夹，就是所有动画
    def get_all_anime_folder(self):
        anime_folders = [f for f in os.listdir(anime_root_path) if os.path.isdir(os.path.join(anime_root_path, f))]
        return anime_folders
    # 获取所有动画信息
    def get_all_anime_infos(self):
        folders = self.get_all_anime_folder()
        animeinfo = []
        for folder in folders:
            animeinfo.append(list.get_anime_info(folder))
        return animeinfo
    # 根据相对路径获取动画信息
    def get_anime_info(self,folder):
        anime_folder = os.path.join(self.anime_root_path,folder)
        info_json = os.path.join(anime_folder,'info.json')
        with open(info_json, 'r') as f:
            json_file = json.load(f)
            return json_file


def add_param(file_path,key,value):
    
    json_info = {}
    with open(file_path,'r') as f:
        json_info = json.load(f)
    if(key in json_info):
        json_info[key] = value
    else:
        json_info[key] = value
    with open(file_path,'w') as f:
        json.dump(json_info,f)



list = animeinfolist()
folders = list.get_all_anime_folder()
for a in folders:
    path = os.path.join(anime_root_path,a)
    path = os.path.join(path,'info.json')
    add_param(path,'cover','cover.jpg')



# print(list.get_all_anime_infos())
