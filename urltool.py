import urllib.parse

def getRefreshUrl(current_path,special_current_path):
    current_path = urllib.parse.quote(current_path)
    special_current_path = urllib.parse.quote(special_current_path)
    return '/list?current_path=' + current_path + '&folder_name=-1' + '&special_current_path=' + special_current_path +'&special_folder_name=-1'
