import sys
import os
import requests

url = "http://192.168.1.111:8080/add"
if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
    for line in open(sys.argv[1], 'r'):
        book, chapter, wline = line.split(" | ")
        words = {'book': book, 'chapter': chapter, 'words': wline.strip().split(" ") }
        print(words)
        x = requests.post(url, json = words)
        print(x.text)

