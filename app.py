from flask import Flask,jsonify
import numpy as np
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

# set-up DB connection

engine = create_engine("sqlite:///hawaii.sqlite",connect_args={'check_same_thread':False})
Base = automap_base()
Base.prepare(engine, reflect=True)

#build table classes

Measurement = Base.classes.measurement
Station = Base.classes.station

#initiate db session

session = Session(engine,autoflush=True)

#date check routines
def monthcheck(month):
        if month > 0 and month <= 12:
            return True
        else:
            return False

def daycheck(month,day):
    monthlist1 = [1,3,5,7,8,10,12]
    monthlist2 = [4,6,9,11]
    monthlist3 = 2 

    for mon in monthlist1:
        if month == mon:
            if day >=1 and day <= 31:
                return True
            else:
                return False

    for mon in monthlist2:
        if month == mon:
            if day >= 1 and day <= 30:
                return True
            else:
                return False

    if month == monthlist3:
        if day >=1 and day <= 29:
            return True
        else:
            return False

def yearcheck(year):
    if len(year) >= 1 and len(year) <= 4:
        return True
    else:
        return False

# check if date(s) are valid
def check_date(*argv):
    rec = session.query(Measurement.date).order_by(Measurement.date).all()
    s = int(rec[0][0].replace("-",""))
    e = int(rec[-1][0].replace("-",""))
    if (len(argv) == 1):
        #check that the input is a valid number
        if (isinstance(int(argv[0].replace("-","")),int)):
            us = int(argv[0].replace("-",""))
        else:
            return False
        
        #check that the date is valid
        chk = argv[0].split("-")
        if ( not (yearcheck(chk[0]) and monthcheck(int(chk[1])) and daycheck(int(chk[1]),int(chk[2])))):
            return False
        
        #check if date is within collected dates of data
        if ((us >= s) and (us <= e)):
            return True
        else:
            return False
    elif (len(argv) == 2):
        #check that start and end dates are valid numbers
        if (isinstance(int(argv[0].replace("-","")),int)):
            us = int(argv[0].replace("-",""))
        else:
            return False
        if (isinstance(int(argv[1].replace("-","")),int)):
            ue = int(argv[1].replace("-",""))
        else:
            return False
        
        #check that the dates are valid
        chk = argv[0].split("-")
        chk1 = argv[1].split("-")
        if (not (yearcheck(chk[0])) and (monthcheck(int(chk[1]))) and (daycheck(int(chk[1]),int(chk[2])))):
            return False
        if (not (yearcheck(chk1[0])) and (monthcheck(int(chk1[1]))) and (daycheck(int(chk1[1]),int(chk1[2])))):
            return False
        
        #check that start and end dates are within the data set
        if (((us >= s) and (us <= e)) and ((ue >= s) and (ue <= e))):
            #check that end date is greater than start date
            if (ue > us):
                return True
            else:
                return False
        else:
            return False
    else:
        return False

app = Flask(__name__)

@app.route('/')
def index():
    rec = session.query(Measurement.date).order_by(Measurement.date).all()
    return (
        f"Available Routes:</br>"
        f"/api/v1.0/precipitation</br>"
        f"<p style=\"text-indent: 40px\">*Returns all precipiattion data</p>"
        f"/api/v1.0/stations</br>"
        f"<p style=\"text-indent: 40px\">*Returns list of all weather monitoring stations</p>"
        f"/api/v1.0/tobs</br>"
        f"<p style=\"text-indent: 40px\">*Returns temperature data for the last year of available data</p>"
        f"/api/v1.0/&ltstart&gt</br>"
        f"<p style=\"text-indent: 40px\">*Returns temperature min/avg/max from given start date to the end of collected data</p>"
        f"<p style=\"text-indent: 40px\">*Valid dates are between " +  rec[0][0] + " and " + rec[-1][0] + "</p>"
        f"<p style=\"text-indent: 40px\">*Usage:</p>"
        f"<p style=\"text-indent: 60px\">/api/v1.0/\"some start date\" i.e. /api/v1.0/2016-02-05</p>"
        f"/api/v1.0/&ltstart&gt/&ltend&gt</br>"
        f"<p style=\"text-indent: 40px\">*Returns temperature data between given start and end dates</p>"
        f"<p style=\"text-indent: 40px\">*Valid dates are between " +  rec[0][0] + " and " + rec[-1][0] + "</p>"
        f"<p style=\"text-indent: 40px\">*Usage:</p>"
        f"<p style=\"text-indent: 60px\">/api/v1.0/\"some start date\"/\"some end date\" i.e. /api/v1.0/2016-05-01/2016-05-13</p>"
        )

@app.route('/api/v1.0/precipitation')
def prec():
    res = session.query(Measurement.date,Measurement.prcp).order_by(Measurement.date).all()
    all_prec=[]
    for i in res:
        dat = {i[0]:i[1]}
        all_prec.append(dat)
    return jsonify(all_prec)

@app.route('/api/v1.0/stations')
def stations():
    res = session.query(Station.station,Station.name).all()
    all_stat=[]
    for i in res:
        dat = {i[0]:i[1]}
        all_stat.append(dat)
    return jsonify(all_stat)

@app.route('/api/v1.0/tobs')
def tobs():
    l_rec = session.query(Measurement.date).order_by(Measurement.date).all()
    end_date = l_rec[-1][0]
    g = end_date.split("-")
    start_date = (str(int(g[0]) -1) + "-" + g[1] + "-" + g[2])

    res = session.query(Measurement.tobs,Measurement.date).filter(Measurement.date >= start_date).filter(Measurement.date <= end_date).order_by(Measurement.date).all()
    all_temp = []
    for i in res:
        dat = {i[1]:i[0]}
        all_temp.append(dat)
    return jsonify(all_temp)
        
@app.route('/api/v1.0/<start>')
def one(start):
    if (check_date(start)):
        sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
        res = session.query(*sel).filter(Measurement.date >= start).all()
        m = list(res[0])
        dat = {'min_temp':m[0],
               'avg_temp':m[1],
               'max_temp':m[2]}
        return jsonify(dat)
    else:
        return "Invalid start date!"

@app.route('/api/v1.0/<start>/<end>')
def two(start,end):
    if (check_date(start,end)):
        sel1 = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]
        res = session.query(*sel1).filter(Measurement.date >= start).filter(Measurement.date <= end).all()
        m = list(res[0])
        dat = {'min_temp':m[0],
               'avg_temp':m[1],
               'max_temp':m[2]}
        return jsonify(dat)
    else:
        return "Invalid start/end date!"

if __name__ == "__main__":
    app.run(debug=False)
