



















###############################################################
#Home page and error pages

@app.route('/')
def homepage():
    """Show homepage, will need to have validation added"""
    return render('home.html')



@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404