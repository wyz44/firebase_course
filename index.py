import requests
from bs4 import BeautifulSoup

import firebase_admin
from firebase_admin import credentials, firestore
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

from flask import Flask, render_template, request, make_response, jsonify
from datetime import datetime,timezone,timedelta
app = Flask(__name__)


@app.route("/")
def index():
    homepage = "<h1>汪奕幟Python網頁</h1>"
    homepage += "<br><a href=/course>選修課程查詢</a><br>"
    homepage += "<br><a href=/movie_update>讀取開眼電影即將上映影片，寫入Firestore</a><br>"
    homepage += "<br><a href=/search>電影查詢</a><br>"
    return homepage



@app.route("/course", methods=["GET", "POST"])
def search_course():
    if request.method == "POST":
        cond = request.form["keyword"]
        result = "請輸入您要查詢的課程關鍵字：" + cond

        db = firestore.client()
        collection_ref = db.collection("111")
        docs = collection_ref.get()
        result = ""
        for doc in docs:
            dict = doc.to_dict()
            if cond in dict["Course"]:
                #print("{}老師開的{}課程,每週{}於{}上課".format(dict["Leacture"], dict["Course"],  dict["Time"],dict["Room"]))
                result += dict["Leacture"] + "老師開的" + dict["Course"] + "課程,每週"
                result += dict["Time"] + "於" + dict["Room"] + "上課<br>"
        # print(result)
        if result == "":
            result = "sorry....."
        return result
    else:
        return render_template("course.html")


@app.route("/movie_update")
def movie():
    url = "http://www.atmovies.com.tw/movie/next/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    result=sp.select(".filmListAllX li")
    lastUpdate = sp.find("div", class_="smaller09").text[5:]

    for item in result:
        picture = item.find("img").get("src").replace(" ", "")
        title = item.find("div", class_="filmtitle").text
        movie_id = item.find("div", class_="filmtitle").find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw" + item.find("div", class_="filmtitle").find("a").get("href")
        show = item.find("div", class_="runtime").text.replace("上映日期：", "")
        show = show.replace("片長：", "")
        show = show.replace("分", "")
        showDate = show[0:10]
        showLength = show[13:]

        rate = None
        if(item.find("div", class_="runtime").img != None):
            rate = item.find("div", class_="runtime").find("img").get("src")
        
        if rate == "/images/cer_G.gif":
            rate = "普遍級(一般觀眾皆可觀賞)"
        elif rate == "/images/cer_P.gif":
            rate = "保護級(未滿六歲之兒童不得觀賞，六歲以上未滿十二歲之兒童須父母、師長或成年親友陪伴輔導觀賞)"
        elif rate == "/images/cer_F2.gif":
            rate = "輔導級(未滿十二歲之兒童不得觀賞)"
        elif rate == "/images/cer_F5.gif":
            rate = "輔導級(未滿十五歲之人不得觀賞)"
        elif rate == "/images/cer_R.gif":
            rate = "限制級(未滿十八歲之人不得觀賞)"
        else:
            rate = "尚無電影分級資訊"
        
        doc = {
            "title": title,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": showLength,
            "lastUpdate": lastUpdate,
            "rate":rate
         }

        doc_ref = db.collection("movies_crawler").document(movie_id)
        doc_ref.set(doc)
        # print(title)
    return "近期上映電影已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate 



@app.route("/search", methods=["POST","GET"])
def search_movies():
    if request.method == "POST":
        MovieTitle = request.form["MovieTitle"]

        info = ""     
        collection_ref = db.collection("movies_crawler")
        #docs = collection_ref.where("title","==", "喜悅：達賴喇嘛遇見屠圖主教").get()
        docs = collection_ref.order_by("showDate").get()
        for doc in docs:
            if MovieTitle in doc.to_dict()["title"]: 
                info += "片名：" + "<a href=" + doc.to_dict()["hyperlink"] + " target=_blank>" + doc.to_dict()["title"] + "</a>" + "<br>" 
                info += "<img src=" + doc.to_dict()["picture"] + "></img>" + "<br>"
                info += "片長：" + doc.to_dict()["showLength"] + " 分鐘<br>" 
                info += "上映日期：" + doc.to_dict()["showDate"] + "<br>"
                info += "電影分級：" + doc.to_dict()["rate"] + "<br><br>"
        if info == "":
            info = "抱歉，查無相關電影資訊"
        return info
    else:  
        return render_template("movies.html")


# @app.route("/webhook", methods=["POST"])      #網頁介面尚未建立
# def webhook():
#     # build a request object
#     req = request.get_json(force=True)
#     # fetch queryResult from json
#     action =  req.get("queryResult").get("action")             #可替換為 action =  req["queryResult"]["action"]
#     # msg =  req.get("queryResult").get("queryText")             #可替換為 msg =  req["queryResult"]["queryText"]
#     # info = "動作：" + action + "； 查詢內容：" + msg

#     if (action == "rateChoice"):
#         rate =  req.get("queryResult").get("parameters").get("rate")
#         if (rate == "輔12級"):
#             rate = "輔導級(未滿十二歲之兒童不得觀賞)"
#         elif (rate == "輔15級"):
#             rate = "輔導級(未滿十五歲之人不得觀賞)"
#         info = "您選擇的電影分級是：" + rate + "，相關電影：\n"

#         collection_ref = db.collection("movies_crawler")
#         docs = collection_ref.get()
#         result = ""
#         for doc in docs:
#             dict = doc.to_dict()
#             if rate in dict["rate"]:
#                 result += "片名：" + dict["title"] + "\n"
#                 result += "介紹：" + dict["hyperlink"] + "\n\n"
#         info += result

#     return make_response(jsonify({"fulfillmentText": info}))


if __name__ == "__main__":
    app.run()