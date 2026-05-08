# -*- coding: utf-8 -*-
# by Leo小二
import json
import re
from base64 import b64decode, b64encode
from urllib.parse import quote, urljoin

try:
    from py_spider import Spider, Response
except Exception:
    from base.spider import Spider  # type: ignore
    Response = None


class Spider(Spider):
    def __init__(self):
        super().__init__()
        self.host = 'https://zh.xhamster.com'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
            'Referer': self.host + '/',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        }
        self.classes = [
            {'type_name': '热门免费色情影片', 'type_id': '/'},
            {'type_name': '高清', 'type_id': '/hd'},
            {'type_name': '4K', 'type_id': '/4k'},
            {'type_name': '虚拟现实', 'type_id': '/vr'},
            {'type_name': '最新视频', 'type_id': '/newest'},
            {'type_name': '最佳视频', 'type_id': '/best/weekly'},
            {'type_name': '短视频', 'type_id': '/moments'},
        ]

    def getName(self):
        return 'xHamster'

    def e64(self, text):
        if not text:
            return ''
        return b64encode(str(text).encode('utf-8')).decode('utf-8')

    def d64(self, text):
        if not text:
            return ''
        return b64decode(str(text)).decode('utf-8')

    def abs(self, url):
        if not url:
            return ''
        return urljoin(self.host, url)

    def clean(self, text):
        if not text:
            return ''
        text = re.sub(r'<[^>]+>', ' ', str(text))
        return re.sub(r'\s+', ' ', text).strip()

    def fmt_duration(self, sec):
        try:
            sec = int(sec or 0)
        except Exception:
            return ''
        if sec <= 0:
            return ''
        h = sec // 3600
        m = (sec % 3600) // 60
        s = sec % 60
        if h > 0:
            return f'{h:02d}:{m:02d}:{s:02d}'
        return f'{m:02d}:{s:02d}'

    def fmt_views(self, val):
        try:
            n = int(val or 0)
        except Exception:
            return ''
        if n >= 100000000:
            return f'{round(n / 100000000, 1)}亿观看'
        if n >= 10000:
            v = round(n / 10000, 1)
            return f'{int(v) if v == int(v) else v}万观看'
        return f'{n}观看' if n else ''

    def quality_from_item(self, item):
        if item.get('isVR'):
            return 'VR'
        if item.get('isUHD'):
            return '4K'
        if item.get('isFHD'):
            return '1080P'
        if item.get('isHD'):
            return 'HD'
        mr = str(item.get('maxResolution') or '')
        if '2160' in mr or '4k' in mr.lower() or 'uhd' in mr.lower():
            return '4K'
        if '1080' in mr:
            return '1080P'
        if '720' in mr:
            return 'HD'
        res = item.get('resolution') or []
        if isinstance(res, list) and len(res) >= 2:
            w, h = int(res[0] or 0), int(res[1] or 0)
            if w >= 3840 or h >= 2160:
                return '4K'
            if w >= 1920 or h >= 1080:
                return '1080P'
            if w >= 1280 or h >= 720:
                return 'HD'
        icon = str(item.get('icon') or '').lower()
        if 'uhd' in icon or '4k' in icon:
            return '4K'
        if 'fhd' in icon or '1080' in icon:
            return '1080P'
        if 'hd' in icon or '720' in icon:
            return 'HD'
        return ''

    def build_page_url(self, tid, pg):
        pg = int(pg or 1)
        tid = tid or '/'
        if pg <= 1:
            return self.abs(tid)
        if '/search/' in tid:
            return self.abs(f'{tid}?page={pg}')
        return self.abs(tid.rstrip('/') + f'/{pg}')

    def fetch(self, url):
        return self.fetch_url(url, headers=self.headers)

    def extract_thumb_props(self, html):
        key = '"videoThumbProps":'
        i = html.find(key)
        if i < 0:
            return []
        s = html[i + len(key):]
        depth = 0
        start = -1
        end = -1
        in_string = False
        esc = False
        for idx, ch in enumerate(s):
            if esc:
                esc = False
                continue
            if ch == '\\':
                esc = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == '[':
                if depth == 0:
                    start = idx
                depth += 1
            elif ch == ']':
                depth -= 1
                if depth == 0:
                    end = idx
                    break
        if start < 0 or end < 0:
            return []
        try:
            return json.loads(s[start:end + 1])
        except Exception:
            return []

    def get_list(self, html):
        items = self.extract_thumb_props(html)
        videos = []
        for item in items:
            q = self.quality_from_item(item)
            dur = self.fmt_duration(item.get('duration'))
            videos.append({
                'vod_id': self.abs(item.get('pageURL') or ''),
                'vod_name': self.clean(item.get('title') or ''),
                'vod_pic': self.abs(item.get('imageURL') or item.get('thumbURL') or ''),
                'vod_remarks': ' · '.join([x for x in [dur, q] if x]),
                'vod_content': self.fmt_views(item.get('views')) or self.clean((item.get('landing') or {}).get('name') or ''),
            })
        return [v for v in videos if v['vod_id'] and v['vod_name']]

    def homeContent(self, filter):
        html = self.fetch(self.host + '/').text
        return {'class': self.classes, 'list': self.get_list(html)[:24], 'filters': {}}

    def categoryContent(self, tid, pg, filter, extend):
        url = self.build_page_url(tid, pg)
        html = self.fetch(url).text
        lst = self.get_list(html)
        m1 = re.search(r'"currentPageNumber":(\d+)', html)
        m2 = re.search(r'"lastPageNumber":(\d+)', html)
        page = int(m1.group(1)) if m1 else int(pg or 1)
        pagecount = int(m2.group(1)) if m2 else page
        return {'list': lst, 'page': page, 'pagecount': pagecount, 'limit': 50, 'total': pagecount * 50}

    def detailContent(self, ids):
        url = ids[0]
        html = self.fetch(url).text
        title = ''
        m = re.search(r'<meta property="og:title" content="([^"]+)"', html)
        if m:
            title = self.clean(m.group(1))
        pic = ''
        m = re.search(r'<meta property="og:image" content="([^"]+)"', html)
        if m:
            pic = self.abs(m.group(1))
        quality = ''
        if '"isUHD":true' in html:
            quality = '4K'
        elif '"isFHD":true' in html:
            quality = '1080P'
        else:
            m = re.search(r'"resolution":\[(\d+),(\d+)\]', html)
            if m:
                w, h = int(m.group(1)), int(m.group(2))
                if w >= 3840 or h >= 2160:
                    quality = '4K'
                elif w >= 1920 or h >= 1080:
                    quality = '1080P'
                elif w >= 1280 or h >= 720:
                    quality = 'HD'
        dur = ''
        m = re.search(r'"duration":(\d+)', html)
        if m:
            dur = self.fmt_duration(m.group(1))

        play_id = self.e64(json.dumps({'video': url}, ensure_ascii=False))
        vod = {
            'vod_id': url,
            'vod_name': title,
            'vod_pic': pic,
            'vod_remarks': ' · '.join([x for x in [dur, quality] if x]),
            'vod_play_from': 'xHamster',
            'vod_play_url': f'自动${play_id}',
        }
        return {'list': [vod]}

    def searchContent(self, key, quick, pg='1'):
        url = self.build_page_url('/search/' + quote(key), pg)
        html = self.fetch(url).text
        lst = self.get_list(html)
        m1 = re.search(r'"currentPageNumber":(\d+)', html)
        m2 = re.search(r'"lastPageNumber":(\d+)', html)
        page = int(m1.group(1)) if m1 else int(pg or 1)
        pagecount = int(m2.group(1)) if m2 else page
        return {'list': lst, 'page': page, 'pagecount': pagecount, 'limit': 50, 'total': pagecount * 50}

    def extract_player_sources(self, html):
        key = '"sources":'
        i = html.find(key)
        if i < 0:
            return {}
        s = html[i + len(key):]
        depth = 0
        start = -1
        end = -1
        in_string = False
        esc = False
        for idx, ch in enumerate(s):
            if esc:
                esc = False
                continue
            if ch == '\\':
                esc = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == '{':
                if depth == 0:
                    start = idx
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = idx
                    break
        if start < 0 or end < 0:
            return {}
        try:
            return json.loads(s[start:end + 1])
        except Exception:
            return {}

    def pick_master(self, html):
        sources = self.extract_player_sources(html)
        hls = (sources.get('hls') or {}) if isinstance(sources, dict) else {}
        av1 = ((hls.get('av1') or {}).get('fallback') or (hls.get('av1') or {}).get('url') or '') if isinstance(hls, dict) else ''
        h264 = ((hls.get('h264') or {}).get('fallback') or (hls.get('h264') or {}).get('url') or '') if isinstance(hls, dict) else ''
        if h264:
            return {'primary': self.abs(h264), 'backup': self.abs(av1) if av1 else ''}
        if av1:
            av1 = self.abs(av1)
            h264_guess = av1.replace('.av1.mp4.m3u8', '.h264.mp4.m3u8') if '.av1.mp4.m3u8' in av1 else av1
            return {'primary': h264_guess, 'backup': av1}
        m = re.search(r'https://[^"\s<>]+\.m3u8[^"\s<>]*', html)
        if m:
            u = self.abs(m.group(0))
            h264_guess = u.replace('.av1.mp4.m3u8', '.h264.mp4.m3u8') if '.av1.mp4.m3u8' in u else u
            return {'primary': h264_guess, 'backup': u if h264_guess != u else ''}
        return {'primary': '', 'backup': ''}

    def playerContent(self, flag, id, vipFlags):
        try:
            data = json.loads(self.d64(id))
        except Exception:
            data = {'video': self.d64(id)}
        video_url = data.get('video', '')
        html = self.fetch(video_url).text
        masters = self.pick_master(html)
        master = masters.get('primary', '')
        backup = masters.get('backup', '')
        if master:
            return {'parse': 0, 'url': self.proxy(self.e64(json.dumps({'primary': master, 'backup': backup}, ensure_ascii=False)), 'm3u8'), 'header': self.headers}
        return {'parse': 1, 'url': video_url, 'header': self.headers}

    def localProxy(self, param):
        url = param.get('url', '')
        ptype = param.get('type', 'm3u8')
        if ptype in ('m3u8', 'master'):
            return self.m3u8Proxy(url)
        return self.tsProxy(url)

    def m3u8Proxy(self, url):
        try:
            data = json.loads(self.d64(url))
            real_url = data.get('primary', '')
            backup_url = data.get('backup', '')
        except Exception:
            data = None
            real_url = url
            backup_url = ''

        try:
            res = self.fetch(real_url)
            txt = res.text
            final_url = real_url
        except Exception:
            if not backup_url:
                raise
            res = self.fetch(backup_url)
            txt = res.text
            final_url = backup_url
        base = final_url.rsplit('/', 1)[0] + '/'
        out = []
        for line in txt.split('\n'):
            line = line.strip('\r')
            if not line:
                out.append(line)
                continue
            if line.startswith('#'):
                out.append(line)
                continue
            full = urljoin(base, line)
            ptype = 'm3u8' if '.m3u8' in line else 'ts'
            out.append(self.proxy(full, ptype))
        body = '\n'.join(out)
        if Response:
            return Response(content=body, media_type='application/vnd.apple.mpegurl')
        return body

    def tsProxy(self, url):
        res = self.fetch(url)
        content = getattr(res, 'content', None)
        if content is None:
            txt = getattr(res, 'text', '')
            content = txt.encode('utf-8') if isinstance(txt, str) else txt
        media = 'video/mp2t'
        if '.m4s' in url:
            media = 'video/iso.segment'
        if Response:
            return Response(content=content, media_type=media)
        return content

    def proxy(self, url, ptype='m3u8'):
        return self.getProxyUrl() + '&url=' + quote(url) + '&type=' + ptype


if __name__ == '__main__':
    Spider().run()
