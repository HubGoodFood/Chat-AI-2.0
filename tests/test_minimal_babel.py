#!/usr/bin/env python3
"""
最小化的Flask-Babel测试
"""
from flask import Flask, render_template_string, session, request
from flask_babel import Babel, gettext, _
import os

app = Flask(__name__)
app.secret_key = 'test-secret-key'

# 配置
app.config['LANGUAGES'] = {'zh': 'Chinese', 'en': 'English'}
app.config['BABEL_DEFAULT_LOCALE'] = 'zh'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'translations'

def get_locale():
    print(f"[DEBUG] get_locale called!")
    print(f"[DEBUG] session: {dict(session)}")
    
    # 检查session中的语言设置
    if 'language' in session:
        lang = session['language']
        print(f"[DEBUG] Using session language: {lang}")
        return lang
    
    print(f"[DEBUG] Using default language: zh")
    return 'zh'

# 初始化Babel
babel = Babel(app, locale_selector=get_locale)

@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{ _('测试页面') }}</title>
    </head>
    <body>
        <h1>{{ _('管理员登录') }}</h1>
        <p>{{ _('当前语言') }}: {{ get_locale() }}</p>
        <a href="/set-lang/en">Switch to English</a> | 
        <a href="/set-lang/zh">切换到中文</a>
    </body>
    </html>
    ''')

@app.route('/set-lang/<language>')
def set_language(language):
    session['language'] = language
    print(f"[DEBUG] Language set to: {language}")
    return f"Language set to {language}. <a href='/'>Go back</a>"

if __name__ == '__main__':
    print("Starting minimal Flask-Babel test...")
    app.run(debug=True, port=5001)
