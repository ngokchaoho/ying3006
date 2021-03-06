from flask import Flask, render_template, request, url_for, session, escape, redirect, jsonify
import my_db as db
import latent

# import sys
# reload(sys)
# sys.setdefaultencoding('utf8')
import io

app = Flask(__name__)
@app.route('/')
def index():
    if 'user' in session:
        # use predicted stock ids to grab stock news
        user_portfolio = get_user_portfolio(session['user']['id'])
        user_suggestion = get_user_suggestion()
        result = []
        user_holding_news = []
        for i in xrange(5):
            for code in user_portfolio:
                result += [db.news[code][i]]
                user_holding_news += [db.news[code][i]]
            for suggestion in user_suggestion:
                result += [db.news[suggestion][i]]
        return render_template('news_feed.html', user=session['user'], news=result, other_news=db.news, user_holding_news=user_holding_news)
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        session['user'] = db.users[username]
        prediction = model.predict(session['user']['id'])
        session['prediction_indexes'] = prediction.columns.values.tolist()
        session['prediction_values'] = prediction.values.tolist()[0]
        print 'Initial prediction: ', session['prediction_indexes']
        return redirect(url_for('index'))
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    # session.pop('user', None)
    session.clear()
    return redirect(url_for('index'))

@app.route('/portfolio', methods=['GET'])
def portfolio():
    # return JSON: user's portfolio list, suggested top 5
    prediction = model.predict(session['user']['id'])
    session['prediction_indexes'] = prediction.columns.values.tolist()
    session['prediction_values'] = prediction.values.tolist()[0]
    user_portfolio = get_user_portfolio(session['user']['id'])
    user_suggestion = get_user_suggestion()
    return render_template('portfolio.html', user=session['user'], name=session['user']['username'], portfolios=user_portfolio, suggestions=user_suggestion)

@app.route('/transaction', methods=['POST'])
def transaction():
    action = request.form['action']
    if(action == 'buy'):
        return buy()
    elif(action == 'sell'):
        return sell()
    else:
        return 'action not defined'

def buy():
    code = request.form['code']
    code = convert_into_valid_code(code)
    share = request.form['share']
    model.update_user_by_code(session['user']['id'], code, float(share))
    model.update()
    print '>>>>>>>> model.R: <<<<<<<<'
    print model.R
    print model.approximate_df
    prediction = model.predict(session['user']['id'])
    session['prediction_indexes'] = prediction.columns.values.tolist()
    session['prediction_values'] = prediction.values.tolist()[0]
    print 'New prediction: ', session['prediction_indexes']
    return redirect(url_for('portfolio'))

def sell():
    code = request.form['code']
    code = convert_into_valid_code(code)
    share = request.form['share']
    model.update_user_by_code(session['user']['id'], code, -float(share))
    model.update()
    print '>>>>>>>> model.R: <<<<<<<<'
    print model.R
    print model.approximate_df
    prediction = model.predict(session['user']['id'])
    session['prediction_indexes'] = prediction.columns.values.tolist()
    session['prediction_values'] = prediction.values.tolist()[0]
    print 'New prediction: ', session['prediction_indexes']
    return redirect(url_for('portfolio'))

def get_user_portfolio(userid):
    user_row = model.R[userid]
    user_portfolio_index = []
    for i in xrange(len(user_row)): # filter out stocks that did not buy
        if user_row[i] >= 0.01:
            user_portfolio_index += [i]
    user_portfolio = {}
    for index in user_portfolio_index:
        stock_code = codes[index]
        stock_name = names[index]
        stock_price = prices[index]
        stock_percentage_change = float(percentage_changes[index])
        value_bought = user_row[index]
        user_portfolio[stock_code] = {'name':stock_name,'price':stock_price,'percentage_change':stock_percentage_change,'value_bought':value_bought}
    return user_portfolio

# set the secret key.  keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

def get_user_suggestion():
    user_suggestion = {}
    for index in session['prediction_indexes']:
        stock_code = codes[index]
        stock_name = names[index]
        stock_price = prices[index]
        stock_percentage_change = float(percentage_changes[index])
        user_suggestion[stock_code] = {'name':stock_name,'price':stock_price,'percentage_change':stock_percentage_change}
    return user_suggestion

def convert_into_valid_code(code):
    num_of_zero_padding = 4-len(code)
    return '0'*num_of_zero_padding+code

if __name__ == "__main__":
    model = latent.LatentFactorModel()
    f = io.open('./stock_info.txt','r', encoding='utf8')
    codes = map(lambda x: x[0:4], f.readline().strip().split('\t'))
    names = f.readline().strip().split('\t')
    prices = f.readline().strip().split('\t')
    percentage_changes = f.readline().strip().split('\t')
    f.close()
    app.run()
