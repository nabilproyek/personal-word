import os
from os.path import join, dirname
from dotenv import load_dotenv

from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient
import requests
from datetime import datetime
from bson import ObjectId

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URL = os.environ.get("MONGODB_URL")
DB_NAME = os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URL)

db = client[DB_NAME]

app = Flask(__name__)

@app.route('/')
def main():
    words_result = db.words.find({}, {'_id': False})
    words = []
    for word in words_result:
        definition = word['definitions'][0]['shortdef']
        definition = definition if type(definition) is str else definition[0]
        words.append({
            'word': word['word'],
            'definition': definition,
        })
    msg = request.args.get('msg')
    return render_template(
        'index.html',
        words=words,
        msg=msg
    )

@app.route('/detail/<keyword>')
def detail(keyword):
    api_key = '0137d445-d2db-418f-b1d3-a9f1f357de30'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    definitions = response.json()
    if not definitions:
        return redirect(url_for('error', keyword=keyword))  

    if type(definitions[0]) is str:
        return redirect(url_for('error', keyword=keyword, suggestions=definitions))

    status = request.args.get('status_give', 'new')
    return render_template(
        'detail.html',
        word=keyword,
        definitions=definitions,
        status=status
    )

@app.route('/api/save_word', methods=['POST'])
def save_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')
    doc = {
        'word': word,
        'definitions': definitions,
        'date': datetime.now().strftime('%Y-%m-%d')
    }
    db.words.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg': f'the word, {word}, was saved!!!',
    })

@app.route('/api/delete_word', methods=['POST'])
def delete_word():
    word = request.form.get('word_give')
    db.words.delete_one({'word': word})
    db.examples.delete_many({'word': word})
    return jsonify({
        'result': 'success',
        'msg': f'the example for the word, {word} was deleted'
    })

@app.route('/error/<keyword>')
def error(keyword):
    api_key = '0137d445-d2db-418f-b1d3-a9f1f357de30'
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    suggestions = response.json()
    if not suggestions:
        return render_template('error.html', keyword=keyword, suggestions=None)
    if type(suggestions[0]) is str:
        return render_template('error.html', keyword=keyword, suggestions=suggestions)
    return render_template('error.html', keyword=keyword, suggestions=None)

@app.route('/api/get_exs', methods=['GET'])
def get_exs():
    word = request.args.get('word')
    examples_data = db.examples.find({'word': word})
    examples = []
    for example in examples_data:
        examples.append({
            'example': example.get('example'),
            'id': str(example.get('_id'))
        })
    return jsonify({'result': 'success', 'examples': examples})

@app.route('/api/save_ex', methods=['POST'])
def save_ex():
    word = request.form.get('word')
    example = request.form.get('example')
    doc = {
        'word': word,
        'example': example
    }

    db.examples.insert_one(doc)
    return jsonify({'result': 'success', 'msg': f'Your examples, {example}, for the word, {word}, was saved!'})

@app.route('/api/delete_ex', methods=['POST'])
def delete_ex():
    id = request.form.get('id')
    word = request.form.get('word')
    db.examples.delete_one({'_id': ObjectId(id)})
    return jsonify({'result': 'success', 'msg': f'Your word, {word}, was deleted!'})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)