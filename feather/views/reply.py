# coding: utf-8
import time
from flask import Module, request, session, g, redirect, url_for, \
		abort, render_template, flash
from feather import config
from feather.extensions import db
from feather.helpers import mentions, mentionfilter, textformat, markdown
from feather.databases import Bill, User, Topic, Reply, Notify

reply = Module(__name__)


@reply.route('/topic/<int:topic_id>/reply',methods=['POST'])
def add_reply(topic_id):
	if not session.get('user_id'):
		abort(401)
	if g.user.time < 5:
		g.error = u'抱歉，您的时间不足5分钟！'
		return redirect(url_for('topic.topic_view', topic_id=topic_id) + "#replyend")
	if request.form['reply[content]'] == '':
		g.error = u'抱歉，您的时间不足5分钟！'
		return redirect(url_for('topic.topic_view', topic_id=topic_id) + "#replyend")
	topic = Topic.query.get(topic_id)
	if topic.replys is not None:
		numbered = len(topic.replys.all())
	else:
		numbered = 0
	page_obj = topic.replys.paginate(1, per_page=config.RE_PER_PAGE)
	if page_obj.pages == 0:
		page = 1
	elif len(topic.replys.all()) % config.RE_PER_PAGE == 0:
		page = page_obj.pages + 1
	else:
		page = page_obj.pages
	if '@' in request.form['reply[content]']:
		reply_content = mentionfilter(request.form['reply[content]'])
	else:
		reply_content = request.form['reply[content]']
	reply_content = textformat(reply_content)
	reply_content = markdown(reply_content)
	reply = Reply(topic=topic, author=g.user, text=reply_content, text_origin=request.form['reply[content]'], number=numbered + 1)
	g.user.time -= 5
	topic.author.time += 5
	topic.last_reply_date = int(time.time())
	topic.reply_count += 1
	for reader in topic.readers:
		topic.readers.remove(reader)
	db.session.add(reply)
	db.session.commit()
	t = int(time.time())
	if session['user_id'] != topic.author.id:
		bill = Bill(author=g.user,time=5,type=3,date=t,reply=reply,user_id=topic.author.id,balance=g.user.time)
		bill2 = Bill(author=topic.author,time=5,type=5,date=t,reply=reply,user_id=g.user.id,balance=topic.author.time)
		db.session.add(bill)
		db.session.add(bill2)
		db.session.commit()
		notify = Notify(author=topic.author, topic=topic, reply=reply, type=1)
		db.session.add(notify)
		db.session.commit()
	if '@' in request.form['reply[content]']:
		content = request.form['reply[content]'].replace('\n','')
		usernames = list(set(mentions(content)))
		for username in usernames:
			author = User.query.filter_by(name=username).first()
			if author.id != topic.author.id and author.id != g.user.id:
				notify = Notify(author, topic, reply=reply, type=2)
				db.session.add(notify)
				db.session.commit()
	return redirect(url_for('topic.topic_view', topic_id=topic_id, page=page) + "#replyend")


@reply.route('/del/reply<int:reply_id>')
def del_reply(reply_id):
	reply = Reply.query.get(reply_id)
	reply.topic.reply_count -= 1
	db.session.delete(reply)
	db.session.commit()
	flash(u'成功删除一条评论！')
	return redirect(url_for('topic.topic_view', topic_id=reply.topic.id) + '#replys')



@reply.route('/reply/<int:reply_id>/edit<int:page>', methods=['GET', 'POST'])
def reply_edit(reply_id, page):
	reply = Reply.query.get(reply_id)
	if session.get('user_id') == reply.author.id or session.get('user_id') == 1:
		if request.method == 'POST':
			if not session.get('user_id'):
				abort(401)
			if '@' in request.form['reply[content]']:
				reply_content = mentionfilter(request.form['reply[content]'])
			else:
				reply_content = request.form['reply[content]']
			reply_content = textformat(reply_content)
			reply_content = markdown(reply_content)
			reply = Reply.query.get(reply_id)
			reply.text = reply_content
			reply.text_origin = request.form['reply[content]']
			db.session.commit()
			return redirect(url_for('topic.topic_view', topic_id=reply.topic.id, page=page) + '#replys')
		return render_template('reply_edit.html', reply=reply, topic=reply.topic, page=page)
	else:
		abort(401)


@reply.route('/reply/<int:reply_id>/thank')
def thank(reply_id):
	if not session.get('user_id'):
		abort(401)
	reply = Reply.query.get(reply_id)
	user = g.user
	if reply in user.thanks:
		return redirect(url_for('topic.topic_view', topic_id=reply.topic.id) + '#reply-' + str(reply_id))
	else:
		author = reply.author
		user.thanks += [reply]
		user.time -= 10
		author.time += 10
		db.session.commit()
		t = int(time.time())
		bill = Bill(author=g.user,time=10,type=4,date=t,reply=reply,user_id=reply.author.id,balance=g.user.time)
		bill2 = Bill(author=reply.author,time=10,type=6,date=t,reply=reply,user_id=g.user.id,balance=reply.author.time)
		db.session.add(bill)
		db.session.add(bill2)
		db.session.commit()
		return redirect(url_for('topic.topic_view', topic_id=reply.topic.id) + '#reply-' + str(reply_id))

