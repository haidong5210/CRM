import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr

msg = MIMEText('傻子吧！', 'plain', 'utf-8')  # 发送内容
msg['From'] = formataddr(["haidong", 'nhd104586@126.com'])  # 发件人
msg['To'] = formataddr(["ali", '2981405421@qq.com'])  # 收件人
msg['Subject'] = "【请回复】测试"  # 主题

server = smtplib.SMTP("smtp.126.com", 25) # SMTP服务
server.login("nhd104586@126.com", "daohaogou213") # 邮箱用户名和密码
server.sendmail('nhd104586@126.com', ['2981405421@qq.com', ], msg.as_string()) # 发送者和接收者
server.quit()
