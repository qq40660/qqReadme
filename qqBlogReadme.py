# -*- coding: UTF-8 -*-
from __future__ import with_statement
import codecs
from datetime import datetime
from datetime import timedelta
from os import linesep
import cPickle
#import ClientCookie
from urllib2 import urlopen, URLError

mainUrl = 'http://%s.qzone.qq.com/'
listUrl = 'http://b.qzone.qq.com/cgi-bin/blognew/blog_output_toppage?uin=%(qq)s&vuin=0&property=GoRE&getall=1&imgdm=imgcache.qq.com&bdm=b.qzone.qq.com&cate=&numperpage=100&sorttype=0&arch=0&pos=%(pos)d&direct=1'
blogUrl = 'http://qzone.qq.com/blog/%(qq)s-%(blogid)s'
GMT_FORMAT = '%a, %d %b %Y %H:%M:%S +0800'
HEADER = u'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
  xmlns:excerpt="http://wordpress.org/export/1.0/excerpt/"
  xmlns:content="http://purl.org/rss/1.0/modules/content/"
  xmlns:wfw="http://wellformedweb.org/CommentAPI/"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:wp="http://wordpress.org/export/1.0/"
>

<channel>
  <title>%(author)s的QQ空间</title>
  <description>%(description)s</description>
  <pubDate>%(time)s</pubDate>
  <generator>keakon的QQ空间导出程序</generator>
  <language>zh-CN</language>
  <wp:wxr_version>1.0</wp:wxr_version>
'''.replace('\n', linesep)
FOOTER = '''</channel>
</rss>'''.replace('\n', linesep)

#cj = ClientCookie.MSIECookieJar(delayload=True)
#cj.load_from_registry()
#opener = ClientCookie.build_opener(ClientCookie.HTTPCookieProcessor(cj))
#ClientCookie.install_opener(opener)

def getBasicInfo(qq):
  AUTHOR = '<meta name="author" content="'
  AUTHOR_LEN = len(AUTHOR)
  DESC = '<meta name="Description" content="'
  DESC_LEN = len(DESC)

  #res = ClientCookie.urlopen(mainUrl % qq)
  res = urlopen(mainUrl % qq)
  html = res.read()

  begin = html.find(AUTHOR)
  if begin == -1:
    raise URLError, 'HTML not complete.'
  begin += AUTHOR_LEN
  end = html.find('"', begin)
  author = unicode(html[begin:end], 'utf8', 'replace')

  begin = html.find(DESC)
  if begin == -1:
    raise URLError, 'HTML not complete.'
  begin += DESC_LEN
  end = html.find('"', begin)
  description = unicode(html[begin:end], 'utf8', 'replace')

  return author, description


def getBlogList(qq):
  global listUrl

  CATEGORY = "selectCategory('"
  CAT_LEN =  len(CATEGORY)
  BLOG = 'selectBlog('
  BLOG_LEN = len(BLOG)

  pos = 0
  round = 0
  blogs = []

  while pos == len(blogs):
    #res = ClientCookie.urlopen(listUrl % {'qq': qq, 'pos': pos})
    res = urlopen(listUrl % {'qq': qq, 'pos': pos})
    html = res.read()
    res.close()

    begin = 0

    while True:
      begin = html.find(CATEGORY, begin)
      if begin == -1:
        break
      else:
        begin += CAT_LEN
        end = html.find("')", begin)
        blog = {}
        blog['category'] = unicode(html[begin:end], 'gb18030', 'replace')

        begin = html.find(BLOG, end)
        if begin == -1:
          raise URLError, 'HTML not complete.'
        else:
          begin += BLOG_LEN
          end = html.find(')', begin)
          blog['id'] = html[begin:end]
          blogs.append(blog)
          begin = end

    pos += 100
    print '已找到%d篇' % len(blogs)

  return blogs


def getBlogContent(qq, author, blogs, outFile):
  global blogUrl

  TITLE = u'<h4 class="c_tx">'
  TIT_LEN = len(TITLE)
  TITLE_END = u'</h4>'
  TIME = u'发表时间：'
  TIME_LEN = len(TIME)
  DETAIL = u'<div id="blogDetailDiv"'
  DETAIL_END = u'<img id="paperPicArea1"'
  DETAIL_END_DIV = u'</div>'
  TIME_FORMAT = '%Y年%m月%d日 %H:%M'
  DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

  ITEM = '''
  <item>
    <title>%(title)s</title>
    <pubDate>%(pubDate)s</pubDate>
    <dc:creator><![CDATA[%(author)s]]></dc:creator>
    <content:encoded><![CDATA[%(content)s]]></content:encoded>
    <wp:post_date>%(time)s</wp:post_date>
    <wp:post_date_gmt>%(gmtTime)s</wp:post_date_gmt>
    <wp:comment_status>open</wp:comment_status>
    <wp:ping_status>open</wp:ping_status>
    <wp:post_name>%(title)s</wp:post_name>
    <wp:status>publish</wp:status>
    <wp:post_parent>0</wp:post_parent>
    <wp:menu_order>0</wp:menu_order>
    <wp:post_type>post</wp:post_type>
    <wp:post_password></wp:post_password>
  </item>
'''.replace('\n', linesep)

  for index, blog in enumerate(blogs):
    url = blogUrl % {'qq': qq, 'blogid': blog['id']}
    print '正在下载第%(index)d篇日志: %(url)s' % {'index': index + 1, 'url': url}

    #res = ClientCookie.urlopen(url)
    res = urlopen(url)
    html = res.read()
    res.close()

    content = unicode(html, 'gbk', 'replace')

    begin = content.find(TITLE)
    if begin == -1:
      print 'HTML not complete. ID: ' + blog['id']
      continue
    begin += TIT_LEN
    end = content.find(TITLE_END, begin)
    blog['title'] = content[begin:end]

    begin = content.find(TIME, end)
    if begin == -1:
      print 'HTML not complete. ID: ' + blog['id']
      continue
    begin += TIME_LEN
    end = content.find('\r\n', begin)
    blog['time'] = datetime.strptime(content[begin:end].encode('gbk'), TIME_FORMAT)

    begin = content.find(DETAIL, end)
    if begin == -1:
      print 'HTML not complete. ID: ' + blog['id']
      continue
    begin = content.find('>', begin) + 1
    if begin == 0:
      print 'HTML not complete. ID: ' + blog['id']
      continue
    end = content.find(DETAIL_END, begin)
    if end == -1:
      print 'HTML not complete. ID: ' + blog['id']
      continue
    # 去掉最后2个div关闭标签
    end2 = content.rfind(DETAIL_END_DIV, begin, end)
    if end2 != -1:
      end3 = content.rfind(DETAIL_END_DIV, begin, end2)
      end = end3 != -1 and end3 or end2
    blog['content'] = content[begin:end].strip()

    outFile.write(ITEM % {'title': blog['title'], 'author': author, 'content': blog['content'],
                  'time': blog['time'].strftime(DATE_FORMAT),
                  'gmtTime': (blog['time'] -timedelta(hours=8)).strftime(DATE_FORMAT),
                  'pubDate': blog['time'].strftime(GMT_FORMAT)})


def main(qq, filename='qzone.xml', filename2='blogs.txt'):
  author, description = getBasicInfo(qq)

  blogs = getBlogList(qq)

  if not blogs:
    print '没有找到日志。若您设置了QQ空间权限，请用IE登录QQ空间，并启用cookie。'
    exit(1)

  categories = set([blog['category'] for blog in blogs])

  with codecs.open(filename, 'w', 'utf8') as outFile:
    # write header
    outFile.write(HEADER % {'author': author, 'description': description, 'time': datetime.now().strftime(GMT_FORMAT)})
    for category in set([blog['category'] for blog in blogs]):
      outFile.write(u'  <wp:category><wp:category_nicename>%(category)s</wp:category_nicename><wp:category_parent></wp:category_parent><wp:cat_name><![CDATA[%(category)s]]></wp:cat_name></wp:category>%(linesep)s' % {'category': category, 'linesep': linesep})

    # write item
    getBlogContent(qq, author, blogs, outFile)

    # write footer
    outFile.write(FOOTER)

  with open(filename2, 'w') as outFile2:
    cPickle.dump(blogs, outFile2)

  print '全部导出完毕'

if __name__ == "__main__":
  main('2457533728') # 这里填你的QQ号
