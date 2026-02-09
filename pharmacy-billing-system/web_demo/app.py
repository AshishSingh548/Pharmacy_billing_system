from flask import Flask, render_template, request, redirect

app = Flask(__name__)

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["name"] == "admin" and request.form["password"] == "123":
            return redirect("/bill")
    return render_template("login.html")


@app.route("/bill", methods=["GET","POST"])
def bill():
    result = None

    if request.method == "POST":
        name = request.form["medicine"]
        qty = int(request.form["qty"])

        fake_prices = {
            "paracetamol":10,
            "crocin":15,
            "dolo":20
        }

        if name.lower() in fake_prices:
            rate = fake_prices[name.lower()]
            amount = rate * qty
            result = (name,rate,qty,amount)

    return render_template("billing.html", result=result)


app.run(host="0.0.0.0",port=10000)
