from flask import Flask, abort
from flask import render_template
import db
# from flask_mysqldb import MySQL

app = Flask(__name__)
db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return str(db.query("SELECT * FROM Elections"))

def render_candidates(names, election_id, institution_id, region_id):
    candidates = db.query('''
        SELECT 
            Persons.name as 'Nume candidat',
            Parties.name as 'Partid',
            Candidates.position as 'Pozitie',
            Candidates.status
        FROM `Candidates`
        JOIN Persons ON Persons.id = Candidates.person_id
        JOIN Parties ON Parties.id = Candidates.party_id
        WHERE Candidates.election_id = %s And Candidates.institution_id = %s AND Candidates.region_id = %s
        ORDER BY Parties.name ASC, Candidates.position ASC
    ''', (election_id, institution_id, region_id))
    return render_template('candidates.html', names=names, candidates=candidates)

# Should answer to /<elections>/<institution>/<county>/<locality>
@app.route('/<election_slug>/<institution_slug>/<county_slug>/<locality_slug>')
@app.route('/<election_slug>/<institution_slug>/<county_slug>/<locality_slug>/')
def local_candidates(election_slug=None, institution_slug=None, county_slug=None, locality_slug=None):
    names = db.query('''
        SELECT
            Elections.id as 'election_id',
            Institutions.id as 'institution_id',
            Reg.id as 'region_id',
            Elections.name as 'Alegeri',
            Institutions.name as 'Institutie',
            `Judet`,
            `Localitate`
        FROM Elections
        JOIN Institutions ON Institutions.slug = %s AND Institutions.region_type = 'uat'
        JOIN (SELECT P.name as 'Judet', C.name as 'Localitate', C.id as id FROM Regions as C
             JOIN Regions as P ON P.id = C.parent_id AND P.slug = %s WHERE C.slug = %s) as Reg
        WHERE Elections.slug = %s
    ''', (institution_slug, county_slug, locality_slug, election_slug))
    if len(names) != 1:
        abort(404)
    names = names[0]
    return render_candidates(names[3:], names[0], names[1], names[2])

@app.route('/<election_slug>/<institution_slug>/<county_slug>/')
def county_candidates(election_slug=None, institution_slug=None, county_slug=None):
    names = db.query('''
        SELECT
            Elections.id as 'election_id',
            Institutions.id as 'institution_id',
            Regions.id as 'region_id',
            Elections.name as 'Alegeri',
            Institutions.name as 'Institutie',
            Regions.name as 'name',
            Institutions.region_type
        FROM Elections
        JOIN Regions ON Regions.slug = %s AND Regions.parent_id = 1
        JOIN Institutions ON Institutions.slug = %s
        WHERE Elections.slug = %s
    ''', (county_slug, institution_slug, election_slug))

    if len(names) != 1:
        abort(404)

    names = names[0]

    if names[-1] == 'judet':
        return render_candidates(names[3:-1], names[0], names[1], names[2])
    elif names[-1] == 'uat':
        localities = db.query('''
            SELECT slug, name FROM Regions
            WHERE parent_id = %s
        ''', (names[2], ))

        links = map(lambda x: ('/{}/{}/{}/{}'.format(election_slug, institution_slug, county_slug, x[0]), x[1]), localities)

        return render_template('list.html', 
            title=names[3], 
            subtitle='Candidaţi la {}'.format(names[4]), 
            list_name='Localităţi din judeţul {}'.format(names[5]),
            links=links)
    else:
        abort(404)


@app.route('/<election_slug>/<institution_slug>/')
def candidates(election_slug=None, institution_slug=None):
    names = db.query('''
        SELECT
            Elections.id as 'election_id',
            Institutions.id as 'institution_id',
            Elections.name as 'Alegeri',
            Institutions.name as 'Institutie'
        FROM Elections
        JOIN Institutions ON Institutions.slug = %s
        WHERE Elections.slug = %s
    ''', (institution_slug, election_slug))

    if len(names) != 1:
        abort(404)

    names = names[0]
    localities = db.query('''
        SELECT slug, name FROM Regions
        WHERE region_type = 'judet' 
        ORDER BY name ASC
    ''')

    links = map(lambda x: ('/{}/{}/{}/'.format(election_slug, institution_slug, x[0]), x[1]), localities)

    return render_template('list.html', 
        title=names[2], 
        subtitle='Candidaţi la {}'.format(names[3]), 
        list_name='Judeţe',
        links=links)

@app.route('/<election_slug>/')
def election(election_slug=None):
    names = db.query('''
        SELECT
            Elections.id as 'election_id',
            Elections.name as 'Alegeri'
        FROM Elections WHERE Elections.slug = %s
    ''', (election_slug, ))

    if len(names) != 1:
        abort(404)

    names = names[0]
    localities = db.query('''
        SELECT DISTINCT Institutions.slug, Institutions.name FROM Institutions
        JOIN Candidates ON Candidates.institution_id = Institutions.id 
                            AND Candidates.election_id = %s
    ''', (names[0], ))

    links = map(lambda x: ('/{}/{}/'.format(election_slug, x[0]), x[1]), localities)

    return render_template('list.html', 
        title='Candidaţi la {}'.format(names[1]), 
        subtitle='', 
        list_name='',
        links=links)


if __name__ == '__main__':
    app.run(debug=True)
