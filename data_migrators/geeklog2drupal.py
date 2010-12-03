#!/usr/bin/env python

# Migrate data from Geeklog 1.x to Drupal 6.x
# Written 2010/09/12 by Chris Guirl (thelusiv / gmail)
# Copyleft 2010 Chris Guirl

### COPYING ###

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

###############

import MySQLdb
import time


geeklog = None
drupal = None

# Geeklog database connection information
geeklog_db_config = \
{
  "username": "",
  "password": "",
  "hostname": "",
  "database": "",
}

# Drupal database connection information
drupal_db_config = \
{
  "username": "",
  "password": "",
  "hostname": "",
  "database": "",
}


# this list is for id numbers of Geeklog users which need to be imported.
gl_uids_to_convert = []

# This is a map from Geeklog user id numbers to drupal user id numbers and the
# associated name. You probably should pre-load this with your admin user that
# already exists, since you won't want to import the Geeklog admin user.
gl_uid_to_drup_uidname = {2: (1, "Admin")}

# this is just used internally, leave it alone
gl_tid_to_drup_tidvid = {}


# convert users
def users_to_users():
  global geeklog, drupal, gl_uid_to_drup_uidname
  geeklog_users = geeklog.cursor()
  where_clause = "WHERE uid = %d" % (gl_uids_to_convert[0])
  for i in range(1, len(gl_uids_to_convert)):
    where_clause += " OR uid = %d" % (gl_uids_to_convert[i])
  geeklog_user_select = "SELECT uid,username,passwd,fullname,email,homepage,sig,regdate FROM gl_users %s;" % (where_clause)
  geeklog_users.execute(geeklog_user_select)
  for geeklog_user in geeklog_users.fetchall():
    geeklog_uid,username,password,fullname,email,url,sig,regdate = geeklog_user
    created_time = time.mktime(regdate.timetuple())
    drupal_user_insert = """
      INSERT INTO users
      (name, pass, mail, signature, signature_format, created, access, status, timezone, init)
      VALUES('%s', '%s', '%s', '%s', %d, '%s', '%s', 1, -14400, 'migrated from geeklog');""" % \
      (username, password, email, sig, sig and 1 or 0, created_time, created_time)
    #print drupal_user_insert
    drupal_user = drupal.cursor()
    drupal_user.execute(drupal_user_insert)
    drupal_new_user_select = "SELECT uid FROM users WHERE mail = '%s';" % (email)
    #print drupal_new_user_select
    drupal_new_user = drupal.cursor()
    drupal_new_user.execute(drupal_new_user_select)
    drupal_new_user_uid = drupal_new_user.fetchone()[0]
    #print drupal_new_user_uid
    gl_uid_to_drup_uidname[geeklog_uid] = (drupal_new_user_uid, fullname)
    drupal_profile_stuff = drupal.cursor()
    drupal_profile_values = []
    if fullname:
      drupal_profile_values.append((1, gl_uid_to_drup_uidname[geeklog_uid][0], fullname))
    if url:
      drupal_profile_values.append((2, gl_uid_to_drup_uidname[geeklog_uid][0], url))
    if drupal_profile_values:
      drupal_profile_stuff.executemany( \
        "INSERT INTO profile_values (fid, uid, value) VALUES(%s, %s, %s);", drupal_profile_values)


# convert categories
def topics_to_taxonomy():
  global geeklog, drupal, gl_tid_to_drup_tidvid
  drupal_term_hierarchy_insert = "INSERT INTO term_hierarchy (parent) VALUES(0);"
  drupal_term_hierarchy = drupal.cursor()
  drupal_term_hierarchy.execute(drupal_term_hierarchy_insert)
  geeklog_topics_select = "SELECT tid, topic FROM gl_topics;"
  geeklog_topics = geeklog.cursor()
  geeklog_topics.execute(geeklog_topics_select)
  weight = 0
  tid = 1
  vid = 1
  for geeklog_topic in geeklog_topics.fetchall():
    geeklog_tid,topic_name = geeklog_topic
    drupal_term_data_insert = "INSERT INTO term_data (vid, name, description, weight) VALUES (1, '%s', '%s', %d)"\
      % (topic_name, topic_name, weight)
    drual_term_data = drupal.cursor()
    drual_term_data.execute(drupal_term_data_insert)
    gl_tid_to_drup_tidvid[geeklog_tid] = (tid, 1)
    drupal_term_hierarchy_insert = "INSERT INTO term_hierarchy (tid, parent) VALUES(%d, 0);" % (tid)
    drupal_term_hierarchy = drupal.cursor()
    drupal_term_hierarchy.execute(drupal_term_hierarchy_insert)
    weight += 1
    tid += 1


# convert stories
def stories_to_nodes():
  global geeklog, drupal, gl_uid_to_drup_uidname
  drupal_last_vid_select = "SELECT vid FROM node ORDER BY nid DESC LIMIT 1;"
  drupal_last_vid = drupal.cursor()
  drupal_last_vid.execute(drupal_last_vid_select)
  vid = drupal_last_vid.fetchone()[0] + 1
  geeklog_stories_select = "SELECT sid, uid, tid, date, title, introtext, bodytext, hits, comments FROM gl_stories;"
  geeklog_stories = geeklog.cursor()
  geeklog_stories.execute(geeklog_stories_select)
  for geeklog_story in geeklog_stories.fetchall():
    geeklog_sid,geeklog_uid,geeklog_tid,date,title,introtext,bodytext,hits,comments = geeklog_story
    created_time = time.mktime(date.timetuple())
    print title
    print introtext
    print bodytext
    drupal_node_insert = """
      INSERT INTO node (vid,type,title,uid,status,created,changed,comment)
      VALUES (%d, 'story', '%s', %d, 1, %d, %d, 1);""" % \
      (vid, title, gl_uid_to_drup_uidname[geeklog_uid][0], created_time, created_time)
    drupal_node = drupal.cursor()
    drupal_node.execute(drupal_node_insert)
    drupal_node_nid_select = "SELECT nid FROM node ORDER BY nid DESC LIMIT 1;"
    drupal_node_nid = drupal.cursor()
    drupal_node_nid.execute(drupal_node_nid_select)
    drupal_new_node_nid = drupal_node_nid.fetchone()[0]
    if not bodytext:
      bodytext = introtext
    drupal_node_revision_insert = """
      INSERT INTO node_revisions (nid,vid,uid,title,body,teaser,log,timestamp,format)
      VALUES (%s, %s, %s, %s, %s, %s, '', %s, 1);"""
    drupal_node_revision_values = \
      (drupal_new_node_nid, vid, gl_uid_to_drup_uidname[geeklog_uid][0], title, bodytext, introtext, created_time)
    drupal_node_revision = drupal.cursor()
    drupal_node_revision.execute(drupal_node_revision_insert, drupal_node_revision_values)
    drupal_term_node_insert = "INSERT INTO term_node (nid,tid,vid) VALUES(%s, %s, %s);"
    drupal_term_node_values = (drupal_new_node_nid, gl_tid_to_drup_tidvid[geeklog_tid][0], vid)
    drupal_term_node = drupal.cursor()
    drupal_term_node.execute(drupal_term_node_insert, drupal_term_node_values)
    if comments > 0:
      geeklog_comments_select = "SELECT date,title,comment,uid FROM gl_comments WHERE sid = '%s'" % (geeklog_sid)
      geeklog_comments = geeklog.cursor()
      geeklog_comments.execute(geeklog_comments_select)
      for geeklog_comment in geeklog_comments.fetchall():
        comment_date,comment_title,comment_text,comment_uid = geeklog_comment
        comment_time = time.mktime(comment_date.timetuple())
        drupal_comment_insert = """
          INSERT INTO comments (pid,nid,uid,subject,comment,timestamp,status,format,thread,name)
          VALUES(0, %s, %s, %s, %s, %s, 0, 1, '01/', %s);"""
        drupal_comment_values = (drupal_new_node_nid, gl_uid_to_drup_uidname[comment_uid][0], comment_title, comment_text, comment_time, gl_uid_to_drup_uidname[comment_uid][1])
        drupal_comment = drupal.cursor()
        drupal_comment.execute(drupal_comment_insert, drupal_comment_values)
    vid += 1


# convert pages
def staticpages_to_nodes():
  global geeklog, drupal, gl_uid_to_drup_uidname
  drupal_last_vid_select = "SELECT vid FROM node ORDER BY nid DESC LIMIT 1;"
  drupal_last_vid = drupal.cursor()
  drupal_last_vid.execute(drupal_last_vid_select)
  vid = drupal_last_vid.fetchone()[0] + 1
  geeklog_staticpages_select = "SELECT sp_uid,sp_title,sp_content,sp_hits,sp_date FROM gl_staticpage"
  geeklog_staticpages = geeklog.cursor()
  geeklog_staticpages.execute(geeklog_staticpages_select)
  for geeklog_staticpage in geeklog_staticpages.fetchall():
    geeklog_uid,title,content,hits,date = geeklog_staticpage
    created_time = time.mktime(date.timetuple())
    drupal_node_insert = """
      INSERT INTO node (vid,type,title,uid,status,created,changed,comment)
      VALUES (%d, 'page', '%s', %d, 1, %d, %d, 1);""" % \
      (vid, title, gl_uid_to_drup_uidname[geeklog_uid][0], created_time, created_time)
    drupal_node = drupal.cursor()
    drupal_node.execute(drupal_node_insert)
    drupal_node_nid_select = "SELECT nid FROM node ORDER BY nid DESC LIMIT 1;"
    drupal_node_nid = drupal.cursor()
    drupal_node_nid.execute(drupal_node_nid_select)
    drupal_new_node_nid = drupal_node_nid.fetchone()[0]
    drupal_node_revision_insert = """
      INSERT INTO node_revisions (nid,vid,uid,title,body,teaser,log,timestamp,format)
      VALUES (%s, %s, %s, %s, %s, %s, '', %s, 1);"""
    drupal_node_revision_values = \
      (drupal_new_node_nid, vid, gl_uid_to_drup_uidname[geeklog_uid][0], title, content, content, created_time)
    drupal_node_revision = drupal.cursor()
    drupal_node_revision.execute(drupal_node_revision_insert, drupal_node_revision_values)
    vid += 1
    


# convert links
def links_to_links():
  global geeklog, drupal
  pass



# convert galleries
def mediagallery_to_drupal():
  global geeklog, drupal
  pass



# connect a database
def connect_db(db_config):
  connection = MySQLdb.connect(host=db_config["hostname"], user=db_config["username"],
    passwd=db_config["password"], db=db_config["database"])
  return connection


# migrate
def convert(geeklog_db=None, drupal_db=None):
  global geeklog, drupal
  geeklog = connect_db(geeklog_db)
  drupal = connect_db(drupal_db)
  users_to_users()
  topics_to_taxonomy()
  stories_to_nodes()
  staticpages_to_nodes()
  links_to_links()
  mediagallery_to_drupal()


# main
convert(geeklog_db_config, drupal_db_config)


