from flask import Flask, session, flash
from server.psqlconnection import PSQLConnector
from server.instructors import Instructors

app = Flask(__name__)
postgresql = PSQLConnector(app, 'CertifyMe')
instructors = Instructors()

class Classes(object):
    def add(self, form_data):
        print "form data", form_data
        validate = True
        instructor_list = []
        for k, v in form_data.iteritems():
            #check every key to see if it begins with new instructor
            if k.startswith('new_instructor'):
                #if it does push value to a list
                instructor_list.append(v)
        if len(form_data['name']) < 6:
            flash("Name should be at lease 6 characters long", "name_error")
            validate = False
        if not form_data['duration'].isdigit():
            flash("Please enter a whole number", "duration_error")
            validate = False
        if len(form_data['date']) < 10:
            flash("Please enter correct date format", "date_error")
            validate = False
        if form_data['existing_instructor'] == "" and len(instructor_list) < 1:
            print "instructor validation fail"
            flash("Please choose existing instructor or add at least one new instructor", "instructor_error")
            validate = False
        #make this requirement longer in deployment, length requirement shortened for testing
        if len(form_data['email_text']) < 4:
            print "email validation fail"
            flash("Email must be at least 4 characters in length", "email_error")
            validate = False
        if len(form_data['race_verbiage']) < 4:
            print "race validation fail"
            flash("Race verbiage must be at least 4 characters in length", "race_error")
            validate = False
        if not validate:
            print "validation fail"
            return "error"
        else:
            print "validation pass"
            print instructor_list
            query = "INSERT INTO classes (name, duration, client_id, email_text, date, created_at, race_verbiage, cvpm_verbiage, status) VALUES (:name, :duration, :client_id, :email_text, :date, NOW(), :race_verbiage, :cvpm_verbiage, :status) RETURNING id"
            values = {
                "name": form_data['name'],
                "duration": form_data['duration'],
                "client_id": session['client_id'],
                "email_text": form_data['email_text'],
                "date": form_data['date'],
                "race_verbiage": form_data['race_verbiage'],
                "cvpm_verbiage": form_data['cvpm_verbiage'],
                "status": "incomplete"
            }
            # add class, return id
            class_id = postgresql.query_db(query, values)
            print class_id
            # add instructor names from list items to db as a group, return ids
            instructor_ids = instructors.add(instructor_list, class_id)
            if 'existing_instructor' in form_data:
                instructor_ids.append(form_data['existing_instructor'])
            print "instructor ids: ", instructor_ids
            # with returned ids, we then go and add entries to relational table
            instructors.add_class_instructors(class_id, instructor_ids)
            return class_id
    def update(self, form_data):
        # update class
        query = "UPDATE classes SET name=:name, duration=:duration, email_text=:email_text, date=:date, updated_at=NOW(), race_verbiage=:race_verbiage, cvpm_verbiage=cvpm_verbiage WHERE id=:id"
        values = {
            "name": form_data['name'],
            "duration": form_data['duration'],
            "email_text": form_data['email_text'],
            "date": form_data['date'],
            "race_verbiage": form_data['race_verbiage'],
            "cvpm_verbiage": form_data['cvpm_verbiage'],
            "id": form_data['id']
        }
        postgresql.query_db(query, values)
        # collect all instructors to be removed, pass to instructors remove function
        remove_instructors = {}
        # collect all instructors to be updated, pass to instructors update function
        update_instructor = {}
        # collect all instructors to be added, pass to add instructors function
        add_instructor = []
        for key in form_data:
            if key.startswith('remove'):
                id = key[6:]
                print id
                remove_instructors[id] = form_data[key]
                print remove_instructors
            elif key.startswith('instructor'):
                id = key[10:]
                print id
                update_instructor[id] = form_data[key]
                print update_instructor
            elif key.startswith('new_instructor'):
                add_instructor.append(form_data[key])
                print add_instructor
        # instructors.delete_class_relationship(remove_instructors)
    def findAll(self):
        query = "SELECT * FROM classes";
        classes = postgresql.query_db(query)
        return classes
    def findIncomplete(self):
        query = "SELECT * FROM classes WHERE status=:status"
        values = {
            "status": "incomplete"
        }
        incomplete_classes = postgresql.query_db(query, values)
        return incomplete_classes
    def findOne(self, class_id):
        query = "SELECT * FROM classes WHERE id=:class_id";
        values = {
            "class_id": class_id
        }
        one_class = postgresql.query_db(query, values)
        return one_class[0]
