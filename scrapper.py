from bs4 import BeautifulSoup as bs
import requests
from urllib.request import urlopen as ureq
from flask import Flask,render_template,request
from pandas import to_datetime
from flask_cors import cross_origin
from numpy import timedelta64
import datetime
#import logging
#import plotly
import pymongo as mg
#import plotly.graph_objects as go
#import json


app=Flask(__name__)

def get_review(commentsbox ,search,flag=True):
    reviews = []
    for comment in commentsbox[:-1]:
        try:
            name = comment.find_all('p', {"class": "_2sc7ZR _2V5EHH"})[0].text
            # print("Name: ",name)
        except:
            name = "No user name found !"

        try:
            if(flag==True):
                rating = comment.div.div.div.div.text[0]

            else:
                rating = comment.div.div.div.div.text

        except:
            rating = 'There is no rating given by this user !'
        try:
            heading = comment.div.div.div.p.text

        except:
            heading = 'No Heading found for this review !'

        try:
            comment_body = comment.find_all('div', {"class": 't-ZTKy'})[0].text
            if(comment_body.endswith('READ MORE')):
                comment_body=comment_body[:comment_body.find('READ MORE')]
            else:
                comment_body=comment_body

        except:
            comment_body = "No comments given by user !"

        """To get the date since user using this device !"""
        try:
            dt=comment.find_all('p', {'class': "_2sc7ZR"})[1].text
            # print(dt)
            if("months" in dt):
                using_since = int(dt[:dt.find('months')])
                # print(using_since)
            else:
                dt=to_datetime(dt)
                today = to_datetime(datetime.datetime.today().strftime('%Y-%m-%d'))
                using_since=int((today-dt)/timedelta64(1,'M'))

                # print(using_since)

            # print(using_since)
            # buyed_on = comment.find_all('p', {'class': "_2sc7ZR"})[1].text
            # print(buyed_on)

        except:
            using_since = "No information present !"

        my_dict = {"Product": search, "Name": name, "Rating": rating, "CommentHead": heading, "Comment": comment_body,'Using Since':str(using_since)+" months"}

        reviews.append(my_dict)
    return(reviews)

@cross_origin()
@app.route("/",methods=["GET","POST"])
def homepage():
    return render_template('index.html')



@app.route("/about",methods=["GET","POST"])
def about():
    return render_template('about.html')

@app.route('/scrap', methods=["GET","POST"])
def scrap():
    if request.method == "POST":
        search = request.form["search_content"].replace(' ', '')
        #DBlogger.debug('Requeest Recieved for {}'.format(search))
        try:
            url = "https://www.flipkart.com/search?q=" + search
            uclient = ureq(url)
            # print(uclient)
            flipkartpage = uclient.read()
            uclient.close()
            flipkart_html = bs(flipkartpage, 'html.parser')
            # print(flipkart_html)
            # _2pi5LC col-12-12 this class has been change with recent one _1AtVbE col-12-12
            bigbox = flipkart_html.findAll('div', {'class': '_1AtVbE col-12-12'})
            # print('bigbox',bigbox)
            del bigbox[0:3]
            box = bigbox[0]
            product_highlights = []
            product_detail = []

            # print(product_highlights)
            product_link = "https://www.flipkart.com" + box.div.div.div.a['href']
            # print(product_link)
            product_open_page = requests.get(product_link)
            product_html = bs(product_open_page.text, 'html.parser')
            #product_highlights.append(get_product_highlights(product_html))
            # try:
            #     rating = product_html.find_all('div', {"class": "_1uJVNT"})
            #     rating_list = []
            #     for i in range(len(rating)):
            #         # print(type(rating[i].text))
            #         rating_list.append(int(rating[i].text.replace(',', '')))
            #     pie_chart = get_pie_chart(rating_list)
            #     DBlogger.debug('Got Pie chart for {}'.format(search))
            #
            # except Exception as e:
            #     DBlogger.exception(e)
            #     # DBlogger.error(e)
            #     print(e)
            # product_detail.extend(get_product_info(product_html, search, product_link))

            reviews = []
            """Conncecting with DataBase"""
            try:
                db_connetion = mg.MongoClient(
                    "mongodb+srv://AbhishekMestry:unlock24708651@cluster0.iofre.mongodb.net/myFirstDatabase?retryWrites=true&w=majority")
                # print(db_connetion.test)
                # DBlogger.debug('Successfully Connected with MongoDB !')

            except Exception as e:
                # DBlogger.exception(e)
                print(e)
            try:
                db = db_connetion['Flask_Scrapper']
                check = db[search].find({})

                if (check.count() > 0):
                    reviews = list(check)

                    #DBlogger.debug('Found Collection in Database {}'.format(search))
                    return render_template('results.html', reviews=reviews,
                                           total_reviews_=len(reviews))
                else:

                    # To get the total reviews of the product
                    try:
                        total_reviews = int(
                            product_html.find_all('div', {'class': "_3UAT2v _16PBlm"})[0].text.replace('All',
                                                                                                       '').replace(
                                'reviews', ''))
                        next_link = product_html.find("div", {"class": "_3UAT2v _16PBlm"})

                    except:
                        # print(e)
                        total_reviews = int(
                            product_html.find_all('div', {'class': "_3UAT2v _33R3aa"})[0].text.replace('All',
                                                                                                       '').replace(
                                'reviews', ''))
                        next_link = product_html.find("div", {"class": "_3UAT2v _33R3aa"})

                    # To get the next review page and to get generating url for the review
                    if (total_reviews > 10):

                        """ To get the next review link"""

                        next_link = next_link.find_parent().attrs['href']
                        # next_link="#"
                        next_review_link = "https://www.flipkart.com" + next_link

                        next_review_page = requests.get(next_review_link)
                        next_page_html = bs(next_review_page.text, 'html.parser')
                        """To find out how many total review pages are there for perticular product"""

                        mx = next_page_html.find_all('div', {'class': '_2MImiq _1Qnn1K'})
                        for i in range(len(mx)):
                            """To get max number of reviews pages """
                            temp_max_reviews = mx[i].span.text
                            """To get the generating link of reviews"""
                            generating_link = mx[i].a['href']

                            # This link will be used to get all liks of the another pages of reviews

                            generating_link = generating_link[:-1]
                            # print(generating_link)
                        """To get the maximum pages of the reviews that are available"""
                        max_reviews = temp_max_reviews[temp_max_reviews.find('of') + 2:]
                        max_reviews = int(max_reviews.replace(',', ''))
                        # print(max_reviews)

                    else:
                        commentsbox = product_html.find_all('div', {"class": "_16PBlm"})

                    # To check the count of the reveiws

                    try:

                        if (len(reviews) < 501 and total_reviews > 10):
                            for i in range(1, max_reviews + 1):
                                if (len(reviews) >= 500):
                                    break

                                else:
                                    # Iterating over Review pages to find the url of reviews of perticular product

                                    next_review_generating_link = "https://www.flipkart.com" + generating_link + str(i)
                                    # print(next_review_generating_link)
                                    """Here we are going with one by one link with the help of generating link !"""
                                    temp_review_page = requests.get(next_review_generating_link)
                                    temp_review_page_html = bs(temp_review_page.text, 'html.parser')
                                    temp_comment_box = temp_review_page_html.find_all('div',
                                                                                      {'class': '_1AtVbE col-12-12'})
                                    """Passing this review page to function which will scrap the reviews """
                                    temp_reveiew_list = get_review(temp_comment_box, search)
                                    temp_reveiew_list = temp_reveiew_list[3:]
                                    # if(temp_reveiew_list[0].get('Name')=="No user name found !"):
                                    #     # print(temp_reveiew_list)
                                    #     temp_reveiew_list=temp_reveiew_list[1:]
                                    reviews.extend(temp_reveiew_list)

                        elif (len(reviews) < 501 and total_reviews < 10):
                            """If we have less than 10 reviews then just passing that page to review"""
                            temp_reveiew_list = get_review(commentsbox, search, flag=False)
                            reviews.extend(temp_reveiew_list)
                            # print(len(reviews))
                        #DBlogger.debug('Reviews for {} are {}'.format(search, len(reviews)))

                        """To Insert The Data Into Database"""
                        try:
                            col_name = db[search]
                            #DBlogger.info('New collection Created as {}'.format(col_name))
                            if (len(reviews) > 501):
                                reviews = reviews[:500]

                            if (len(reviews) == 0):
                                my_dict = {"Product": search, "Name": "-", "Rating": "-", "CommentHead": "-",
                                           "Comment": "No Reviews Available for this product", 'Using Since': "-"}

                                reviews.append(my_dict)

                            col_name.insert_many(reviews)
                            #DBlogger.debug("{} Added To {} Collection".format(len(reviews), col_name))
                            return render_template('results.html',  reviews=reviews,
                                                   total_reviews_=len(reviews))


                        except Exception as e:
                            #DBlogger.exception(e)
                            print(e)

                    except Exception as e:
                        #DBlogger.exception(e)
                        print(e)

            except Exception as e:
                #DBlogger.exception(e)
                print(e)


        except Exception as e:
            #logging.debug(e)
            print(e)
            return ("<h1>Something Went Wrong ! We'll Fix Issue Soon And We'll Be Back</h1>")


if __name__ == "__main__":
    app.run(debug=True)
