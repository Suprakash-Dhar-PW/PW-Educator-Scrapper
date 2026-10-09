import requests

def test():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    data = {"q": "linkedin IIT-JEE Physics Kota"}
    res = requests.post("https://lite.duckduckgo.com/lite/", headers=headers, data=data)
    
    with open("ddg_dump.html", "w", encoding="utf-8") as f:
        f.write(res.text)
        
    print("Dumped!")

test()
