import sys
content = open('app.py').read()
old_route = '@app.get("/verify-token")'
if 'X-API-Key' not in content:
    new_route = '@app.get("/verify-token")\nasync def authenticated_route(request: Request):\n    api_key = request.headers.get("X-API-Key")\n    if api_key == "surfsense":\n        return {"message": "API Key is valid"}\n'
    # Find the original function definition and replace the whole block
    import re
    content = re.sub(r'@app\.get\("/verify-token"\)\nasync def authenticated_route\(.*?\):.*?return \{"message": "Token is valid"\}', new_route, content, flags=re.DOTALL)
    with open('app.py', 'w') as f:
        f.write(content)
