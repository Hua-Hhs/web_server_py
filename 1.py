import argparse
import os
import aiohttp
import aiohttp_jinja2
import jinja2
import asyncio
from aiohttp import web, WSMsgType
from aiohttp_jinja2 import get_env
import urllib.parse
import aiofiles
from urltool import getRefreshUrl
from aiohttp import MultipartWriter, MultipartReader
from filetool import get_file_size, next_path, get_path_file_info, get_empty_file_info_list
from corosmiddleware import CORSMiddleware
import sys
import time
import base64
import io
import uuid
import urllib.parse

anime_root_path = 'E:\\web\\anime\\'
special_client_connection = None
special_files = []
special_files_id = []
current_special_files_info = {'is_used': True}
anime_titles = []
anime_covers = []
anime_chapter_list = []
anime_chapter_list_id = []
my_text = ''
current_path = ''
# 脚本所在文件夹
script_path = os.path.dirname(os.path.abspath(__file__))
# 存贮文件的根目录
file_root_path = os.path.join(script_path, 'files')
# html模板文件夹
templates_path = os.path.join(script_path, 'templates/')


# 创建aiohttp应用实例
app = web.Application(client_max_size=1024**2*1000)
app.middlewares.append(CORSMiddleware())
# 设置静态文件夹，用于程序调用静态文件
app.router.add_static('/static/', path=script_path + '/static', name='static')

# 设置Jinja2模板环境
aiohttp_jinja2.setup(
    app, loader=jinja2.FileSystemLoader(templates_path)
)


async def send_file_to_client(file_path, file_name):
    chunk_size = 8192
    file_size = get_file_size(file_path)
    # 编写请求头
    headers = {
        'Content-Disposition': f'attachment; filename="{file_name}"',
        'Content-Length': str(file_size)
    }
    # 发送文件

    async def file_stream():
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    return web.Response(body=file_stream(), headers=headers)


# 首页
async def index(request):
    # print('11')
    global my_text
    # files = os.listdir(file_root_path)
    file_info_list = get_path_file_info(file_root_path)
    # print('22')

    special_folder_path = ''
    special_file_info_list = await get_special_client_folder_info(special_folder_path)
    # print('33')
    data = {
        'file_info_list': file_info_list,
        'current_path': '',
        'special_file_info_list': special_file_info_list,
        'special_current_path': '',
        'my_text': my_text
    }
    # print('22')
    return web.json_response(data)


async def upload(request):
    if request.method == 'GET':
        return {}  # 空字典作为模板上下文数据
    elif request.method == 'POST':
        data = await request.post()
        print(data)
        current_path = data['current_path']

        field = data['file']
        file_name = field.filename
        # print(file_name)
        print(field.file)
        save_path = os.path.join(current_path, file_name)
        save_path = os.path.join(file_root_path, save_path)
        total_write = 0
        print_len = 0.1
        print('...savepath... ', save_path)
        if field.filename:
            # 保存上传的文件到服务器
            with open(save_path, 'wb') as f:
                while True:
                    chunk = field.file.read(1024)  # 读取文件块

                    if not chunk:
                        print('上传完成')
                        break
                    f.write(chunk)
                    total_write += len(chunk)
                    # print(total_write)
                    if (total_write/1024/1024 > print_len):
                        sys.stdout.write(
                            f"\r{'%.2f MB'%(total_write/1024/1024)}")
                        sys.stdout.flush()
                        print_len += 0.01

    return web.json_response({"message": "seccess"})


async def rewrite_text(request):
    current_path = request.query['current_path']
    postdata = await request.post()
    global my_text
    my_text = postdata.get('new_text')
    print(my_text)
    print('---')
    print('create_folder')
    # with open('1.txt','w',encoding='utf-8') as f:
    #     f.write(my_text)
    special_current_path = request.query['special_current_path']
    url = getRefreshUrl(current_path, special_current_path)
    # print(url)
    print('---create_folder complete---')
    raise web.HTTPFound(url)

async def download2(request):
    # return web.FileResponse('')
    return web.FileResponse('E:\\web\\myweb\\files\\video.mp4')


async def download(request):
    
    current_path = request.query['current_path']
    # 从html获取文件夹的名字
    file_name = request.query['file_name']
    # 拼接绝对路径
    downloadfilepath = os.path.join(file_root_path, current_path)
    downloadfilepath = os.path.join(downloadfilepath, file_name)
    
    # # 定义分块传输的块的大小，获取文件大小
    chunk_size = 8192
    file_size = get_file_size(downloadfilepath)
    # 编写请求头
    headers = {
        'Content-Disposition': f'attachment; filename="{file_name}"',
        'Content-Length': str(file_size)
    } 
    # return web.FileResponse(downloadfilepath,headers=headers)
    # 发送文件
    print('开始发送', downloadfilepath)

    async def file_stream():
        with open(downloadfilepath, 'rb') as f:
            print_len = 0
            total_write = 0
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                total_write += len(chunk)
                if (total_write/1024/1024 > print_len):
                    sys.stdout.write(
                        f"\r{'%.2f / %.2f MB'%(total_write/1024/1024,file_size/1024/1024)}")
                    sys.stdout.flush()
                    print_len += 0.01
                yield chunk
    print('发送中')
    return web.Response(body=file_stream(), headers=headers)



# 展示文件夹
# 参数folder_name为空时返回上一级，为-1时刷新文件夹，其他为进入名为folder_name的的值的文件夹
async def list_directory(request):
    global my_text
    postdata = await request.json()
    # print(postdata)
    current_path = postdata.get("current_path")
    folder_name = postdata.get("folder_name")
    special_current_path = postdata.get("special_current_path")
    special_folder_name = postdata.get("special_folder_name")

    current_path = folder_path = next_path(current_path, folder_name)
    folder_path = os.path.join(file_root_path, folder_path)
    file_info_list = get_path_file_info(folder_path)

    special_current_path = special_folder_path = next_path(
        special_current_path, special_folder_name)

    special_file_info_list = await get_special_client_folder_info(special_folder_path)
    env = get_env(request.app)

    data = {
        'file_info_list': file_info_list,
        'current_path': current_path,
        'special_file_info_list': special_file_info_list,
        'special_current_path': special_current_path,
        'my_text': my_text
    }

    print('---list_directory complete---')
    return web.json_response(data)
    # return web.Response(text=html_content, content_type='text/html')
# 创建文件夹


async def create_folder(request):
    # current_path = request.query['current_path']
    postdata = await request.json()
    folder_name = postdata.get('folder_name')
    current_path = postdata.get('current_path')
    print('---')
    print('create_folder')

    folder_path = os.path.join(file_root_path, current_path)
    folder_path = os.path.join(folder_path, folder_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return web.json_response({"message": "seccess"})

# async def create_folder1(request):
    current_path = request.query['current_path']
    postdata = await request.post()
    folder_name = postdata.get('folder_name')
    print('---')
    print('create_folder')
    folder_path = os.path.join(file_root_path, current_path)
    folder_path = os.path.join(folder_path, folder_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    special_current_path = request.query['special_current_path']
    url = getRefreshUrl(current_path, special_current_path)
    # print(url)
    print('---create_folder complete---')
    raise web.HTTPFound(url)


# 通过文件的UUID（自定义的UUID）为文件缓冲区添加新文件
def add_new_special_file(UUID):
    global special_files_id
    global special_files
    special_files_id.append(UUID)
    special_files.append({'UUID': UUID, 'Data': []})
    pass

# 根据文件UUID删除文件缓冲区的文件
def delete_special_files(UUID):
    global special_files_id
    global special_files
    index = special_files_id.index(UUID)
    special_files.pop(index)
    special_files_id.pop(index)

# 通过文件的UUID（自定义的UUID）为文件缓冲区添加新文件
def add_new_chapter(UUID):
    global anime_chapter_list_id
    global anime_chapter_list
    anime_chapter_list_id.append(UUID)
    anime_chapter_list.append({'UUID': UUID, 'chapters': []})
    pass

# 根据文件UUID删除文件缓冲区的文件
def delete_chapter(UUID):
    global anime_chapter_list_id
    global anime_chapter_list
    index = anime_chapter_list_id.index(UUID)
    anime_chapter_list_id.pop(index)
    anime_chapter_list.pop(index)

# 与特殊客户端建立连接并循环接收报文


async def handle_special_client(request):
    global special_client_connection
    special_client_connection = web.WebSocketResponse()
    await special_client_connection.prepare(request)

    print(special_client_connection)
    print('建立连接')
    while True:
        if not is_client_conecting(special_client_connection):
            print('断开连接')
            break
        while True:
            msg = await special_client_connection.receive_json()
            try:
                # 客户端发送文件头报文用于识别不同文件或同一文件的多次同时请求时分别记录不同进度
                # 发送的报文类型为文件头报文，获取报文的UUID，在文件缓冲区创建文件，用于接收发来的文件,herder从
                if (msg['Type'] == 'header'):
                    pass
                    # UUID = msg['UUID']
                    # add_new_special_file(UUID)
                # 接收文件
                elif (msg['Type'] == 'file'):
                    UUID = msg['UUID']
                    data = msg['Data']
                    index = special_files_id.index(UUID)
                    special_files[index]['Data'].append(data)
                    # data = {'Chunk' : chunk, 'Is_the_last' : False}
                # 接收文件夹信息
                elif (msg['Type'] == 'folder'):
                    global current_special_files_info
                    # print(msg)
                    current_special_files_info = msg['Infos']
                    # current_special_files_info.append({'is_used'L})
                elif (msg['Type'] == 'chapters'):
                    UUID = msg['UUID']
                    chapters = msg['chapters']
                    index = anime_chapter_list_id.index(UUID)
                    anime_chapter_list[index]['chapters'] = chapters
                elif (msg['Type'] == 'title'):
                    global anime_titles 
                    anime_titles = msg['titles']
                

            except Exception as e:
                print(f"download special file error: {e} ")
                break
        await asyncio.sleep(2)

    return special_client_connection


async def save_file(reader, file_path):
    with open(file_path, 'wb') as f:
        while True:
            chunk = await reader.read_chunk()
            if not chunk:
                break
            f.write(chunk)


async def receive_special_file(file_name):
    global special_client_connection

    msg = await special_client_connection.receive()
    if msg.type == WSMsgType.binary:
        print('接收' + file_name + '中')
        with open(file_name, "wb") as file:
            file.write(bytes(msg.data))
            while True:
                msg = await special_client_connection.receive()
                if msg.type == WSMsgType.binary:
                    yield bytes(msg.data)
                elif msg.type == WSMsgType.TEXT:
                    print('接收' + file_name + '完毕')
                    break
    elif msg.type == WSMsgType.CLOSED:
        special_client_connection = None
        return
    elif msg.type == WSMsgType.TEXT:
        print(msg.data)


def is_client_conecting(special_client_connection):
    return special_client_connection != None and not special_client_connection.closed


async def send_to_special_client(message):
    global special_client_connection

    if is_client_conecting(special_client_connection):
        print('send to client')
        await special_client_connection.send_str(message)


async def get_special_client_folder_info(folder_path):
    if is_client_conecting(special_client_connection):
        headers = {
            'Type': 'folder',
            'Path': folder_path
        }
        global current_special_files_info
        # print(headers)
        await special_client_connection.send_json(headers)
        # print(current_special_files_info)
        while current_special_files_info['is_used']:
            # print(current_special_files_info)
            await asyncio.sleep(0.1)

        msg = current_special_files_info['file_info_list']
        current_special_files_info['is_used'] = True
        # print('111')
        return msg
    else:

        print('---get_special_client_folder_info:---')
        print('连接已断开')
        return get_empty_file_info_list()


async def download_special_file(request):
    global special_client_connection

    if not is_client_conecting(special_client_connection):
        print('---download_special_file:---')
        print('连接已断开')
        current_path = request.query['current_path']
        special_file_name = request.query['special_file_name']
        special_file_size = request.query['special_file_size']
        url = getRefreshUrl(current_path, special_file_name)
        print(url)
        raise web.HTTPFound(url)

    special_current_path = request.query['special_current_path']
    special_file_name = request.query['special_file_name']
    special_file_size = request.query['special_file_size']
  
    path = os.path.join(special_current_path, special_file_name)
    UUID = str(uuid.uuid4())
    headers = {
        'Type': 'file',
        'Path': path,
        'UUID': UUID,
        'FileType': 'file'
    }
    add_new_special_file(UUID)
    await special_client_connection.send_json(headers)
    # chunk_size = 8192
    # file_size = get_file_size(special_file_name)
    # 编写请求头
    headers = {
        'Content-Disposition': f'attachment; filename="{special_file_name}"',
        'Content-Length': str(special_file_size)
    }
    # global special_files
    # global special_files_id

    # async def get_next_chunk_by_id(UUID):

    #     index = special_files_id.index(UUID)
    #     chunks = special_files[index]['Data']

    #     while True:
    #         if chunks:
    #             break
    #         await asyncio.sleep(0.1)

    #     current_chunk = chunks[0]
    #     # chunks.pop(0)
    #     delete_special_files(UUID)
    #     return current_chunk

    # async def file_stream(UUID):
    #     while True:
    #         current_chunk = await get_next_chunk_by_id(UUID)
    #         chunk_data = current_chunk['Chunk']
    #         # print(current_chunk)
    #         # 将字符串重新编码为utf-8的二进制序列（该序列被b64编码过）
    #         chunk_data = chunk_data.encode(encoding='utf-8')
    #         # b64解码,获得原二进制序列
    #         chunk_data = base64.b64decode(chunk_data)

    #         # print(chunk_data)
    #         yield chunk_data
    #         if current_chunk['Is_the_last'] == True:
    #             break

    print('---download_special_file complete---')
    print('接收中')
    return web.Response(body=file_stream(UUID), headers=headers)

async def read_file_in_chunks(file_path, chunk_size=1024*1024):  # 默认块大小为1MB
    with open(file_path, "rb") as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            yield chunk


def parse_range_header(range_header, file_size):
    # print(range_header)
    _, range_values = range_header.split('=')
    start_str, end_str = range_values.split('-')

    # 处理空字符串的情况，使用默认值
    start = int(start_str) if start_str else 0
    end = int(end_str) if end_str else file_size - 1

    return start, end


async def get_video_from_client_with_range(range,title,chapter):
    global special_client_connection
    UUID = str(uuid.uuid4())
    data = {'UUID':UUID,'Range':range,'Title':title, 'Chapter':chapter}
    await special_client_connection.send_json({'Type': 'file','FileType': 'video','UUID':UUID, 'Data': data})
    add_new_special_file(UUID)
    
    index = special_files_id.index(UUID)
    data = special_files[index]['Data']
    # print(2)
    while not data:
        await asyncio.sleep(0.1)
    # print(data)
    data = data[0]
    print(data['file_size'])
    file_size = data['file_size']
    start = data['start'] 
    end= data['end']
    request_size = data['request_size']
    chunk = data['chunk']
    chunk = chunk.encode(encoding='utf-8')
    # b64解码,获得原二进制序列
    chunk = base64.b64decode(chunk)
    return file_size, start, end, request_size, chunk




async def test2(request):
    path = 'E:\\web\\myweb\\files\\bule bird\\video.mp4'  # Set the correct path to your video file
    try:
        file_size = os.path.getsize(path)
        range_header = request.headers.get('Range')
        # print(range_header)

        # if range_header:
            
        #     # _, range_values = range_header.split('=')
        #     # start, end = range_values.split('-')
        #     # start = int(start) if start else 0
        #     # end = int(end) if end else file_size - 1

        #     start, end = parse_range_header(range_header, file_size)
        #     request_size = end - start + 1
        # else:
        #     start = 0
        #     end = file_size - 1
        #     request_size = file_size


        file_size, start, end, request_size, chunk =await get_video_from_client_with_range(range_header)
        
        headers = {
            'Accept-Ranges': 'bytes',
            'Content-Type': 'video/mp4',
        }

        if not range_header:
            headers['Content-Disposition'] = 'attachment; filename=test.mp4'
            headers['Content-Length'] = str(file_size)
        else:
            headers['Content-Length'] = str(request_size)
            headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'

        response = web.StreamResponse(headers=headers)
        

        if range_header:
            response.set_status(206)

        await response.prepare(request)
        await response.write(chunk)
        # with open(path, 'rb') as file:
        #     file.seek(start)
        #     while request_size > 0:
        #         chunk_size = min(4096, request_size)
        #         data = file.read(chunk_size)
        #         await response.write(data)
        #         request_size -= chunk_size

        await response.write_eof()
        return response

    except Exception as e:
        print(f"Error: {e}")
        raise web.HTTPInternalServerError()



async def handle_video_request(request): 
    title = request.query['title']     
    chapter = request.query['chapter']

    # path = 'E:\\web\\myweb\\files\\bule bird\\video.mp4'  # Set the correct path to your video file
    try:
        # file_size = os.path.getsize(path)
        range_header = request.headers.get('Range')
        file_size, start, end, request_size, chunk =await get_video_from_client_with_range(range_header,title,chapter)
        
        headers = {
            'Accept-Ranges': 'bytes',
            'Content-Type': 'video/mp4',
        }

        if not range_header:
            headers['Content-Disposition'] = 'attachment; filename=test.mp4'
            headers['Content-Length'] = str(file_size)
        else:
            headers['Content-Length'] = str(request_size)
            headers['Content-Range'] = f'bytes {start}-{end}/{file_size}'

        response = web.StreamResponse(headers=headers)
        
        if range_header:
            response.set_status(206)

        await response.prepare(request)
        await response.write(chunk)
        await response.write_eof()
        return response

    except Exception as e:
        print(f"Error: {e}")
        raise web.HTTPInternalServerError()


async def get_anime_info(request):
    # 连接特殊服务器时使用
    global special_client_connection
    print('get_anime_info')
    # msg = {'Type'}
    await special_client_connection.send_json({'Type': 'animeinfo'})
    global anime_titles
    while (not anime_titles):
        await asyncio.sleep(1)
        pass
    msg={'titles':anime_titles}
    
    anime_titles = []
    print('get_anime_info_over')
    # msg = {"titles": [
    #     "魔圆",
    #     "bule bird",
    #     "Trick"
    # ]}
    return web.json_response(msg)

async def get_current_anime_chapter(request):
    msg = await request.json()
    # print(postdata)
    print(request)
    current_anime_title = msg.get("current_path")
    # current_anime_title = request.query['current_anime_title']
    global special_client_connection
    UUID = str(uuid.uuid4())
    msg = {
        'Type': 'chapters',
        'Title': current_anime_title,
        'UUID': UUID,
    }
    await special_client_connection.send_json(msg)
    global anime_chapter_list_id
    add_new_chapter(UUID)
    print(anime_chapter_list_id)
    index = anime_chapter_list_id.index(UUID)
    chapters = anime_chapter_list[index]['chapters']
    while(not chapters):
        await asyncio.sleep(0.1)
        chapters = anime_chapter_list[index]['chapters']
    delete_chapter(UUID)
    print(chapters)
    print('get_current_anime_chapter_over')
    return web.json_response({'chapters':chapters})
    

async def get_next_chunk_by_id(UUID):

    index = special_files_id.index(UUID)
    chunks = special_files[index]['Data']

    while True:
        if chunks:
            break
        await asyncio.sleep(0.1)

    current_chunk = chunks[0]
    # delete_special_files(UUID)
    chunks.pop(0)
    return current_chunk

async def file_stream(UUID):
    while True:
        current_chunk = await get_next_chunk_by_id(UUID)
        chunk_data = current_chunk['Chunk']
        # print(current_chunk)
        # 将字符串重新编码为utf-8的二进制序列（该序列被b64编码过）
        chunk_data = chunk_data.encode(encoding='utf-8')
        # b64解码,获得原二进制序列
        chunk_data = base64.b64decode(chunk_data)

        # print(chunk_data)
        yield chunk_data
        if current_chunk['Is_the_last'] == True:
            break
async def get_anime_cover(request):
    global anime_root_path
    title = request.query['title']

    UUID = str(uuid.uuid4())
    headers = {
        'Type': 'file',
        'Path': title,
        'UUID': UUID,
        'FileType': 'cover'
    }
    add_new_special_file(UUID)
    await special_client_connection.send_json(headers)

    # global special_files
    # global special_files_id


    return web.Response(body=file_stream(UUID))

    # return web.Response(body=read_file_in_chunks(cover_path))


# async def get_file_blocks(file_path):  
#     file_path = 'E:\\web\\myweb\\files\\bule bird\\video.mp4'
#     file_size = os.path.getsize(file_path)  
#     block_size = 1024 * 1024  # 1MB  
#     blocks = []  
#     with open(file_path, 'rb') as file:  
#         for i in range(0, file_size, block_size):  
#             block = file.read(min(block_size, file_size - i))  
#             blocks.append(block)  
#     # block = urllib.parse.quote(block)  
#     data = {'block':block}
#     return block  


app.router.add_get('/', index)
app.router.add_get('/upload', upload)
app.router.add_post('/upload', upload)
app.router.add_get('/rewrite_text', rewrite_text)
app.router.add_post('/rewrite_text', rewrite_text)
app.router.add_get('/download', download)
app.router.add_post('/download', download)
app.router.add_get('/list', list_directory)
app.router.add_post('/list', list_directory)
app.router.add_post('/createfolder', create_folder)
app.router.add_get('/9000', handle_special_client)
app.router.add_get('/download_special_file', download_special_file)
# app.router.add_get('/test2', test2)
app.router.add_get('/handle_video_request', handle_video_request)
app.router.add_post('/handle_video_request', handle_video_request)
app.router.add_get('/get_anime_cover', get_anime_cover)
app.router.add_post('/get_anime_cover', get_anime_cover)
app.router.add_get('/get_anime_info', get_anime_info)

app.router.add_get('/get_current_anime_chapter', get_current_anime_chapter)
app.router.add_post('/get_current_anime_chapter', get_current_anime_chapter)
# app.router.add_post('/get_anime_info', get_anime_info)
# app.router.add_get('/get-file-blocks', get_file_blocks)


if __name__ == '__main__':
    # with open('1.txt','r', encoding='utf-8') as f:
    #     my_text = f.read()
    # 设置默认端口，可手动指定端口   python 1.py 20000
    parser = argparse.ArgumentParser(description='Run aiohttp server')
    parser.add_argument('port', type=int, nargs='?',
                        default=20000, help='Port to run the server on')
    args = parser.parse_args() 
    web.run_app(app, host='0.0.0.0', port=args.port)

            
