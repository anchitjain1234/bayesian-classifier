from __future__ import division
from mode import Mode
from db import Db
from words import text_to_list
import operator
import pdb
class Classify(Mode):
	MIN_WORD_COUNT = 5
	RARE_WORD_PROB = 0.5
	EXCLUSIVE_WORD_PROB = 0.99

	def top_100_words(self,words,db):
		pl={}
		# db=Db()
		for word in words:
			spamicity=self.p_for_word(db,word)
			if(spamicity>0.45 and spamicity<0.55):
				continue
			# elif(self.wc_doctype_1(word,db)+self.wc_doctype_2(word,db)<100):
			# 	continue
			else:
				p1 = self.wc_doctype_1(word,db)/self.doctype1_word_count
				p2 = self.wc_doctype_2(word,db)/self.doctype2_word_count
				pl[word]=abs(p1-p2)
		if(len(pl)):
			sorted_pl=sorted(pl.items(), key=operator.itemgetter(1),reverse=True)
			# sorted_pl=sorted_pl.reverse()
			w=[]
			ct=0
			for k in sorted_pl:
				if(ct>=100):
					break
				w.append(k[0])
				ct+=1
			pdb.set_trace()
			return w
		else:
			return words

	def wc_doctype_1(self,word,db):
		return db.get_word_count(self.doctype1, word)

	def wc_doctype_2(self,word,db):
		return db.get_word_count(self.doctype2, word)

	def get_total_wc(self):
		return self.doctype1_word_count + self.doctype2_word_count

	def set_text(self, text):
		words = text_to_list(text)

		if not len(words):
			raise ValueError('Text did not contain any valid words')

		self.words = words
		return self

	def set_file_name(self, file_name):
		try:
			file_contents = open(file_name, 'r').read()
			return self.set_text(file_contents)

		except Exception as e:
			raise ValueError('Unable to read specified file "%s", the error message was: %s' % (file_name, e))

	def set_doctypes(self, doctype1, doctype2):
		if doctype1 == doctype2:
			raise ValueError('Please enter two different doctypes')

		d = Db().get_doctype_counts()
		if doctype1 not in d.keys():
			raise ValueError('Unknown doctype: ' + doctype1)

		if doctype2 not in d.keys():
			raise ValueError('Unknown doctype: ' + doctype2)

		self.doctype1 = doctype1
		self.doctype2 = doctype2

	def validate(self, args):
		if len(args) != 5:
			raise ValueError('Usage: %s classify <file> <doctype> <doctype>' % args[0])

		self.set_file_name(args[2])
		self.set_doctypes(args[3], args[4])

	def p_for_word(self, db, word):
		total_word_count = self.doctype1_word_count + self.doctype2_word_count

		word_count_doctype1 = db.get_word_count(self.doctype1, word)
		word_count_doctype2 = db.get_word_count(self.doctype2, word)
		
		if word_count_doctype1 + word_count_doctype2 < self.MIN_WORD_COUNT:
			return self.RARE_WORD_PROB

		if word_count_doctype1 == 0:
				return 1 - self.EXCLUSIVE_WORD_PROB
		elif word_count_doctype2 == 0:
				return self.EXCLUSIVE_WORD_PROB

		# P(S|W) = P(W|S) / ( P(W|S) + P(W|H) )

		p_ws = word_count_doctype1 / self.doctype1_word_count
		p_wh = word_count_doctype2 / self.doctype2_word_count

		return p_ws / (p_ws + p_wh)

	def p_from_list(self, l):
		p_product         = reduce(lambda x,y: x*y, l)
		p_inverse_product = reduce(lambda x,y: x*y, map(lambda x: 1-x, l))

		return p_product / (p_product + p_inverse_product)

	def execute(self):
		pl = []
		db = Db()

		d = db.get_doctype_counts()
		self.doctype1_count = d.get(self.doctype1)
		self.doctype2_count = d.get(self.doctype2)

		self.doctype1_word_count = db.get_words_count(self.doctype1)
		self.doctype2_word_count = db.get_words_count(self.doctype2)

		self.words=self.top_100_words(self.words,db)
		for word in self.words:
			p = self.p_for_word(db, word)
			pl.append(p)

		result = self.p_from_list(pl)

		return result

	def output(self, result):
		print 'Probability that document is %s rather than %s is %1.2f' % (self.doctype1, self.doctype2, result)
