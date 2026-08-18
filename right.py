#!/usr/bin/env python3
# new Env("恩山论坛每日签到")
# Python3依赖:DrissionPage,requests
# Linux依赖:chromium,chromium-chromedriver

import json
import time
import os
import re
import random
import shutil
from DrissionPage import ChromiumPage, ChromiumOptions

# 呆呆面板配置 - 从环境变量获取
ENSHAN_COOKIE = os.getenv('ENSHAN_COOKIE', '')
# 写死的配置
USER_UID = "327034"  # 请替换为你的实际UID
ENABLE_RANDOM_WAIT = False  # True=启用随机延迟, False=禁用

# 统一的 User-Agent
USER_AGENT = "Mozilla/5.0 (Linux; Android 13; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Mobile Safari/537.36"

def random_wait():
    """随机倒数函数 (0-900秒)"""
    if ENABLE_RANDOM_WAIT:
        delay = random.randint(0, 900)
        print(f"🎲 随机延迟启动: 将在 {delay} 秒后开始执行任务...")
        time.sleep(delay)
        print("⏰ 倒计时结束，任务开始！")
    else:
        print("⏩ 随机延迟已禁用，直接开始执行任务")

def force_kill_chrome():
    """强制清理残留的浏览器进程"""
    print("🧹 正在清理残留的浏览器进程...")
    try:
        os.system("pkill -f chromium")
        os.system("pkill -f chrome")
        time.sleep(2) 
    except:
        pass

def system_notify(title, content):
    """呆呆面板通知函数"""
    try:
        # 呆呆面板使用 print 输出，由面板捕获
        print(f"📨 [通知] {title}")
        print(f"📨 [内容] {content}")
        print('✅ 通知已发送')
        return True
    except Exception as e:
        print(f'⚠️ 通知发送失败: {e}')
        return False

def save_cookie_to_file(cookie_str):
    """保存Cookie到本地文件（可选）"""
    try:
        if not cookie_str:
            return
        # 保存到文件，方便调试
        with open('enshan_cookie_backup.txt', 'w', encoding='utf-8') as f:
            f.write(cookie_str)
        print("💾 Cookie 已备份到 enshan_cookie_backup.txt")
    except Exception as e:
        print(f"❌ 保存 Cookie 失败: {str(e)}")

def get_cookies_safe(page):
    try:
        ret = page.run_cdp('Network.getCookies')
        cookies_list = ret.get('cookies', [])
        return "; ".join([f"{item['name']}={item['value']}" for item in cookies_list])
    except Exception as e:
        print(f"❌ 获取 Cookie 异常: {e}")
        return ""

def extract_regex(pattern, text, default="0"):
    try:
        match = re.search(pattern, text)
        return match.group(1).strip() if match else default
    except:
        return default

def run_sign_in():
    # 1. 检查Cookie
    if not ENSHAN_COOKIE:
        print("❌ 错误: 环境变量 ENSHAN_COOKIE 未设置")
        system_notify("恩山签到失败", "❌ 环境变量 ENSHAN_COOKIE 未设置，请检查配置")
        return
    
    if not USER_UID:
        print("❌ 错误: USER_UID 未设置")
        system_notify("恩山签到失败", "❌ USER_UID 未设置，请修改脚本")
        return
    
    # 随机延迟
    random_wait()
    
    print(f"📋 当前配置:")
    print(f"  - UID: {USER_UID[:2]}***{USER_UID[-2:] if len(USER_UID) > 4 else ''}")
    print(f"  - Cookie: {ENSHAN_COOKIE[:30]}...")
    print(f"  - 随机延迟: {'启用' if ENABLE_RANDOM_WAIT else '禁用'}")
    print("=" * 50)

    # 3. 初始化浏览器配置
    co = ChromiumOptions()
    
    # 随机生成端口
    rand_port = random.randint(9300, 19000)
    co.set_local_port(rand_port)
    print(f"🔌 分配随机通信端口: {rand_port}")
    
    # 随机生成独立临时数据目录
    rand_dir = f"/tmp/drissionpage_enshan_{rand_port}"
    co.set_user_data_path(rand_dir)
    print(f"📁 分配独立数据目录: {rand_dir}")
    
    # 无头模式
    co.set_argument('--headless=new')
    
    # 核心环境参数
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-gpu')
    co.set_argument('--disable-dev-shm-usage')
    
    # 杂项优化参数
    co.set_argument('--disable-software-rasterizer')
    co.set_argument('--disable-features=VizDisplayCompositor')
    co.set_argument('--disable-extensions')
    co.set_argument('--disable-popup-blocking')
    
    co.set_argument('--window-size=375,812')
    co.set_user_agent(user_agent=USER_AGENT)
    
    # 路径检测
    browser_path = ""
    if os.path.exists("/usr/bin/chromium-browser"):
        browser_path = "/usr/bin/chromium-browser"
    elif os.path.exists("/usr/bin/chromium"):
        browser_path = "/usr/bin/chromium"
    elif os.path.exists("/usr/bin/google-chrome"):
        browser_path = "/usr/bin/google-chrome"
    elif os.path.exists("/usr/bin/chrome"):
        browser_path = "/usr/bin/chrome"
    
    if browser_path:
        co.set_paths(browser_path=browser_path)
        print(f"✅ 使用浏览器: {browser_path}")
    else:
        print("❌ 未找到 chromium/chrome 可执行文件，请检查依赖安装！")
        system_notify("恩山签到错误", "❌ 未找到浏览器可执行文件")
        return
    
    # 4. 尝试启动浏览器
    page = None
    for attempt in range(3):
        try:
            force_kill_chrome()
            page = ChromiumPage(co)
            if page: 
                print(f"✅ 浏览器启动成功 (尝试 {attempt+1}/3)")
                break
        except Exception as e:
            print(f"⚠️ 浏览器启动失败 (第 {attempt+1} 次尝试): {e}")
            time.sleep(5)
    
    if not page:
        print("❌ 浏览器连续启动失败，放弃执行。")
        system_notify("恩山签到错误", "❌ 浏览器连续启动失败，请检查系统环境")
        shutil.rmtree(rand_dir, ignore_errors=True)
        return

    try:
        print("=== 开始执行恩山签到 ===")
        
        # 5. 访问主页 & 注入 Cookie
        print("1. 访问主页确立作用域...")
        page.get('https://www.right.com.cn/forum/forum.php?mobile=2', timeout=30, retry=2)
        try: 
            page.set.cookies(ENSHAN_COOKIE)
            print("✅ Cookie 注入成功")
        except Exception as e:
            print(f"⚠️ Cookie注入异常: {e}")
        
        print("2. 刷新页面并过盾...")
        page.refresh()
        time.sleep(5)
            
        title = page.title
        if "安全" in title or "验证" in title:
            print("🛡️ 检测到防火墙拦截，正在等待自动跳转...")
            time.sleep(15)

        # 6. 获取 Formhash
        print("3. 正在获取签到信息...")
        check_url = "https://www.right.com.cn/forum/erling_qd-sign_in_m.html"
        page.get(check_url, timeout=30, retry=2)
        time.sleep(3) 
        
        is_signed = False
        html = page.html
        
        # 提取 Formhash
        formhash = extract_regex(r"var FORMHASH = '([0-9a-zA-Z]+)'", html, "")
        if not formhash:
            formhash = extract_regex(r'name="formhash" value="([0-9a-zA-Z]+)"', html, "")
        if not formhash:
            formhash = extract_regex(r'formhash=([0-9a-zA-Z]+)', html, "")
            
        # 登录检测
        if not formhash:
            try:
                if "登录" in page.ele('tag:body').text:
                    print("❌ 严重错误: Cookie 已失效，变为游客状态。")
                    system_notify("恩山签到失败", "❌ Cookie 已失效，请更新环境变量 ENSHAN_COOKIE")
                    return
            except: pass
        
        # 签到状态检测
        try:
            body_text = page.ele('tag:body').text
            if "连续签到" in body_text and "立即签到" not in body_text:
                is_signed = True
                print("ℹ️ 状态: 今天已经签到过了。")
        except: pass
            
        if not formhash and not is_signed:
            print("❌ 错误: 无法提取 formhash")
            system_notify("恩山签到失败", "❌ 无法提取 Formhash，可能页面结构已变化")
            return
        
        if formhash:
            print(f"🔑 获取 Formhash 成功: {formhash}")

        # 7. 执行签到 (JS 注入)
        sign_success = False
        sign_msg = "已签到"
        
        if not is_signed:
            sign_api = "https://www.right.com.cn/forum/plugin.php?id=erling_qd:action&action=sign"
            print("🚀 正在发送签到请求...")
            js_code = f"""
            return fetch("{sign_api}", {{
                method: "POST",
                headers: {{
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "X-Requested-With": "XMLHttpRequest"
                }},
                body: "formhash={formhash}"
            }}).then(response => response.json());
            """
            try:
                result = page.run_js(js_code)
                print(f"📥 签到接口返回: {result}")
                if result and (result.get('success') or "已经签到" in str(result)):
                    sign_success = True
                    sign_msg = result.get('message', '签到成功')
                else:
                    sign_msg = result.get('message', '未知错误') if result else "接口无响应"
            except Exception as js_err:
                print(f"❌ JS 执行异常: {js_err}")
                sign_success = False
                sign_msg = "JS执行失败或WAF拦截"
        else:
            sign_success = True

        # 8. 最终数据获取与推送
        if sign_success:
            print("4. 正在获取最终积分数据...")
            
            # 8.1 获取签到数据
            page.get(check_url)
            time.sleep(2)
            sign_html = page.html
            today_points = extract_regex(r'erqd-current-point[^>]*>(\d+)', sign_html, "未知")
            if today_points == "未知": today_points = extract_regex(r'今日积分.*?(\d+)', sign_html, "未知")
            continuous_days = extract_regex(r'erqd-continuous-days[^>]*>(\d+)', sign_html, "未知")
            if continuous_days == "未知": continuous_days = extract_regex(r'连续签到.*?(\d+)', sign_html, "未知")
            total_days = extract_regex(r'erqd-total-days[^>]*>(\d+)', sign_html, "未知")
            if total_days == "未知": total_days = extract_regex(r'总签到天数.*?(\d+)', sign_html, "未知")

            # 8.2 刷新缓存
            print("🔄 正在刷新积分缓存...")
            credit_log_url = "https://www.right.com.cn/forum/home.php?mod=spacecp&ac=credit&op=log&mobile=2"
            page.get(credit_log_url)
            time.sleep(2)

            # 8.3 获取个人资料
            profile_url = f"https://www.right.com.cn/forum/home.php?mod=space&uid={USER_UID}&do=profile&mycenter=1&mobile=2"
            print(f"📥 正在抓取个人资料页 (UID: {USER_UID[:2]}***{USER_UID[-2:] if len(USER_UID) > 4 else ''})...")
            page.get(profile_url)
            
            total_points = "获取失败"
            contribution = "获取失败"
            enshan_coin = "获取失败"
            
            try:
                time.sleep(5)
                all_lis = page.eles('tag:li')
                for li in all_lis:
                    clean_text = li.text.replace(" ", "").replace("\n", "").replace("\r", "")
                    if not clean_text: continue
                    
                    if ("积分" in clean_text and "今日" not in clean_text) or "Points" in clean_text:
                        match_cn = re.search(r'(\d+)积分', clean_text)
                        match_en = re.search(r'(\d+)Points', clean_text)
                        if match_cn: total_points = match_cn.group(1)
                        elif match_en: total_points = match_en.group(1)

                    if "贡献" in clean_text or "Contributions" in clean_text:
                        match_cn = re.search(r'(\d+)分贡献', clean_text)
                        match_en = re.search(r'(\d+)pointsContributions', clean_text)
                        if match_cn: contribution = match_cn.group(1)
                        elif match_en: contribution = match_en.group(1)

                    if "恩山币" in clean_text or "EnshanCoin" in clean_text:
                        match_cn = re.search(r'(\d+)币恩山币', clean_text)
                        match_en = re.search(r'(\d+)coinsEnshanCoin', clean_text)
                        if match_cn: enshan_coin = match_cn.group(1)
                        elif match_en: enshan_coin = match_en.group(1)
                
                print(f"📊 抓取结果: 积分={total_points}, 贡献={contribution}, 币={enshan_coin}")
                
            except Exception as e:
                print(f"❌ 数据解析异常: {e}")

            # userid脱敏
            try:
                if len(USER_UID) >= 5:
                    notify_user_id = USER_UID[:2] + "***" + USER_UID[len(USER_UID) - 2:]
                else:
                    notify_user_id = "***"
            except Exception as e:
                print(f"❌ UserID脱敏异常: {e}")
                notify_user_id = "获取失败"

            # 8.4 构建推送模版
            notify_content = (
                f"🎉 ===EnShan-Signin-Tool===\n"
                f"✅ 签到成功！🎊\n"
                f"======签到信息=====\n"
                f"账号UID：{notify_user_id} \n"
                f"今日积分：{today_points} \n"
                f"连续签到：{continuous_days} 天 \n"
                f"总签到天数：{total_days} 天 \n"
                f"======积分统计=====\n"
                f"总积分：{total_points} \n"
                f"贡献分：{contribution} 分 \n"
                f"恩山币：{enshan_coin} 币 \n"
                f"=====结束===== \n"
                f"💡By EnShan-Signin-Tool  \n"
            )
            
            print("=== 推送内容预览 ===")
            print(notify_content)
            
            system_notify("恩山签到成功", notify_content)
            
            # 备份Cookie
            final_cookies = get_cookies_safe(page)
            if final_cookies:
                save_cookie_to_file(final_cookies)
            
        else:
            print("❌ 签到失败")
            system_notify("恩山签到失败", f"❌ 恩山签到失败：{sign_msg}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        system_notify("恩山脚本错误", f"恩山脚本运行出错: {str(e)}")
        
    finally:
        try:
            if page: page.quit()
        except:
            pass
        force_kill_chrome()
        # 执行完毕后销毁临时目录
        try:
            shutil.rmtree(rand_dir, ignore_errors=True)
        except:
            pass

if __name__ == "__main__":
    run_sign_in()
