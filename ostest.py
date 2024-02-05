import sys
from filetool import get_file_size
from aiohttp import web
import aiohttp
import asyncio

chunk_size = 1024

async def download(request):
    downloadfilepath = request.query['name']
    chunk_size = 1024
    file_size = get_file_size(downloadfilepath)
    # 编写请求头
    headers = {
        'Content-Type': 'video/mp4',
        'Content-Disposition': f'attachment; filename="{downloadfilepath}"',
        'Content-Length': str(file_size)
    }    
    with open(downloadfilepath, 'rb') as f:
        print_len = 0
        total_write = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                print('读取完成')
                break
            total_write += len(chunk)
            if(total_write/1024/1024 > print_len):
                print(total_write/1024/1024)
                print_len+=0.01
    async def file_stream():
        with open(downloadfilepath, 'rb') as f:
            print_len = 0
            total_write = 0
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    print('发送完成')
                    break
                total_write += len(chunk)
                if(total_write/1024/1024 > print_len):
                    print(total_write/1024/1024)
                    print_len+=0.01
                yield chunk
                
    print('发送中')    
    print('---download complete---')
    print(headers)
    return web.Response(body=file_stream(), headers=headers)

async def file_stream():
    with open('1.mp4', 'rb') as f:
        print_len = 0
        total_write = 0
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                print('发送完成1')
                break
            total_write += len(chunk)
            if(total_write/1024/1024 > print_len):
                # print(total_write/1024/1024)
                print_len+=0.01
            yield chunk
async def main():
    async for chunk in file_stream():
        # 处理数据块
        pass
# asyncio.run(main())
print(aiohttp.__version__)
app = web.Application()     
app.router.add_get('/download', download)
web.run_app(app)

# http://localhost:8080/download?name=1.mp4
# http://107.174.67.157:8080/download?name=1.mp4