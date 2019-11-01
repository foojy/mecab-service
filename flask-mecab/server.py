#!/bin/python3
from flask import Flask, abort, jsonify, request
from flask_cors import CORS

import MeCab
import os

app = Flask(__name__)
cors = CORS(app, resources={r"/mecab/*": {"origins": "*"}})

messages = ['Success', 'Faild']


@app.route('/mecab/v1/parse-ipadic', methods=['POST'])
def parse_ipadic():
    sdict = 'ipadic'
    return parse(sdict)

@app.route('/mecab/v1/parse-neologd', methods=['POST'])
def parse_neologd():
    sdict = 'neologd'
    return parse(sdict)

def parse(sdict):
    if not (request.json and 'sentence' in request.json):
        abort(400)
    sentence = request.json['sentence']

    udicts = []
    if request.json and 'udicts' in request.json:
        udicts = request.json['udicts']

    results = mecab_parse(sentence, sdict, udicts)
    return mecab_response(200, messages[0], results, sdict, udicts)

@app.errorhandler(400)
def error400(error):
    return mecab_response(400, messages[1], None, None, [])


def mecab_response(status, message, results, sdict, udicts):
    return jsonify({'status': status, 'message': message, 'results': results, 'sdict': sdict, 'udicts': udicts}), status


def mecab_parse(sentence, sdic='ipadic', udicts=[]):
    repstr = '****'
    sentence = sentence.replace(' ', repstr) #半角スペースを一旦****に変換する
    dic_dir = "/usr/local/lib/mecab/dic/"
    if sdic == 'neologd':
        dic_name = 'mecab-ipadic-neologd'
    else:
        dic_name = sdic
    tagger_str = '-d ' + dic_dir + dic_name

    for udict in udicts:
        udict_path = dic_dir + 'user/' + udict + '.dic'
        if udict is not None and os.path.exists(udict_path):
            tagger_str += ' -u ' + udict_path
    m = MeCab.Tagger(tagger_str)

    # 出力フォーマット（デフォルト）
    format = ['表層形', '品詞', '品詞細分類1', '品詞細分類2', '品詞細分類3', '活用形', '活用型','原型','読み','発音']
    ret = [dict(zip(format, (lambda x: [x[0]]+x[1].split(','))(p.split('\t')))) for p in m.parse(sentence).split('\n')[:-2]]
    #半角スペースを****に置き換えたものを半角スペースに戻す
    for i in range(len(ret)):
        for k, v in ret[i].items():
            if k == '表層形' and v == repstr:
                ret[i]['表層形'] = ' '
                ret[i]['原型'] = ' '
                ret[i]['品詞'] = '記号'
                ret[i]['品詞細分類1'] = '空白'
                ret[i]['読み'] = ' '
                ret[i]['発音'] = ' '
                break
    return ret

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
