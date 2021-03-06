# coding: utf-8
import time
from flask import Module, request, session, g, redirect, url_for, \
		abort, render_template, flash, jsonify
from flask_sqlalchemy import Pagination
from feather import config
from feather.extensions import db, cache
from feather.helpers import mentions, mentionfilter
from feather.databases import Bill, Bank, User, Nodeclass, Node, \
		Topic, Reply, Notify


blog = Module(__name__)

@blog.route('/blog', defaults={'page': 1})
@blog.route('/blog/page/<int:page>')
def index(page):
	page_obj = Topic.query.filter_by(report=3).order_by(Topic.date.desc()).paginate(page, per_page=config.PER_PAGE)
	page_url = lambda page: url_for("blog.index", page=page)
	return render_template('blog.html', page_obj=page_obj, page_url=page_url)

@blog.route('/blog/add', methods=['GET', 'POST'])
def blog_add():
	node = Node.query.filter_by(name=u'爱情').first()
	if session.get('user_id') != 1:
		return redirect(url_for('topic.index'))
	if request.method == 'POST':
		topic = Topic(author=g.user, title=request.form['title'], text=request.form['text'], text_origin=request.form['text'], reply_count=0, node=node, report=3)
		db.session.add(topic)
		db.session.commit()
		return redirect(url_for('blog.blog_view', topic_id=topic.id))
	return render_template('blog_add.html', node=node)

@blog.route('/blog/<int:topic_id>')
def blog_view(topic_id):
	topic = Topic.query.get(topic_id)
	return render_template('blog_view.html', topic=topic)

@blog.route('/blog/edit/<int:topic_id>', methods=['GET', 'POST'])
def blog_edit(topic_id):
	if session['user_id'] != 1:
		return redirect(url_for('topic.index'))
	topic = Topic.query.get(topic_id)
	if request.method == 'POST':
		topic.title = request.form['title']
		topic.text = request.form['text']
		db.session.commit()
		return redirect(url_for('blog.blog_view', topic_id=topic_id))
	return render_template('blog_edit.html', topic=topic)


@blog.route('/blog/<int:topic_id>/reply', methods=['POST'])
def blog_reply(topic_id):
	topic = Topic.query.get(topic_id)
	reply = Reply(topic=topic, author=g.user, text=request.form['reply[content]'], text_origin=request.form['reply[content]'], type=2)
	db.session.add(reply)
	db.session.commit()
	return redirect(url_for('blog.blog_view', topic_id=topic_id))
