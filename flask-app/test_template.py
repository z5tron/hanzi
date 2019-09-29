from jinja2 import Template

template = Template(open('templates/print_words.tex', 'r').read())
words='食 无 名 加 共 事 帮 饿 肚 狮 觉 毛 求 等 香 肉 听 水'
print(template.render(title='中文', date='2019-09-29', words=words.split()))
