from difflib import SequenceMatcher
import numpy as np
import pymongo
from datetime import datetime
from flask import Flask, render_template, jsonify
import json

from pandas import *
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["briqb"]
mycol = mydb["quotes"]

xls = ExcelFile('Assignment Dataset .xlsx')
data = xls.parse(xls.sheet_names[0])
quotes = []
quotes.append(data.to_dict('records'))
mycol.insert_many(data.to_dict('records'))

app = Flask(__name__)


def check_float(potential_float):
    if str(potential_float) != 'nan':
        try:
            float(potential_float)

            return True
        except ValueError:
            return False
    else:
        return False


@app.route('/rated')
def Rated_quotes():
    mydb = myclient["briqb"]
    mycol = mydb["quotes"]
    not_null = []
    for m in mycol.find():
        if check_float(str(m['rating'])):
            not_null.append(m['quotes'])
    val = {"data1": not_null}
    print(val['data1'])
    rsp = {"status": 0, "data": str(val)}
    return jsonify(rsp)


# for null rated quotes

@app.route('/unrated')
def unrated_quotes():
    unrated_quote = []
    for m in mycol.find():
        if not check_float(str(m['rating'])):
            unrated_quote.append(m['quotes'])
    unrated = {'unrated_qoutes': unrated_quote}
    return jsonify(unrated)


# GET RELATED QUOTE - returns the related unrated quote from the
# unrated quotelist which has matching words from the recommended quotes
# table


@app.route('/get-all')
def get_all_quotes():
    mydb = myclient["briqb"]

    mycol = mydb["quotes"]
    # get all quotes
    all_quotes = []
    for m in mycol.find():
        all_quotes.append(m['quotes'])
    all_qutoes_found = {'all_quotes': all_quotes}
    return jsonify(all_qutoes_found)


@app.route('/add-quote')
def add_quote():

    mydict = {'id': '5a6ce86e2af929789500e7e4', 'quotes': 'Computer Science is no more about computers than astronomy is about telescopes.',
              'author': 'Linu Jose', 'source': 'medium', 'rating': 3.5, 'addedBy': '5ab04d928c8b4e3cbf733557'}

    mycol.insert_one(mydict)

    dumps = json.dumps(mydict, default=str)
    return dumps


@app.route('/delete-quote')
def delete_quote():
    # delete query
    myquery = {'id': '5a6ce86e2af929789500e7e4'}
    qurey_to_be_deleted = {'deleted_quote': mycol.find_one(myquery)}
    mycol.delete_one(myquery)
    dumps = json.dumps(qurey_to_be_deleted, default=str)
    return dumps


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


@app.route('/rec-quotes')
def recommended_quotes():
    recm_qute = []
    for m in mycol.find():
        if m['rating'] > 3.0:
            recm_qute.append(
                {"id": m['_id'], 'quotes': m['quotes'], 'ratings': m['rating']})
    recommends_col = mydb["recommended-quotes"]
    recommends_col.insert_many(recm_qute)
    recs = {'recommended_quotes': recm_qute}
    dumps = json.dumps(recs, default=str)
    return dumps


@app.route('/similar-quotes')
def similar_quote():
    for m in mycol.find():
        if not check_float(str(m['rating'])):
            unrated_quote = m['quotes']

    recm_qute = []
    for m in mycol.find():
        if m['rating'] > 3.0:
            recm_qute.append({"id": m['_id'], 'quotes': m['quotes']})

    li_com = []
    for rq in recm_qute:
        #     print(rq['quotes'])
        li_com.append((similar(rq['quotes'], unrated_quote), rq['quotes']))
    quote_found = li_com[np.argmax(list(map(lambda x: x[0], li_com)))]

    similar_quote_found = {'quote_found': quote_found}

    return jsonify(similar_quote_found)


@app.route('/update')
def Rate_or_UpdateQuote():
    myquery = {'id': '5a6ce86e2af929789500e7e4'}
    old_vals = mycol.find_one(myquery)
    newvalues = {"$set": {"rating": 5.0}}
    mycol.update_one(myquery, newvalues)
    updated_q = {"Old_values":
                 old_vals, "Updated_values": mycol.find_one(myquery)}
    dumps = json.dumps(updated_q, default=str)
    return dumps


@app.route('/disliked')
def Below_Three_or_Disliked():
    disliked_qute = []
    for m in mycol.find():
        if m['rating'] < 3.0:
            disliked_qute.append(
                {"id": m['_id'], 'quotes': m['quotes'], 'ratings': m['rating']})
    dis = {'recommended_quotes': disliked_qute}
    dumps = json.dumps(dis, default=str)
    return dumps


if __name__ == '__main__':
    app.run(debug=True)
