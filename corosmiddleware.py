from aiohttp import web
class CORSMiddleware:  
    async def __call__(self, app, handler):  
        async def log_request(request):  
            if request.method == 'OPTIONS':  
                response = web.Response()  
                response.headers['Access-Control-Allow-Origin'] = '*'    
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'    
                response.headers['Access-Control-Allow-Headers'] = 'Origin, Content-Type, X-Requested-With'    
                return response  
            else:  
                response = await handler(request)    
                response.headers['Access-Control-Allow-Origin'] = '*'    
                response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'    
                response.headers['Access-Control-Allow-Headers'] = 'Origin, Content-Type, X-Requested-With'    
                return response 
            return response  
        return log_request 