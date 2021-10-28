import time
from json import loads as json_loads
from sys import argv as sys_argv
from lxml import etree
from requests import session
import smtplib
from email.mime.text import MIMEText
from captcha_break import DailyFDCaptcha
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')

SUCCESS = False

class Fudan:
    """
    建立与复旦服务器的会话，执行登录/登出操作
    """
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36"

    # 初始化会话
    def __init__(self, uid, psw, url_login='https://uis.fudan.edu.cn/authserver/login'):
        """
        初始化一个session，及登录信息
        :param uid: 学号
        :param psw: 密码
        :param url_login: 登录页，默认服务为空
        """
        self.session = session()
        self.session.headers['User-Agent'] = self.UA
        self.url_login = url_login

        self.uid = uid
        self.psw = psw

    def _page_init(self):
        """
        检查是否能打开登录页面
        :return: 登录页page source
        """
        logging.debug("Initiating...")
        page_login = self.session.get(self.url_login)

        logging.debug("Response code: " + str(page_login.status_code))

        if page_login.status_code == 200:
            logging.debug("Initiated.")
            return page_login.text
        else:
            logging.error("Failed to open the login page.")
            raise Exception("Failed to open the login page.")

    def login(self):
        """
        执行登录
        """
        page_login = self._page_init()

        logging.debug("Parsing the login page...")
        html = etree.HTML(page_login, etree.HTMLParser())

        logging.debug("Getting tokens...")
        data = {
            "username": self.uid,
            "password": self.psw,
            # "service" : "https://zlapp.fudan.edu.cn/site/ncov/fudanDaily"
        }

        # 获取登录页上的令牌
        data.update(
                zip(
                        html.xpath("/html/body/form/input/@name"),
                        html.xpath("/html/body/form/input/@value")
                )
        )

        headers = {
            "Host"      : "uis.fudan.edu.cn",
            "Origin"    : "https://uis.fudan.edu.cn",
            "Referer"   : self.url_login,
            "User-Agent": self.UA
        }

        logging.debug("Logining...")
        post = self.session.post(
                self.url_login,
                data=data,
                headers=headers,
                allow_redirects=False)

        logging.debug("Response code: %d" % post.status_code)

        if post.status_code == 302:
            logging.debug("Login.")
        else:
            logging.error("Failed to login.")
            raise Exception("Failed to login.")

    def logout(self):
        """
        执行登出
        """
        exit_url = 'https://uis.fudan.edu.cn/authserver/logout?service=/authserver/login'
        expire = self.session.get(exit_url).headers.get('Set-Cookie')

        if '01-Jan-1970' in expire:
            logging.debug("Logout.")
        else:
            logging.error("Failed to logout.")
            raise Exception("Failed to logout.")

    def close(self):
        """
        执行登出并关闭会话
        """
        self.logout()
        self.session.close()
        logging.debug("Session closed.")

class Zlapp(Fudan):
    last_info = ''
    status_sfzx = ''

    def check(self):
        """
        检查
        """
        logging.info("Checking...")
        get_info = self.session.get('https://zlapp.fudan.edu.cn/ncov/wap/fudan/get-info')
        last_info = get_info.json()

        logging.info("Last data: %s " % last_info["d"]["info"]["date"])

        position = last_info["d"]["info"]['geo_api_info']
        position = json_loads(position)

        logging.info("Last address: %s" % position['formattedAddress'])

        self.status_sfzx = last_info["d"]["oldInfo"]["sfzx"]
        logging.info("Last status of sfzx: %s" % self.status_sfzx)

        today = time.strftime("%Y%m%d", time.localtime())
        
        global SUCCESS
        if last_info["d"]["info"]["date"] == today:
            logging.info("Already Submitted.")
            SUCCESS = True
        else:
            logging.info("NOT yet submitted.")
            SUCCESS = False
            self.last_info = last_info["d"]["info"]

    def submit(self, captcha: DailyFDCaptcha):
        """
        提交
        """
        headers = {
            "Origin"    : "https://zlapp.fudan.edu.cn",
            "Referer"   : "https://zlapp.fudan.edu.cn/site/ncov/fudanDaily",
            "User-Agent": self.UA
        }

        logging.info("Submitting...")

        geo_api_info = json_loads(self.last_info["geo_api_info"])
        province = geo_api_info["addressComponent"].get("province", "")
        city = geo_api_info["addressComponent"].get("city", "") or province
        district = geo_api_info["addressComponent"].get("district", "")
        if city == province:
            area = " ".join(list((province, district)))
        else:
            area = " ".join(list((province, city, district)))
        self.last_info.update(
                {
                    "tw"      : "13",
                    "province": province,
                    "city"    : city,
                    "area"    : area,
                    "ismoved" : 0
                }
        )

        for i in range(3):
            captcha_text = captcha()
            if not captcha_text:
                continue
            self.last_info.update({
                'sfzx': self.status_sfzx,
                'code': captcha_text
            })
            
            save = self.session.post(
                    'https://zlapp.fudan.edu.cn/ncov/wap/fudan/save',
                    data=self.last_info,
                    headers=headers,
                    allow_redirects=False)

            save_msg = json_loads(save.text)["m"]
            logging.info(save_msg)
            if save_msg != '验证码错误':
                break

def send_mail():
    logging.info('Sending email...')
    mail_sender, mail_psw, mail_receiver = sys_argv[2].strip().split(' ')
    mail_host = 'smtp.yeah.net'

    message = MIMEText('打卡失败', 'plain', 'utf-8')
    message['From'] = mail_sender.split('@')[0] + '<' + mail_sender + '>'
    message['To'] = mail_receiver.split('@')[0] + '<' + mail_receiver + '>'
    message['Subject'] = '平安复旦打卡失败通知'
    
    try:
        smtpObj = smtplib.SMTP() 
        smtpObj.connect(mail_host, 25)    # 25 为 SMTP 端口号
        smtpObj.login(mail_sender, mail_psw)  
        smtpObj.sendmail(mail_sender, mail_receiver, message.as_string())
        logging.info('Email sent.')
    except:
        logging.error('Failed to send email.')

if __name__ == '__main__':
    try:
        uid, psw = sys_argv[1].strip().split(' ')
        captcha_uname, captcha_pwd = sys_argv[3].strip().split(' ')
        daily_fudan = Zlapp(uid, psw)
        daily_fudan.login()
        daily_fudan.check()
        if not SUCCESS:
            captcha = DailyFDCaptcha(captcha_uname, captcha_pwd, daily_fudan)
            daily_fudan.submit(captcha)
            daily_fudan.check()
        daily_fudan.close()
    except:
        logging.exception('打卡失败！')
        SUCCESS = False
    
    if not SUCCESS:
        send_mail()
