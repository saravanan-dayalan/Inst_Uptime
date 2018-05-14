from flask import request
from flask import Flask
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker, Query
from flask import Flask,redirect,url_for  
import json
import time
from collections import defaultdict
import datetime

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:MINCSY417@localhost:3306/projectdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
db.Model.metadata.reflect(db.engine)
class Info(db.Model):
    
    __table__ = db.Model.metadata.tables['spl_info']

class Detail(db.Model):
    __table__ = db.Model.metadata.tables['spl_dtl']

@app.route('/data',methods=['POST', 'GET'])
def data():
    instrumentsName = db.session.query(Info.instrument).distinct().all()   
    
    instruments = []
    for i in instrumentsName:
        instruments.append(i[0])
    if request.method == 'POST':
        if request.form['form'] == 'data':
            sttime1 = request.form['starttime1']
            ettime1 = request.form['endtime1']
            sttime2 = request.form['starttime2']
            ettime2 = request.form['endtime2']
            if sttime1 == '' or ettime1 == '':
                sttime = '1000-00-00'
                ettime = '3000-00-00'
            else:
                sttime = sttime1 + ' ' + sttime2
                ettime = ettime1 + ' ' + ettime2
            inst = request.form['instrument']          
            info_instrument = db.session.query(Info).filter_by(instrument=inst).filter(Info.actualstarttime > sttime,Info.actualendtime<ettime).all()
        elif request.form['form'] == 'all':
            info_instrument = db.session.query(Info).all()
        
        samples = {}
        samples1 = {}
        for i in info_instrument:
            sample = db.session.query(Detail).filter_by(name = i.name).all()
            samples[i.name] = sample
            nameTar={}       
            for j in sample:                
                data=j.data
                data1=str(data['RTs'])
                data1 = data1[1:len(data1)-1]
                data2=str(data['ints'])
                data2 = data2[1:len(data2)-1]
                data = data1+',,'+data2        
                key=str(j.EIC)
                nameTar[key]=data
            samples1[str(i.name)] = nameTar
        print(samples1)
        samples1 = json.dumps(samples1)
        
        return render_template("data.html",instruments=instruments,info_instrument = info_instrument,samples = samples, samples1 = samples1)       
                
    return render_template("data.html",instruments=instruments)


@app.route('/', methods=['POST', 'GET'])
def summary():
    # get the count of instruments [instrument1, 2, 3..]
    info_instruments = db.session.query(Info.instrument).distinct().all()
    instruments = []
    for i in info_instruments:
        instruments.append(i[0])
    sorted(instruments)
    smry_instruments = defaultdict(dict)
    if request.method == 'POST':
        if request.form['form'] == 'summary':
            sttime = request.form['starttime']
            ettime = request.form['endtime']             
            inst = request.form.getlist('instrument')
            if len(inst) == 0:
                return render_template("summary.html",instruments = instruments,smry_instruments = smry_instruments)
            
            else:
                for j in inst:                
                    if sttime != '' and ettime != '':
                        info_instrument = db.session.query(Info).filter_by(instrument=j).filter(Info.actualstarttime > sttime,Info.actualendtime<ettime).all()
                        st = datetime.datetime.strptime(sttime, "%Y-%m-%d").date()
                        et = datetime.datetime.strptime(ettime, "%Y-%m-%d").date()
                        st = int(time.mktime(st.timetuple()) * 1000)
                        et = int(time.mktime(et.timetuple()) * 1000)
                        total = et-st
                    else:
                        info_instrument = db.session.query(Info).filter_by(instrument=j).all()
                        ct = datetime.now()
                        ct = int(time.mktime(ct.timetuple()) * 1000 + ct.microsecond / 1000)

                        ft = db.session.query(Info).first().actualstarttime
                        ft = int(time.mktime(ft.timetuple()) * 1000 + ft.microsecond / 1000)

                        total = ct - ft                       
                            
                    count_sample = len(info_instrument)

                    data = []
                    total_length = 0
                    for i in info_instrument:
                        st = i.actualstarttime
                        et = i.actualendtime
                        length = i.length
                        total_length += length
                        st = int(time.mktime(st.timetuple()) * 1000 + st.microsecond / 1000)
                        et = int(time.mktime(et.timetuple()) * 1000 + et.microsecond / 1000)

                        data.append([st, 1])
                        data.append([et, 0])
                    
                    ratio = round(total_length * 1000 / total * 100, 2)
                    rest_ratio = 100 - ratio
                    smry_instruments[j]['count'] = count_sample
                    smry_instruments[j]['hours'] = round(total/3600000,2)
                    smry_instruments[j]['ratio'] = ratio
                    smry_instruments[j]['rest_ratio'] = rest_ratio
                    smry_instruments[j]['data'] = data
                    # smry_insruments = json.dumps(smry_instruments)
 
            return render_template("summary.html", smry_instruments = smry_instruments, instruments = instruments,inst=inst)
    return render_template("summary.html",instruments = instruments,smry_instruments = smry_instruments)



if __name__ == '__main__':
    app.debug = True
    app.run()
   
