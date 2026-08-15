#!/usr/bin/env python3
# backend.py - Vibecode AI Engine
# Deployable to Render, Vercel, or any Python host

import os
import json
import re
import zipfile
import io
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins="*")

PORT = int(os.environ.get('PORT', 5000))

# ─── DEPLOYMENT TEMPLATES ──────────────────────────────────

DEPLOYMENT_TEMPLATES = {
    "render": '''services:
  - type: web
    name: {{project_name}}
    runtime: python
    repo: https://github.com/{{username}}/{{project_name}}
    branch: main
    plan: free
    envVars:
      - key: FLASK_SECRET_KEY
        generateValue: true
      - key: LOG_LEVEL
        value: INFO
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn backend:app -w 1
    healthCheckPath: /
    autoDeploy: true''',

    "vercel": '''{
  "rewrites": [
    { "source": "/(.*)", "destination": "/" }
  ],
  "builds": [
    { "src": "backend.py", "use": "@vercel/python" },
    { "src": "frontend/*", "use": "@vercel/static" }
  ],
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "Access-Control-Allow-Origin", "value": "*" }
      ]
    }
  ]
}''',

    "netlify": '''[build]
  command = "pip install -r requirements.txt"
  functions = "functions"
  publish = "frontend"

[build.environment]
  PYTHON_VERSION = "3.11"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200''',

    "docker": '''FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY backend.py .
COPY frontend ./frontend

EXPOSE 5000

CMD ["python", "backend.py"]''',

    "aws": '''service: {{project_name}}
provider:
  name: aws
  runtime: python3.11
  region: us-east-1

functions:
  api:
    handler: backend.handler
    events:
      - http:
          path: /
          method: ANY
      - http:
          path: /{proxy+}
          method: ANY

plugins:
  - serverless-python-requirements''',

    "heroku": '''web: gunicorn backend:app -w 1
release: python manage.py migrate
worker: python worker.py'''
}

# ─── CODE GENERATION ──────────────────────────────────────

def generate_code(prompt, language):
    prompt_lower = prompt.lower()
    code = ""
    explanation = ""

    # ─── HTML ──────────────────────────────────────────────────
    if language == "html":
        if "login" in prompt_lower or "form" in prompt_lower:
            code = '''<!DOCTYPE html>
<html>
<head><title>Login</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#0a0e17;display:flex;justify-content:center;align-items:center;min-height:100vh}
.login{background:rgba(255,255,255,0.03);padding:40px;border-radius:16px;border:1px solid rgba(255,255,255,0.05);width:100%;max-width:400px}
.login h2{color:#e2e8f0;margin-bottom:24px;text-align:center}
.login input{width:100%;padding:14px 16px;margin-bottom:16px;border-radius:8px;border:1px solid rgba(255,255,255,0.06);background:rgba(0,0,0,0.3);color:#e2e8f0;font-size:14px}
.login input:focus{outline:none;border-color:#6c5ce7}
.login button{width:100%;padding:14px;border:none;border-radius:8px;background:linear-gradient(135deg,#6c5ce7,#a29bfe);color:#fff;font-size:16px;font-weight:600;cursor:pointer}
.login button:hover{transform:translateY(-2px)}
</style>
</head>
<body>
<div class="login">
<h2>🔐 Login</h2>
<input type="email" placeholder="Email" id="email">
<input type="password" placeholder="Password" id="password">
<button onclick="alert('Login: '+document.getElementById('email').value)">Sign In</button>
</div>
</body>
</html>'''
            explanation = "Dark-themed login form with email and password."

        elif "todo" in prompt_lower:
            code = '''<!DOCTYPE html>
<html>
<head><title>Todo List</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#0a0e17;display:flex;justify-content:center;padding:40px}
.todo{background:rgba(255,255,255,0.03);padding:30px;border-radius:16px;width:100%;max-width:500px;border:1px solid rgba(255,255,255,0.05)}
.todo h2{color:#e2e8f0;margin-bottom:20px}
.todo input{width:70%;padding:12px 16px;border-radius:8px;border:1px solid rgba(255,255,255,0.06);background:rgba(0,0,0,0.3);color:#e2e8f0}
.todo button{padding:12px 20px;border:none;border-radius:8px;background:#6c5ce7;color:#fff;cursor:pointer;margin-left:8px}
.todo ul{list-style:none;margin-top:16px}
.todo li{padding:10px 14px;background:rgba(255,255,255,0.03);border-radius:6px;margin-bottom:6px;color:#e2e8f0;display:flex;justify-content:space-between}
.todo li button{background:#ef5350;padding:4px 12px;font-size:12px}
</style>
</head>
<body>
<div class="todo">
<h2>📋 Todo List</h2>
<div><input type="text" id="taskInput" placeholder="Enter task..."><button onclick="addTask()">Add</button></div>
<ul id="taskList"></ul>
</div>
<script>
function addTask(){
const input=document.getElementById('taskInput');
if(!input.value.trim())return;
const li=document.createElement('li');
li.innerHTML='<span>'+input.value+'</span><button onclick="this.parentElement.remove()">✕</button>';
document.getElementById('taskList').appendChild(li);
input.value='';
}
</script>
</body>
</html>'''
            explanation = "Todo list with add and delete functionality."

        else:
            code = '''<!DOCTYPE html>
<html>
<head><title>Vibecode</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#0a0e17;color:#e2e8f0;display:flex;justify-content:center;align-items:center;min-height:100vh}
.card{background:rgba(255,255,255,0.03);padding:40px;border-radius:16px;border:1px solid rgba(255,255,255,0.05);text-align:center;max-width:500px}
.card h1{font-size:24px;background:linear-gradient(135deg,#6c5ce7,#a29bfe);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.card p{color:#718096;margin-top:12px}
</style>
</head>
<body>
<div class="card"><h1>⚡ Vibecode</h1><p>Your AI-generated page is ready.</p></div>
</body>
</html>'''
            explanation = "Clean HTML page with gradient title."

    # ─── PYTHON ──────────────────────────────────────────────────
    elif language == "python":
        if "scrape" in prompt_lower or "web" in prompt_lower:
            code = '''import requests
from bs4 import BeautifulSoup
def scrape_website(url):
    try:
        r=requests.get(url,timeout=10)
        r.raise_for_status()
        s=BeautifulSoup(r.text,'html.parser')
        for script in s(["script","style"]): script.decompose()
        return "\\n".join([line.strip() for line in s.get_text().splitlines() if line.strip()])
    except Exception as e: return f"Error: {e}"
if __name__=="__main__": print(scrape_website(input("URL: "))[:500])'''
            explanation = "Web scraper that extracts text from any URL."

        elif "api" in prompt_lower or "flask" in prompt_lower:
            code = '''from flask import Flask,request,jsonify
from flask_cors import CORS
app=Flask(__name__)
CORS(app)
@app.route('/')
def home(): return jsonify({"message":"API running","status":"ok"})
@app.route('/api/data',methods=['GET','POST'])
def data():
    if request.method=='POST': return jsonify({"received":request.json,"status":"success"})
    return jsonify({"message":"Send POST with JSON"})
if __name__=='__main__': app.run(host='0.0.0.0',port=5000,debug=True)'''
            explanation = "Flask REST API with CORS and data endpoint."

        else:
            code = '''# Vibecode Python Template
import os, sys
def main():
    print("⚡ Vibecode Python Generator")
    print(f"Python: {sys.version}")
    print("✅ Ready to run!")
if __name__=="__main__": main()'''
            explanation = "Python script template with version info."

    # ─── JAVASCRIPT ──────────────────────────────────────────────
    elif language == "javascript":
        if "fetch" in prompt_lower or "api" in prompt_lower:
            code = '''async function fetchData(url) {
    try {
        const r=await fetch(url);
        if(!r.ok)throw new Error(`HTTP ${r.status}`);
        const data=await r.json();
        console.log('Data:',data);
        return data;
    } catch(e){console.error('Error:',e.message);return null;}
}
fetchData('https://api.github.com/users/octocat').then(console.log);'''
            explanation = "Async function to fetch JSON from any API."

        else:
            code = '''// Vibecode JavaScript Template
console.log('⚡ Vibecode JS Generator');
function greet(name){return `Hello, ${name}!`;}
module.exports={greet};'''
            explanation = "JavaScript module with greeting function."

    # ─── GO ──────────────────────────────────────────────────────
    elif language == "go":
        code = '''package main
import ("fmt""net/http")
func main(){
    http.HandleFunc("/",func(w http.ResponseWriter,r *http.Request){fmt.Fprintf(w,"⚡ Vibecode Go Server")})
    http.HandleFunc("/api",func(w http.ResponseWriter,r *http.Request){w.Header().Set("Content-Type","application/json");fmt.Fprintf(w,`{"message":"Go API running"}`)})
    fmt.Println("Server on :8080");http.ListenAndServe(":8080",nil)
}'''
        explanation = "Go web server with JSON API."

    # ─── RUST ────────────────────────────────────────────────────
    elif language == "rust":
        code = '''fn main(){
    println!("⚡ Vibecode Rust");
    let sum: i32 = vec![1,2,3,4,5].iter().sum();
    println!("Sum: {}", sum);
}'''
        explanation = "Rust program with vector operations."

    # ─── DEPLOYMENT FILES ──────────────────────────────────────
    elif language == "docker":
        code = '''FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn","app:app","-w","1"]'''
        explanation = "Dockerfile for containerizing Python applications."

    elif language == "vercel":
        code = '''{"rewrites":[{"source":"/(.*)","destination":"/"}],"headers":[{"source":"/(.*)","headers":[{"key":"Access-Control-Allow-Origin","value":"*"}]}]}'''
        explanation = "vercel.json for deploying to Vercel."

    elif language == "render":
        code = '''services:
  - type: web
    name: my-app
    runtime: python
    repo: https://github.com/your-username/your-repo
    branch: main
    plan: free
    envVars:
      - key: FLASK_SECRET_KEY
        generateValue: true
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app -w 1
    autoDeploy: true'''
        explanation = "render.yaml for one-click deployment on Render."

    else:
        code = f'# Vibecode Generated\nprint("Hello from Vibecode!")\nprint(f"Language: {language}")'
        explanation = "Generic template with your prompt and language."

    return {"code": code, "explanation": explanation, "language": language}

# ─── PROJECT GENERATOR ────────────────────────────────────

def generate_project(prompt):
    prompt_lower = prompt.lower()
    
    project_name = "vibecode-app"
    name_match = re.search(r'call it\s+(\w+)', prompt_lower)
    if name_match:
        project_name = name_match.group(1)
    
    username = "your-username"
    user_match = re.search(r'username\s+(\w+)', prompt_lower)
    if user_match:
        username = user_match.group(1)
    
    platform = "render"
    if "vercel" in prompt_lower:
        platform = "vercel"
    elif "netlify" in prompt_lower:
        platform = "netlify"
    elif "docker" in prompt_lower:
        platform = "docker"
    elif "aws" in prompt_lower:
        platform = "aws"
    elif "heroku" in prompt_lower:
        platform = "heroku"
    
    structure = {
        "backend.py": generate_code(prompt, "python")["code"],
        "requirements.txt": "Flask==2.3.3\nflask-cors==4.0.0\ngunicorn==21.2.0\nrequests==2.31.0\n",
        "frontend/index.html": generate_code(prompt, "html")["code"],
        "frontend/app.js": '''const API_URL = window.location.hostname === 'localhost' ? 'http://localhost:5000/api' : '/api';
document.addEventListener('DOMContentLoaded', async () => {
    try {
        const r = await fetch(API_URL + '/data');
        const data = await r.json();
        document.getElementById('apiResponse').textContent = JSON.stringify(data, null, 2);
    } catch(e) {
        document.getElementById('apiResponse').textContent = 'Error: ' + e.message;
    }
});''',
        "frontend/style.css": '''*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',sans-serif;background:#0a0e17;color:#c8d6e5;min-height:100vh;display:flex;justify-content:center;align-items:center;padding:20px}
.card{background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.05);border-radius:12px;padding:24px;max-width:600px;width:100%}
h1{background:linear-gradient(135deg,#6c5ce7,#a29bfe);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
#apiResponse{background:rgba(0,0,0,0.3);padding:12px 16px;border-radius:8px;font-family:monospace;font-size:13px;color:#a0aec0;min-height:60px}'''
    }
    
    if platform == "render":
        structure["render.yaml"] = DEPLOYMENT_TEMPLATES["render"].replace("{{project_name}}", project_name).replace("{{username}}", username)
    elif platform == "vercel":
        structure["vercel.json"] = DEPLOYMENT_TEMPLATES["vercel"]
    elif platform == "netlify":
        structure["netlify.toml"] = DEPLOYMENT_TEMPLATES["netlify"]
    elif platform == "docker":
        structure["Dockerfile"] = DEPLOYMENT_TEMPLATES["docker"]
    elif platform == "aws":
        structure["serverless.yml"] = DEPLOYMENT_TEMPLATES["aws"].replace("{{project_name}}", project_name)
    elif platform == "heroku":
        structure["Procfile"] = DEPLOYMENT_TEMPLATES["heroku"]
    
    structure["README.md"] = f'''# {project_name}

Generated by **Vibecode AI** — Deployable in one click.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

Live at: `https://{project_name}.onrender.com`
'''
    
    return {
        "name": project_name,
        "username": username,
        "platform": platform,
        "structure": structure,
        "url": f"https://{project_name}.onrender.com",
        "instructions": f"""
🚀 DEPLOYMENT INSTRUCTIONS

1. Push to GitHub:
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/{username}/{project_name}
   git push -u origin main

2. Deploy to {platform.capitalize()}:
   - Go to https://{platform}.com
   - Click "New" → Connect your repo
   - Click "Deploy"

3. Live at: https://{project_name}.onrender.com
"""
    }

# ─── API ROUTES ────────────────────────────────────────────

@app.route('/')
def index():
    return jsonify({
        'status': 'Vibecode AI Online',
        'version': '3.0',
        'endpoints': {
            '/api/generate': 'POST - Generate code',
            '/api/deploy': 'POST - Generate deployable project',
            '/api/download': 'POST - Download project as ZIP',
            '/api/languages': 'GET - List supported languages'
        }
    })

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.json
    prompt = data.get('prompt', '')
    language = data.get('language', 'python')
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    return jsonify(generate_code(prompt, language))

@app.route('/api/deploy', methods=['POST'])
def deploy():
    data = request.json
    prompt = data.get('prompt', '')
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    return jsonify(generate_project(prompt))

@app.route('/api/download', methods=['POST'])
def download():
    data = request.json
    prompt = data.get('prompt', '')
    if not prompt:
        return jsonify({'error': 'No prompt provided'}), 400
    
    project = generate_project(prompt)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path, content in project['structure'].items():
            zip_file.writestr(f"{project['name']}/{file_path}", content)
    zip_buffer.seek(0)
    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name=f"{project['name']}.zip")

@app.route('/api/languages', methods=['GET'])
def languages():
    return jsonify({
        'languages': ['python', 'javascript', 'html', 'go', 'rust', 'docker', 'vercel', 'render'],
        'deployment': ['render', 'vercel', 'netlify', 'docker', 'aws', 'heroku']
    })

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat(), 'version': '3.0'})

# ─── MAIN ──────────────────────────────────────────────────

if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                   VIBECODE AI ENGINE                     ║
    ║  ⚡ Generate & Deploy Projects in One Click              ║
    ║                                                          ║
    ║  API:   http://localhost:5000/api                       ║
    ║  Status: Online                                         ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=PORT, debug=False)
