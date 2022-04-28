from market import app

#Checks if the app.py file has executed directly and not imported
if __name__ == "__main__":
  app.run(debug=True)





#DYnamic routes
# @app.route("/about/<username>")
# def about_page_user(username):
#     return f"<h1>About Page of {username} </h1>"